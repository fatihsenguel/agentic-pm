# src/agents/nodes.py
# Purpose: LangGraph node functions for each agent
# Principle: Nodes are thin wrappers that call agent logic and update state
# Phase: 6.2 - LangGraph State Machine
# 
# PRODUCTION STANDARDS:
# - NO fallback data (fail fast with clear errors)
# - NO guessing or defaults for financial data
# - NO silent failures
# - Clear error messages with actionable solutions

from config import config
import logging
logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional, Literal, List, Tuple
from langchain_core.messages import AIMessage, HumanMessage

from .protocols import PortfolioContext
from .schemas import INTENTS

from .state import (
    AgentState,
    set_router_decision,
    mark_agent_complete,
    add_shared_data,
    add_error,
    set_final_response,
    get_next_agent,
    get_user_message,
    get_agent_result,
    get_shared_data,
    is_execution_complete,
    has_errors,
)


# Import observability
try:
    from observability import get_tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    def get_tracer():
        return None


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class PortfolioContextError(Exception):
    """Raised when portfolio context is invalid or missing"""
    pass


class DataCalculationError(Exception):
    """Raised when financial data calculation fails"""
    pass


# =============================================================================
# HELPER FUNCTIONS - STRICT MODE (NO FALLBACKS)
# =============================================================================

def load_portfolio_context(state: "AgentState") -> PortfolioContext:
    """Load portfolio tickers, holdings and cash from state or database."""
    
    portfolio_id = state.get("portfolio_id")
    
    if not portfolio_id:
        # Get tickers from router decision
        router_decision = state.get("router_decision") or {} 
        parameters = router_decision.get("parameters", {})
        tickers = parameters.get("tickers", [])
        
        if not tickers:
            raise PortfolioContextError(
                "No portfolio specified and no tickers found in query.\n"
                "Please either:\n"
                "  1. Specify a portfolio: create_initial_state(..., portfolio_id=X)\n"
                "  2. Include tickers in query: 'Analyze SPY and TLT'\n"
                "\n"
                "Cannot proceed without knowing which assets to analyze."
            )
        
        logger.debug(f"No portfolio specified, using tickers from query: {tickers}")
        return PortfolioContext(tickers=tickers)
    
    # Portfolio specified - load from database
    from portfolio_tool.portfolio_manager import PortfolioManager
    pm = PortfolioManager()
    
    # Cash lives on the portfolio row, not on the holdings, so it is read even
    # when holdings come from cache. expected_values.md D2 puts cash in the
    # allocation denominator, so a missing balance is a wrong answer.
    portfolio = pm.get_portfolio(portfolio_id)
    if portfolio is None:
        raise PortfolioContextError(
            f"Portfolio {portfolio_id} not found.\n"
            "Check portfolio_id is correct."
        )
    cash_balance = float(portfolio["cash_balance"])
    # The portfolio's own currency (expected_values.md D15): every figure
    # about it is reported in this, and a foreign holding is valued into it.
    base_currency = portfolio["currency"]

    # Check cache first
    cached_holdings = state.get("portfolio_holdings")
    if cached_holdings:
        tickers = [h["ticker"] for h in cached_holdings]
        return PortfolioContext(
            tickers=tickers,
            holdings=cached_holdings,
            cash_balance=cash_balance,
            base_currency=base_currency,
            portfolio_id=portfolio_id,
        )
    
    # ✅ DISTINGUISH: User errors vs System errors
    try:
        holdings = pm.get_holdings(portfolio_id)
    except ValueError as e:
        # User error: Portfolio doesn't exist
        raise PortfolioContextError(
            f"Portfolio {portfolio_id} not found: {e}\n"
            "Check portfolio_id is correct."
        ) from e
    except Exception as e:
        # System error: Database/infrastructure issue
        # Let it bubble up - ops team needs to see this
        logger.critical(f"Infrastructure error loading portfolio {portfolio_id}: {e}")
        raise  # Don't mask as PortfolioContextError
    
    if not holdings:
        raise PortfolioContextError(
            f"Portfolio {portfolio_id} is empty.\n"
            "Add holdings before analysis."
        )
    
    tickers = [h["ticker"] for h in holdings]
    return PortfolioContext(
        tickers=tickers,
        holdings=holdings,
        cash_balance=cash_balance,
        base_currency=base_currency,
        portfolio_id=portfolio_id,
    )


def get_current_positions(holdings: Optional[List[Dict]]) -> Dict[str, float]:
    """
    Convert holdings list to position dictionary.
    
    Args:
        holdings: List of holding dicts from portfolio
        
    Returns:
        Dictionary of {ticker: quantity}
    """
    if not holdings:
        return {}
    
    return {
        h["ticker"]: float(h["quantity"]) 
        for h in holdings
    }


def get_cost_basis(holdings: Optional[List[Dict]]) -> Dict[str, float]:
    """
    Extract cost basis from holdings.
    
    Args:
        holdings: List of holding dicts from portfolio
        
    Returns:
        Dictionary of {ticker: average_price}
    """
    if not holdings:
        return {}
    
    return {
        h["ticker"]: float(h["average_price"]) 
        for h in holdings
    }

def build_holdings_summary(holdings: Optional[List[Dict]]) -> List[Dict[str, Any]]:
    """
    Reduce holdings rows to the summary published on `shared_data`.

    Hot potato: `shared_data` carries summaries, not database rows. The raw rows
    stay in `portfolio_holdings`; this is what downstream agents read.

    Deliberately unpriced. Market value needs `latest_prices` and cash, and
    combining them is an allocation computation that belongs to the agent doing
    the computing, not to the agent fetching the data.

    `sector` stays None where the asset has none. Per expected_values.md D3,
    unsectored holdings are reported explicitly rather than bucketed.

    `instrument_type` ('share' or 'fund') stays None where the asset has
    none, and is published as None rather than dropped: the compliance
    checker raises on a holding whose type it does not know (IPS-4.2 counts
    directly held shares only), and it can only do that if the absence
    reaches it. `currency`, the price's, the same way: the rate lookup
    (quant/fx.py) raises on a holding whose currency it does not know (D16).

    Args:
        holdings: Rows from PortfolioManager.get_holdings, or None

    Returns:
        JSON-serialisable list of summary dicts, empty if there are no holdings.
    """
    if not holdings:
        return []

    return [
        {
            "ticker": h["ticker"],
            "quantity": float(h["quantity"]),
            "average_price": float(h["average_price"]),
            "asset_class": h.get("asset_class"),
            "sector": h.get("sector"),
            "instrument_type": h.get("instrument_type"),
            "purchase_date": (
                h["purchase_date"].isoformat() if h.get("purchase_date") else None
            ),
            "currency": h.get("currency"),
        }
        for h in holdings
    ]


def cache_portfolio_holdings(state: "AgentState", holdings: List[Dict]) -> Dict[str, Any]:
    """
    Build a state update carrying portfolio holdings to downstream agents.

    LangGraph merges what a node RETURNS; mutating `state` in place does not
    propagate. The caller must spread this dict into its return value.

    Args:
        state: Current agent state
        holdings: Holdings loaded from portfolio manager

    Returns:
        State update dict, empty if there are no holdings.
    """
    if not holdings:
        return {}
    logger.debug(f"Caching {len(holdings)} holdings in state")
    return {"portfolio_holdings": holdings}


def validate_portfolio_context(state: "AgentState") -> bool:
    """
    Check if portfolio context is properly loaded.
    
    Returns True if either:
    - No portfolio specified (ad-hoc query)
    - Portfolio specified AND holdings loaded
    
    Returns False if:
    - Portfolio specified but holdings missing (error state)
    
    Args:
        state: Current agent state
        
    Returns:
        True if context is valid, False otherwise
    """
    portfolio_id = state.get("portfolio_id")
    
    if not portfolio_id:
        # No portfolio - valid (ad-hoc query)
        return True
    
    holdings = state.get("portfolio_holdings")
    
    if holdings:
        # Portfolio + holdings - valid
        return True
    
    # Portfolio specified but no holdings - invalid
    logger.error(f"Portfolio {portfolio_id} specified but holdings not loaded")
    return False


# =============================================================================
# ROUTER NODE
# =============================================================================

async def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Router node - determines which agents to call and in what order.
    
    Uses the Smart Router (Phase 6.1) for LLM-based intent detection.
    """
    from .smart_router import get_router
    
    tracer = get_tracer()
    agent_ctx = None
    
    try:
        # The request span is owned by run_agent_graph, so it outlives this
        # node and the agents after it trace into the same request. Opening
        # it here closed it here, and every later node found no request:
        # no agent spans, no tool calls, no handovers in any live trace.
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("Router")
                agent_ctx.__enter__()
        
        # Get user message
        user_message = get_user_message(state)
        
        if not user_message:
            return add_error(state, "No user message found")
        
        # Call Smart Router
        router = get_router()
        portfolio_id = state.get("portfolio_id")
        decision, validation = await router.route(
            user_message, portfolio_id=portfolio_id, pending=state.get("pending"))

        # Every attempt the router rejected before this decision, carried in
        # the state so a repaired route is visible to the CLI and the golden
        # runner. This loop used to call add_warning and drop what it
        # returned, so no retry ever reached state["warnings"].
        warnings = list(state.get("warnings", []))
        warnings.extend(f"Validation: {error}" for error in validation.errors)

        # Check if clarification needed
        if decision.intent == "clarification_needed":
            return {
                **set_final_response(state, decision.clarification_question or "Could you please clarify your request?"),
                "router_decision": _decision_to_dict(decision),
                "warnings": warnings,
            }

        # Set router decision and initialize execution
        return {
            **set_router_decision(state, _decision_to_dict(decision)),
            "warnings": warnings,
        }
        
    except Exception as e:
        return add_error(state, f"Router error: {str(e)}")
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


def _decision_to_dict(decision) -> Dict[str, Any]:
    """Convert RouterDecision to dict for state storage."""
    return {
        "intent": decision.intent if isinstance(decision.intent, str) else decision.intent.value,
        "confidence": decision.confidence,
        # Every extracted field, from the schema. A hand-picked key list here
        # was a second statement of ExtractedParameters and dropped any field
        # it did not name - a router output that validated and then vanished
        # before any node could read it.
        "parameters": decision.parameters.model_dump(),
        "execution_order": decision.execution_order,
        # What was asked back, as text for the CLI and as the record the next
        # turn resolves the reply against. Both used to be dropped here, so
        # the CLI's "asked back" line never printed (KNOWN_GAPS).
        "clarification_question": decision.clarification_question,
        "pending": getattr(decision, "pending", None),
        "resolved": getattr(decision, "resolved", None),
        # The model's sentence, or extraction's "could not resolve", or the
        # fallback's "Router failed". The CLI prints it; it was dropped here
        # since the dict was first written (KNOWN_GAPS).
        "reasoning": getattr(decision, "reasoning", None),
    }


# =============================================================================
# DATA AGENT NODE - STRICT MODE
# =============================================================================

async def data_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Data Agent node - fetches prices, calculates returns and covariance.
    
    STRICT MODE: Fails if data cannot be calculated properly.
    """
    tracer = get_tracer()
    agent_ctx = None
    
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("DataAgent")
                agent_ctx.__enter__()
    except Exception as e:
        # Just log the error and continue. Do not crash the trade.
        logger.warning(f"Tracing failed in DataAgent (ignoring): {e}")
    
    # Business Logic Starts Here
    try:
        print("\n" + "="*80)
        print("DATA AGENT - Fetching market data")
        print("="*80)
        
        # ⭐ STRICT: Load portfolio context (fails if invalid)
        try:
            ctx = load_portfolio_context(state)
            tickers, holdings = ctx.tickers, ctx.holdings
        except PortfolioContextError as e:
            logger.error(f"Portfolio context error: {e}")
            return {
                **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
                **add_error(state, f"DataAgent: {str(e)}"),
            }
        
        # Cache holdings if loaded (spread into the return below)
        holdings_update = cache_portfolio_holdings(state, holdings)
        
        # The period is extraction's: a vocabulary key or None, always
        # present on the decision. None falls through to config's default in
        # the data agent; no second default lives here.
        router_decision = state.get("router_decision") or {}
        parameters = router_decision.get("parameters", {})
        period = parameters.get("period")
        
        print(f"  Tickers: {tickers}")
        print(f"  Period: {period}")
        print(f"  Portfolio ID: {state.get('portfolio_id')}")
        
        # Try to use actual DataAgent
        try:
            from .data_agent import create_data_agent
            agent = create_data_agent(verbose=False)
            
            tickers_str = ",".join(tickers)
            
            # Fetch prices
            print(f"  Fetching prices...")
            price_result = agent.fetch_prices_tool(
                tickers=tickers_str,
                period=period
            )
            
            if not price_result.get("success"):
                raise DataCalculationError(
                    f"Price data fetch failed for {tickers_str}.\n"
                    f"Error: {price_result.get('error', 'Unknown error')}\n"
                    f"\n"
                    f"Possible causes:\n"
                    f"  - Invalid ticker symbols\n"
                    f"  - No data available for the period ({period})\n"
                    f"  - Network/API error\n"
                    f"\n"
                    f"Please verify tickers are valid and try again."
                )
            
            # Calculate covariance
            print(f"  Calculating covariance...")
            cov_result = agent.calculate_covariance_tool(
                tickers=tickers_str,
                period=period
            )
            
            if not cov_result.get("success"):
                raise DataCalculationError(
                    f"Covariance calculation failed for {tickers_str}.\n"
                    f"Error: {cov_result.get('error', 'Unknown error')}\n"
                    f"\n"
                    f"This usually means insufficient price data.\n"
                    f"Need at least 252 trading days for reliable covariance."
                )
            
            # Calculate returns
            print(f"  Calculating returns...")
            returns_result = {}
            if hasattr(agent, 'calculate_returns_tool'):
                returns_result = agent.calculate_returns_tool(
                    tickers=tickers_str,
                    period=period
                )
            
            # ✅ STRICT: Only accept raw float data
            if returns_result.get("success"):
                raw_rets = returns_result.get("annualized_returns_raw")
                
                if not raw_rets:
                    raise DataCalculationError(
                        f"Returns calculation succeeded but 'annualized_returns_raw' is missing.\n"
                        f"Available keys: {list(returns_result.keys())}\n"
                        f"\n"
                        f"This indicates a data contract violation.\n"
                        f"DataAgent.calculate_returns_tool() MUST return 'annualized_returns_raw' as dict[str, float].\n"
                        f"\n"
                        f"DO NOT return formatted strings like '5.0%' - use raw floats like 0.05.\n"
                        f"Fix the tool output, not the parser."
                    )
                
                # Validate data type
                if not isinstance(raw_rets, dict):
                    raise DataCalculationError(f"annualized_returns_raw must be dict, got {type(raw_rets)}")
                
                # Validate all values are numeric
                for ticker, value in raw_rets.items():
                    if not isinstance(value, (int, float)):
                        raise DataCalculationError(
                            f"Return for {ticker} must be numeric, got {type(value)}: {value}\n"
                            f"Data contract violation: Returns must be floats (0.05), not strings ('5%')"
                        )
                
                expected_returns = raw_rets
            else:
                raise DataCalculationError(
                    f"Returns calculation failed: {returns_result.get('error')}\n"
                    f"Cannot proceed without valid return estimates."
                )
            
            # Build result
            # STRICT: volatilities travel as floats, not display strings.
            # "15.33%" forces every downstream consumer to parse it back, which
            # is the hot-potato violation in miniature.
            raw_vols = cov_result.get("annualized_volatilities_raw")
            if not raw_vols:
                raise DataCalculationError(
                    "Covariance succeeded but 'annualized_volatilities_raw' is missing.\n"
                    f"Available keys: {list(cov_result.keys())}\n"
                    "\n"
                    "Data contract violation. Volatilities must reach shared_data as\n"
                    "floats (0.1533), not formatted strings ('15.33%').\n"
                    "Fix the producer, not the consumer."
                )

            # Spot rates for every holding priced in a currency other than
            # the portfolio's, on the date of that holding's latest close
            # (expected_values.md D16, D17). Fetched beside the prices and
            # published only for those dates; the year of rates stays in the
            # database. A single-currency portfolio publishes an empty table
            # and makes no call. A holding with no currency is left to the
            # analysis node's lookup, which raises naming it.
            as_of_dates = price_result.get("as_of_dates", {})
            base_currency = ctx.base_currency
            needed: Dict[str, set] = {}
            for h in holdings or []:
                currency = h.get("currency")
                as_of = as_of_dates.get(h["ticker"])
                if base_currency and currency and currency != base_currency and as_of:
                    needed.setdefault(currency, set()).add(as_of)
            fx_rates: Dict[str, Dict[str, float]] = {}
            if needed:
                print(f"  Fetching spot rates into {base_currency} for {sorted(needed)}...")
                fx_result = agent.fetch_fx_rates_tool(
                    base_currency,
                    {c: sorted(d) for c, d in needed.items()},
                    period=period,
                )
                if not fx_result.get("success"):
                    raise DataCalculationError(
                        f"Spot rate fetch failed for {sorted(needed)} into {base_currency}.\n"
                        f"Error: {fx_result.get('error', 'Unknown error')}"
                    )
                fx_rates = fx_result.get("rates", {})

            result = {
                "success": True,
                "prices": price_result,
                "covariance": cov_result,
                "returns": returns_result,
                "tickers": tickers,
                "period": period,
            }

            # Store shared data
            shared_updates = {
                "tickers": tickers,
                "tickers_str": tickers_str,
                "latest_prices": price_result.get("latest_prices", {}),
                "as_of_dates": as_of_dates,
                "base_currency": base_currency,
                "fx_rates": fx_rates,
                "price_window": price_result.get("window"),
                "covariance_matrix": cov_result.get("covariance_matrix", {}),
                "covariance_method": cov_result.get("method"),
                "volatilities": raw_vols,
                "expected_returns": expected_returns,  # GUARANTEED to exist
                "holdings": build_holdings_summary(holdings),
                "cash_balance": ctx.cash_balance,
            }
            
            if "price_data" in price_result:
                shared_updates["price_data_json"] = price_result.get("price_data")
            
            print(f"  ✓ Data loaded successfully")
            print(f"  ✓ Expected returns: {list(expected_returns.keys())}")
            
            return {
                **mark_agent_complete(state, "DataAgent", result),
                **holdings_update,
                "shared_data": {**state.get("shared_data", {}), **shared_updates},
            }
        
        except DataCalculationError:
            # Re-raise data errors
            raise
        except ImportError as e:
            # DataAgent not available - this is a development/testing scenario
            raise RuntimeError(
                f"DataAgent module not available: {e}\n"
                f"\n"
                f"This system requires the DataAgent to fetch real market data.\n"
                f"Cannot proceed without it.\n"
                f"\n"
                f"Please ensure:\n"
                f"  1. data_agent.py is in src/agents/\n"
                f"  2. All dependencies are installed\n"
                f"  3. Database is properly configured"
            )
    
    except (PortfolioContextError, DataCalculationError, RuntimeError) as e:
        # These are expected errors with clear messages
        logger.error(f"DataAgent error: {e}")
        return {
            **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"DataAgent: {str(e)}"),
        }
    
    except Exception as e:
        # Unexpected error
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Unexpected DataAgent error:\n{error_detail}")
        return {
            **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"DataAgent unexpected error: {str(e)}"),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)



# =============================================================================
# MACRO AGENT NODE
# =============================================================================

async def macro_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Macro Agent node - analyzes VIX, yield curve, and market regime.
    """

    tracer = get_tracer()
    agent_ctx = None

    # ✅ ROBUST TRACING START
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("MacroAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in MacroAgent (ignoring): {e}")


    try:
        # Try to import and use the actual MacroAgent
        try:
            from .macro_agent import create_macro_agent
            agent = create_macro_agent(verbose=False)
            
            # Fetch macro data
            fetch_result = agent.fetch_macro_data_tool(indicators="VIX,TNX_10Y,IRX_3M", days=30)
            
            # Get snapshot
            snapshot = agent.get_macro_snapshot_tool()
            
            # Assess regime
            vix_data = snapshot.get("vix", {})
            yc_data = snapshot.get("yield_curve", {})
            vix_level = vix_data.get("value")
            if vix_level is None:
                raise DataCalculationError("VIX data missing from snapshot")

            slope = yc_data.get("slope_raw")
            if slope is None:
                raise DataCalculationError("Yield curve data missing from snapshot")

            regime = agent.assess_regime_tool(
                vix_level=vix_level,
                yield_curve_slope=slope
            )
            
            result = {
                "success": True,
                "snapshot": snapshot,
                "regime": regime,
                "fetch_result": fetch_result,
            }
            
            # Store regime in shared data
            return {
                **mark_agent_complete(state, "MacroAgent", result),
                "shared_data": {
                    **state.get("shared_data", {}),
                    "macro_regime": regime,
                    "macro_snapshot": snapshot,
                },
            }
            
        except ImportError as e:
            logger.error(f"Agent error: {e}")
            
            return {
                **mark_agent_complete(state, "MacroAgent", {"success": False, "error": str(e)}),
                **add_error(state, f"MacroAgent: {str(e)}"),
            }
    
    except Exception as e:
        return {
            **mark_agent_complete(state, "MacroAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"MacroAgent error: {str(e)}"),
        }
    finally:
        # ✅ ROBUST TRACING END
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)

# =============================================================================
# PORTFOLIO ANALYSIS AGENT NODE
# =============================================================================

async def portfolio_analysis_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Computes allocation from the holdings, prices and cash DataAgent published.

    Reads only `shared_data` - no database, no provider calls. DataAgent fetches;
    this agent computes; the synthesizer formats. Publishes both the asset-class
    and sector breakdowns, the P&L of every position, and portfolio
    volatility, because 1.1, 1.4, 1.2 and 1.3 each need a different one and
    choosing between computed figures is selection rather than computation.
    The router's `measure` says which was asked for; the synthesizer reads it,
    this node does not.

    Every figure is in the portfolio's base currency (D15). A holding priced
    in another currency is valued through the spot rate on its price's date,
    read from the table DataAgent published; the rate and its date are
    published beside the price's (D16). A foreign holding with no rate for
    that day stops the node (D17): the answer is a refusal naming the
    currency and the date, and nothing is published.

    Reference: expected_values.md Parts 1-4 and 8 C, decisions D1-D8, D15-D18.
    """
    tracer = get_tracer()
    agent_ctx = None

    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("PortfolioAnalysisAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in PortfolioAnalysisAgent (ignoring): {e}")

    print("\n" + "=" * 80)
    print("PORTFOLIO ANALYSIS AGENT - Computing allocation")
    print("=" * 80)

    try:
        shared = state.get("shared_data", {})

        # STRICT: every input comes from DataAgent. No fallbacks - a default
        # here would produce an allocation against a denominator nobody chose.
        holdings = shared.get("holdings")
        if not holdings:
            raise DataCalculationError(
                "No holdings in shared_data.\n"
                "PortfolioAnalysisAgent requires DataAgent to run first with a "
                "portfolio_id.\n"
                "Check the plan puts DataAgent before PortfolioAnalysisAgent."
            )

        prices = shared.get("latest_prices")
        if not prices:
            raise DataCalculationError(
                "No latest_prices in shared_data.\n"
                "DataAgent must provide prices before allocation is computed."
            )

        as_of_dates = shared.get("as_of_dates")
        if not as_of_dates:
            raise DataCalculationError(
                "No as_of_dates in shared_data.\n"
                "Every figure derived from market data must state its as-of "
                "date (benchmark.md Part 3b). DataAgent publishes these "
                "alongside latest_prices; absent dates are not current dates."
            )

        cash_balance = shared.get("cash_balance")
        if cash_balance is None:
            raise DataCalculationError(
                "No cash_balance in shared_data.\n"
                "Per expected_values.md D2 cash belongs in the allocation "
                "denominator. Absent cash is not zero cash - it is an unknown "
                "denominator, and the percentages would all be wrong."
            )

        # The base currency and the rate table are DataAgent's to publish
        # (D15, D17). An absent key is neither a dollar portfolio nor an
        # empty table: it is an input nobody supplied. An empty table is a
        # valid one, and is what a single-currency portfolio carries.
        base_currency = shared.get("base_currency")
        if not base_currency:
            raise DataCalculationError(
                "No base_currency in shared_data.\n"
                "Every figure is reported in the portfolio's currency "
                "(expected_values.md D15); without it nothing can be valued."
            )
        if "fx_rates" not in shared:
            raise DataCalculationError(
                "No fx_rates in shared_data.\n"
                "DataAgent publishes the spot rates on the held tickers' as-of "
                "dates (D17), an empty table when no holding is foreign. An "
                "absent table is not an empty one."
            )
        fx_rates = shared["fx_rates"]

        from portfolio_tool.quant.allocation import (
            allocation_by_asset_class,
            allocation_by_position,
            allocation_by_sector,
            position_pnl,
        )
        from portfolio_tool.quant.fx import spot_rates

        # One entry per holding: None when its currency is the base, else the
        # rate on its price's date (D16). A foreign holding with no rate for
        # that day raises here, before anything is valued, and the answer is
        # the refusal Part 8 C describes, not a value at another rate.
        rates = spot_rates(holdings, as_of_dates, base_currency, fx_rates)

        by_class = allocation_by_asset_class(holdings, prices, cash_balance, rates)
        by_sector = allocation_by_sector(holdings, prices, cash_balance, rates)
        by_position = allocation_by_position(holdings, prices, cash_balance, rates)
        pnl = position_pnl(holdings, prices, rates)

        # An allocation line aggregates several holdings, so no single holding's
        # date describes it. Reduce to the worst case: no figure is presented as
        # fresher than its stalest input. That can understate freshness and
        # cannot overstate it, which is the safe direction for a data-age field.
        #
        # Computed here rather than in the synthesizer so the value lands in
        # shared_data and can be asserted on - anything the synthesizer derives
        # exists only as text in the answer. Compliance needs the same number.
        #
        # `min` is chronological only because these are YYYY-MM-DD strings, in
        # which lexicographic order matches date order. Nothing enforces that
        # format; it comes from the strftime in data_agent.py.
        held = [h["ticker"] for h in holdings if h.get("ticker") in as_of_dates]
        if not held:
            # allocation_by_asset_class has already raised on any unpriced
            # holding, so a partial gap cannot reach here. This is the
            # all-missing case, and it means the price summary lost its dates.
            raise DataCalculationError(
                "No as-of date for any held ticker.\n"
                f"Holdings: {sorted({h.get('ticker') for h in holdings})}\n"
                f"Dated:    {sorted(as_of_dates)}\n"
                "The allocation cannot state how current it is."
            )
        stalest = min(held, key=lambda t: as_of_dates[t])

        # Equal dates are the normal case - nine holdings, one close - and the
        # synthesizer has to know. Naming a stalest holding when nothing is
        # stale invents a distinction the data does not carry.
        uniform = len({as_of_dates[t] for t in held}) == 1

        def _lines(allocation):
            return [
                {
                    "label": line.label,
                    "market_value": round(line.market_value, 2),
                    "cost_basis": round(line.cost_basis, 2),
                    "pct_of_sectored": line.pct_of_sectored,
                    "pct_of_invested": line.pct_of_invested,
                    "pct_of_total": line.pct_of_total,
                    "tickers": line.tickers,
                }
                for line in allocation.lines
            ]

        # Every position, whichever one was asked about: selecting is the
        # synthesizer's job. One holding, one close, so the as-of is per
        # position and needs no reduction. A held ticker with no date cannot
        # state its age and is not published silently as if it could.
        undated = [t for t in pnl if t not in as_of_dates]
        if undated:
            raise DataCalculationError(
                f"No as-of date for priced holdings: {sorted(undated)}.\n"
                "Every P&L figure must state its date (benchmark.md Part 3b)."
            )
        # Portfolio volatility (expected_values.md Part 4, D7): market-value
        # weights of the invested assets, cash excluded, against the
        # covariance matrix DataAgent published. Every input is read from
        # shared_data and checked for presence: a missing matrix or window
        # cannot be defaulted into a figure that still states its basis.
        cov_matrix = shared.get("covariance_matrix")
        if not cov_matrix:
            raise DataCalculationError(
                "No covariance_matrix in shared_data.\n"
                "DataAgent publishes it for up to ten tickers; see "
                "CovarianceResult.to_dict. Portfolio volatility cannot be "
                "computed without it."
            )
        window = shared.get("price_window")
        if not window:
            raise DataCalculationError(
                "No price_window in shared_data.\n"
                "A volatility figure must state the window it was computed "
                "over (benchmark 1.3: basis of calculation traceable)."
            )

        from portfolio_tool.quant.risk_metrics import portfolio_volatility_by_ticker

        invested = by_class.invested_value
        weights = {p.ticker: p.market_value / invested for p in pnl.values()}
        vol = portfolio_volatility_by_ticker(weights, cov_matrix)

        portfolio_volatility_summary = {
            "annualised": vol,
            "weights_basis": "market value of invested assets, cash excluded",
            "weights": {t: round(w, 6) for t, w in weights.items()},
            "weights_as_of": as_of_dates[stalest],
            "window": window,
            "covariance_method": shared.get("covariance_method"),
            "annualisation": config.data.trading_days_per_year,
        }

        # `price` is the quote in `currency`; cost basis, average price,
        # market value and P&L are in the base currency (D18). `rate` and
        # `rate_as_of` are the spot rate the value went through and its
        # day, None when the currencies agree (D16, D17). Both dates travel
        # so the formatter states them and derives nothing.
        position_pnl_summary = {
            t: {
                "quantity": p.quantity,
                "average_price": p.average_price,
                "price": p.price,
                "currency": p.currency,
                "cost_basis": round(p.cost_basis, 2),
                "market_value": round(p.market_value, 2),
                "pnl_abs": round(p.pnl_abs, 2),
                "pnl_pct": p.pnl_pct,
                "purchase_date": p.purchase_date,
                "as_of": as_of_dates[t],
                "rate": p.rate,
                "rate_as_of": p.rate_as_of,
            }
            for t, p in pnl.items()
        }

        allocation_summary = {
            "base_currency": base_currency,
            "by_asset_class": {
                "lines": _lines(by_class),
                "invested_value": round(by_class.invested_value, 2),
                "cash_balance": round(by_class.cash_balance, 2),
                "total_value": round(by_class.total_value, 2),
            },
            "by_sector": {
                "lines": _lines(by_sector),
                "invested_value": round(by_sector.invested_value, 2),
                "sectored_value": round(by_sector.sectored_value, 2),
                "total_value": round(by_sector.total_value, 2),
            },
            # Part 7's IPS-4.1 table: concentration as a view of the same
            # computation. The checker reads each line's share of total
            # under IPS-4.1 and 4.2; the formatter prints it largest first.
            "by_position": {
                "lines": _lines(by_position),
                "invested_value": round(by_position.invested_value, 2),
                "cash_balance": round(by_position.cash_balance, 2),
                "total_value": round(by_position.total_value, 2),
            },
            "as_of": {
                "worst_case": as_of_dates[stalest],
                "stalest": stalest,
                "uniform": uniform,
            },
        }

        print(f"  Total portfolio value: {by_class.total_value:,.2f}")
        for line in by_class.lines:
            print(f"    {line.label:<16} {line.pct_of_total:>7.2%}")
        print(f"  Position P&L computed for {len(pnl)} positions")
        print(f"  Portfolio volatility: {vol:.4%} over {window['closes']} closes")

        result = {
            "success": True,
            "agent_name": "PortfolioAnalysisAgent",
            "base_currency": base_currency,
            "allocation": allocation_summary,
            "position_pnl": position_pnl_summary,
            "portfolio_volatility": portfolio_volatility_summary,
        }

        return {
            **mark_agent_complete(state, "PortfolioAnalysisAgent", result),
            "shared_data": {
                **shared,
                "allocation": allocation_summary,
                "position_pnl": position_pnl_summary,
                "portfolio_volatility": portfolio_volatility_summary,
            },
        }

    except Exception as e:
        return {
            **mark_agent_complete(
                state, "PortfolioAnalysisAgent", {"success": False, "error": str(e)}
            ),
            **add_error(state, f"PortfolioAnalysisAgent: {str(e)}"),
        }
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# COMPLIANCE AGENT NODE
# =============================================================================

async def compliance_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Compliance Agent node - the IPS applied to the published allocation.

    Reads only `shared_data`: the allocation block PortfolioAnalysisAgent
    published, and the holdings summary for each position's instrument
    type. No database, no provider, no recomputation
    (tests/golden/KNOWN_GAPS.md, "wip/phase7-snapshot was read and rejected").
    Loads the policy from ips.toml on every run, so a broken policy file
    fails the run that needs it and not the import of everything.

    Publishes `shared_data["compliance"]`: the loaded policy (id, type and
    the clause text a citation quotes), its statements, the D2 denominator,
    the allocation's as-of copied and not reduced again, one finding per
    (clause, subject, bound), and the `no_clause` marker. The synthesizer
    formats and cites; this node does not.

    Three modes, decided by the router's parameters and nothing else:
    neither set is a check of the portfolio; `hypothetical_weight` is a
    proposed weight in one position, refused or permitted with no portfolio
    measured (3.1); `policy_topic` is the user's own words for a topic, and
    the lookup is which clauses' topics occur inside those words (3.4) - the
    owner's vocabulary contained in the question, no similarity, no nearest
    clause, and the router is never shown the vocabulary. The last two
    publish no total and no as-of, because nothing was priced.

    Reference: expected_values.md Part 7, decisions D2 and D9.
    """
    tracer = get_tracer()
    agent_ctx = None

    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("ComplianceAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in ComplianceAgent (ignoring): {e}")

    print("\n" + "=" * 80)
    print("COMPLIANCE AGENT - Checking the portfolio against the IPS")
    print("=" * 80)

    try:
        shared = state.get("shared_data", {})
        params = (state.get("router_decision") or {}).get("parameters") or {}
        weight = params.get("hypothetical_weight")
        topic = params.get("policy_topic")
        if weight is not None and topic is not None:
            raise DataCalculationError(
                "Both hypothetical_weight and policy_topic are set; the router's "
                "validator rejects this, so it did not run."
            )

        from contextlib import nullcontext
        from dataclasses import asdict

        from portfolio_tool.compliance import check, refuse
        from portfolio_tool.ips import load_ips, normalise_topic

        ips = load_ips()
        total_value = None
        as_of = None
        no_clause = False
        topic_block = None
        by_status = {}

        if topic is not None:
            # Lookup: the owner's topic words inside the user's words, nothing else.
            on_topic = ips.clauses_on(topic)
            findings = []
            no_clause = not on_topic
            topic_block = {"asked": normalise_topic(topic), "clauses": [c.id for c in on_topic]}
            print(f"  topic {topic_block['asked']!r}: "
                  + (", ".join(topic_block["clauses"]) if on_topic else "no clause"))

        elif weight is not None:
            # A proposed weight in one position: no portfolio, no total, no date.
            with (agent_ctx.trace_tool("refuse_ips") if agent_ctx else nullcontext()) as tool_ctx:
                if tool_ctx:
                    tool_ctx.set_input({"policy": ips.path, "weight": weight})
                findings = refuse(ips, weight)
                for f in findings:
                    by_status[f.status] = by_status.get(f.status, 0) + 1
                if tool_ctx:
                    tool_ctx.set_output({"findings": by_status})
            print(f"  hypothetical {weight:.2%} in one position: "
                  + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))

        else:
            # STRICT: every input is PortfolioAnalysisAgent's output. No fallback;
            # a check against figures nobody computed is a verdict nobody asked for.
            allocation = shared.get("allocation")
            holdings = shared.get("holdings")
            for key, value in (("allocation", allocation), ("holdings", holdings)):
                if not value:
                    raise DataCalculationError(
                        f"No {key} in shared_data.\n"
                        "ComplianceAgent requires DataAgent and PortfolioAnalysisAgent "
                        "to run first. Check the plan puts both before ComplianceAgent."
                    )
            instrument_types = {h["ticker"]: h.get("instrument_type") for h in holdings}

            # The checker is this agent's one tool call, traced as one: inputs
            # and outputs as counts, never the findings themselves (hot potato).
            # A raise inside leaves the trace with the exception recorded.
            with (agent_ctx.trace_tool("check_ips") if agent_ctx else nullcontext()) as tool_ctx:
                if tool_ctx:
                    tool_ctx.set_input({
                        "policy": ips.path,
                        "clauses": len(ips),
                        "checkable": len(ips.checkable),
                        "positions": len((allocation.get("by_position") or {}).get("lines") or []),
                    })
                findings = check(ips, allocation, instrument_types)
                for f in findings:
                    by_status[f.status] = by_status.get(f.status, 0) + 1
                if tool_ctx:
                    tool_ctx.set_output({"findings": by_status})
            total_value = allocation["by_asset_class"]["total_value"]
            as_of = allocation.get("as_of")

            print(f"  {len(ips.checkable)} checkable clauses, {len(ips.statements)} statements")
            print("  findings: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
            for f in findings:
                if f.status == "breach":
                    print(f"    {f.clause:<8} {f.subject:<14} {f.observed:>7.2%} vs "
                          f"{f.limit:.0%} {f.bound}  {f.distance_pp:+.2f} pp")

        compliance_summary = {
            "policy": {c.id: {"type": c.type, "text": c.text} for c in ips},
            "statements": [{"clause": c.id, "text": c.text} for c in ips.statements],
            "total_value": total_value,
            "as_of": as_of,
            "findings": [asdict(f) for f in findings],
            "no_clause": no_clause,
            "topic": topic_block,
        }

        result = {
            "success": True,
            "agent_name": "ComplianceAgent",
            "compliance": compliance_summary,
        }

        return {
            **mark_agent_complete(state, "ComplianceAgent", result),
            "shared_data": {**shared, "compliance": compliance_summary},
        }

    except Exception as e:
        return {
            **mark_agent_complete(
                state, "ComplianceAgent", {"success": False, "error": str(e)}
            ),
            **add_error(state, f"ComplianceAgent: {str(e)}"),
        }
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# FIXED: OPTIMIZATION AGENT NODE
# =============================================================================

async def optimization_agent_node(state: AgentState) -> Dict[str, Any]:
    """Optimization Agent node - runs portfolio optimization."""
    tracer = get_tracer()
    agent_ctx = None

    # ✅ ROBUST TRACING START
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("OptimizationAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in OptimizationAgent (ignoring): {e}")

    try:
        # ✅ STRICT: Get required data
        shared = state.get("shared_data", {})
        
        # Validate shared data exists
        if not shared:
            raise ValueError(
                "No shared_data from DataAgent.\n"
                "OptimizationAgent requires DataAgent to run first.\n"
                "Check workflow execution order."
            )
        
        # ✅ STRICT: Get tickers (NO fallback)
        tickers = shared.get("tickers")
        if not tickers:
            raise ValueError(
                "No tickers in shared_data.\n"
                "DataAgent must provide tickers.\n"
                "This indicates DataAgent failed or didn't run."
            )
        
        # ✅ STRICT: Get expected returns (NO fallback)
        expected_returns = shared.get("expected_returns")
        if not expected_returns:
            raise DataCalculationError(
                "No expected_returns in shared_data.\n"
                "Cannot optimize without return estimates.\n"
                "DataAgent must calculate returns first."
            )
        
        # ✅ STRICT: Get covariance (NO fallback)
        covariance_matrix = shared.get("covariance_matrix")
        if not covariance_matrix:
            raise DataCalculationError(
                "No covariance_matrix in shared_data.\n"
                "Cannot optimize without risk estimates.\n"
                "DataAgent must calculate covariance first."
            )
        
        # Validate data types
        if not isinstance(expected_returns, dict):
            raise ValueError(f"expected_returns must be dict, got {type(expected_returns)}")
        
        if not isinstance(covariance_matrix, dict):
            raise ValueError(f"covariance_matrix must be dict, got {type(covariance_matrix)}")
        
        # =========================================================================
        # ⭐ STRICT: Matrix Alignment & Shape Validation (Input Contract)
        # =========================================================================
        
        ret_tickers = set(expected_returns.keys())
        cov_tickers = set(covariance_matrix.keys())

        if ret_tickers != cov_tickers:
            raise DataCalculationError(
                f"Data alignment error:\n"
                f"  Returns tickers: {sorted(ret_tickers)}\n"
                f"  Covariance tickers: {sorted(cov_tickers)}\n"
                f"All tickers must have both returns and covariance data."
            )

        # Validate Shape: Covariance matrix must be square (NxN)
        for ticker in cov_tickers:
            if ticker not in covariance_matrix:
                raise DataCalculationError(f"Covariance missing entry for {ticker}")
            
            ticker_cov = covariance_matrix[ticker]
            if not isinstance(ticker_cov, dict):
                raise DataCalculationError(f"Covariance for {ticker} must be dict, got {type(ticker_cov)}")
            
            cov_inner_tickers = set(ticker_cov.keys())
            if cov_inner_tickers != cov_tickers:
                raise DataCalculationError(f"Covariance matrix for {ticker} is not square.")

        print(f"  ✓ Matrix alignment validated: {len(ret_tickers)} tickers")
        
        # =========================================================================
        
        # Get optional parameters
        router_decision = state.get("router_decision") or {}
        params = router_decision.get("parameters", {})
        max_vol = params.get("max_volatility")
        
        tickers_str = ",".join(tickers)
        
        print(f"  [DEBUG] Optimizing for tickers: {tickers}")
        
        # Import and run agent
        try:
            from .optimization_agent import create_optimization_agent
            import json
            
            agent = create_optimization_agent(verbose=False)
            
            # Run optimization
            result = agent.optimize_portfolio_tool(
                tickers=tickers_str,
                expected_returns=json.dumps(expected_returns),
                covariance_matrix=json.dumps(covariance_matrix),
                method="max_sharpe",
                max_volatility=max_vol,
                min_weight=0.0,
                max_weight=0.40,
            )

            # =========================================================================
            # ⭐ STRICT: Output Contract Enforcement (Bank-Grade Fix)
            # Validate that the Agent returned compliant data before passing it on.
            # =========================================================================
            if result.get("success"):
                weights = result.get("weights", {})
                
                # 1. Validate Types (Must be floats)
                clean_weights = {}
                total_weight = 0.0
                
                for ticker, weight in weights.items():
                    # Strict Type Check
                    if not isinstance(weight, (int, float)):
                        # If we strictly forbid strings, we raise here.
                        # However, JSON serialization might have converted to strings, so we parse carefully.
                        if isinstance(weight, str):
                            try:
                                val = float(weight.replace("%", "")) / 100.0 if "%" in weight else float(weight)
                            except ValueError:
                                raise ValueError(f"Invalid weight format for {ticker}: {weight}")
                        else:
                            raise ValueError(f"Invalid weight type for {ticker}: {type(weight)}")
                    else:
                        val = float(weight)
                        
                    clean_weights[ticker] = val
                    total_weight += val
                
                # 2. Validate Sum (Must be ~1.0 for a fully invested portfolio)
                # Allow small floating point drift (0.99 - 1.01)
                if not (0.99 <= total_weight <= 1.01):
                    raise RuntimeError(f"Optimization weights sum to {total_weight:.4f}, expected 1.0")
                
                # Update result with clean, validated data
                result["weights"] = clean_weights
                # "optimal_weights" is the standard key used by downstream agents
                result["optimal_weights"] = clean_weights
            
            # =========================================================================
            
            if not result.get("success"):
                raise RuntimeError(f"Optimization failed: {result.get('error')}")
            
            return {
                **mark_agent_complete(state, "OptimizationAgent", result),
                "shared_data": {
                    **shared,
                    "optimal_weights": result.get("weights", {}),
                },
            }
            
        except ImportError as e:
            raise RuntimeError(
                f"OptimizationAgent module not available: {e}\n"
                "Cannot run optimization without OptimizationAgent."
            )
    
    except (ValueError, DataCalculationError, RuntimeError) as e:
        logger.error(f"OptimizationAgent error: {e}")
        return {
            **mark_agent_complete(state, "OptimizationAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"OptimizationAgent: {str(e)}"),
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "OptimizationAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"OptimizationAgent unexpected error: {str(e)}"),
        }
    
    finally:
        # ✅ ROBUST TRACING END
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)
# =============================================================================
# REBALANCE AGENT NODE
# =============================================================================

async def rebalance_agent_node(state: AgentState) -> Dict[str, Any]:
    """Rebalance Agent node - calculates drift and generates trade list."""

    tracer = get_tracer()
    agent_ctx = None

    # ✅ ROBUST TRACING START
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("RebalanceAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in RebalanceAgent (ignoring): {e}")
    
    try:
        # Validate portfolio context
        if not validate_portfolio_context(state):
            raise PortfolioContextError(
                "Portfolio specified but holdings not loaded.\n"
                "DataAgent must load portfolio holdings first."
            )
        
        # ✅ STRICT: Get holdings (NO fallback)
        holdings = state.get("portfolio_holdings")
        
        if not holdings:
            # Ad-hoc query without portfolio - skip rebalancing
            return mark_agent_complete(state, "RebalanceAgent", {
                "success": True,
                "message": "Rebalancing skipped - no portfolio specified"
            })
        
        # ✅ STRICT: Get prices from DataAgent (NO fallback)
        shared = state.get("shared_data", {})
        prices = shared.get("latest_prices")
        
        if not prices:
            raise DataCalculationError(
                "No latest_prices in shared_data.\n"
                "Cannot calculate rebalancing without current prices.\n"
                "DataAgent must fetch price data first."
            )
        
        # ✅ STRICT: Get target weights from OptimizationAgent (NO fallback)
        opt_result = state.get("sub_results", {}).get("OptimizationAgent", {})
        target_weights = opt_result.get("optimal_weights") or opt_result.get("weights")
        
        if not target_weights:
            raise ValueError(
                "No target weights from OptimizationAgent.\n"
                "Cannot rebalance without target allocation.\n"
                "OptimizationAgent must run before rebalancing."
            )
        
        # Extract current positions
        current_positions = get_current_positions(holdings)
        
        # ✅ STRICT: Calculate total value (NO fallback)
        total_value = 0.0
        for ticker, qty in current_positions.items():
            price = prices.get(ticker)
            if price is None:
                raise DataCalculationError(
                    f"No price available for {ticker}.\n"
                    f"Cannot calculate portfolio value.\n"
                    f"DataAgent must fetch prices for all holdings."
                )
            total_value += qty * price
        
        if total_value <= 0:
            raise ValueError(
                f"Portfolio value is ${total_value:.2f}.\n"
                "Cannot rebalance portfolio with zero or negative value.\n"
                "Check holdings and prices."
            )
        
        print(f"  [DEBUG] Portfolio value: ${total_value:,.2f}")
        print(f"  [DEBUG] Current positions: {current_positions}")
        print(f"  [DEBUG] Target weights: {target_weights}")
        
        # Import and run agent
        try:
            from .rebalance_agent import create_rebalance_agent
            agent = create_rebalance_agent(verbose=False)
            
            result = agent.analyze_rebalance_tool(
                current_weights=current_positions,
                target_weights=target_weights,
                portfolio_value=total_value,
                prices=prices
            )
            
            if not result.get("success"):
                raise RuntimeError(f"Rebalancing failed: {result.get('error')}")
            
            # Add TAA recommendation if available
            regime = shared.get("macro_regime")
            if regime:
                result["taa_signal"] = {
                    "regime": regime.get("regime", "NEUTRAL"),
                    "equity_adjustment": regime.get("equity_adjustment", 0),
                }
            
            return mark_agent_complete(state, "RebalanceAgent", result)
            
        except ImportError as e:
            raise RuntimeError(
                f"RebalanceAgent module not available: {e}\n"
                "Cannot calculate rebalancing without RebalanceAgent."
            )
    
    except (PortfolioContextError, DataCalculationError, ValueError, RuntimeError) as e:
        logger.error(f"RebalanceAgent error: {e}")
        return {
            **mark_agent_complete(state, "RebalanceAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"RebalanceAgent: {str(e)}"),
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "RebalanceAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"RebalanceAgent unexpected error: {str(e)}"),
        }
    
    finally:
        # ✅ ROBUST TRACING END
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)

# =============================================================================
# BACKTEST AGENT NODE
# =============================================================================

async def backtest_agent_node(state: AgentState) -> Dict[str, Any]:
    """Backtest Agent node - runs historical simulation."""

    tracer = get_tracer()
    agent_ctx = None

    # ✅ ROBUST TRACING START
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("BacktestAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in BacktestAgent (ignoring): {e}")
    
    try:
        # ✅ STRICT: Get required data from shared_data
        shared = state.get("shared_data", {})
        
        if not shared:
            raise ValueError(
                "No shared_data available.\n"
                "BacktestAgent requires data from DataAgent and OptimizationAgent."
            )
        
        # ✅ STRICT: Get tickers (NO fallback)
        tickers = shared.get("tickers")
        if not tickers:
            raise ValueError(
                "No tickers in shared_data.\n"
                "DataAgent must provide tickers."
            )
        
        # ✅ STRICT: Get optimal weights (NO fallback)
        weights = shared.get("optimal_weights")
        if not weights:
            raise ValueError(
                "No optimal_weights in shared_data.\n"
                "Cannot backtest without target allocation.\n"
                "OptimizationAgent must run before backtesting."
            )
        
        # ✅ STRICT: Get price data (NO fallback)
        price_data_json = shared.get("price_data_json")
        if not price_data_json:
            raise DataCalculationError(
                "No price_data_json in shared_data.\n"
                "Cannot backtest without historical price data.\n"
                "DataAgent must fetch price history first."
            )
        
        tickers_str = ",".join(tickers)
        
        print(f"  [DEBUG] Backtesting {len(tickers)} tickers")
        print(f"  [DEBUG] Weights: {weights}")
        
        # Import and run agent
        try:
            from .backtest_agent import create_backtest_agent
            import json
            
            agent = create_backtest_agent(verbose=False)
            
            # =========================================================================
            # ⭐ STRICT: Dynamic Configuration
            # Remove hardcoded financial assumptions. Use Config or User Input.
            # =========================================================================
            
            # Get parameters from router (user intent) or fall back to system config
            params = state.get("router_decision", {}).get("parameters", {})
            
            # 1. Initial Capital: User Input -> Config Default -> Safe Fallback
            initial_capital = params.get("portfolio_value")
            if initial_capital is None:
                initial_capital = getattr(config.backtest, "default_initial_capital", 100000.0)
            
            # 2. Rebalance Frequency
            rebalance_freq = params.get("rebalance_frequency")
            if not rebalance_freq:
                 rebalance_freq = getattr(config.backtest, "default_rebalance_frequency", "quarterly")
                 
            # 3. Drift Threshold
            drift_threshold = params.get("drift_threshold")
            if drift_threshold is None:
                drift_threshold = getattr(config.backtest, "default_drift_threshold", 0.05)

            print(f"  [DEBUG] Backtest config:")
            print(f"    Initial capital: ${initial_capital:,.0f}")
            print(f"    Rebalance: {rebalance_freq}")
            print(f"    Drift threshold: {drift_threshold:.1%}")

            # Run backtest with dynamic parameters
            result = agent.run_backtest_tool(
                tickers=tickers_str,
                weights=json.dumps(weights),
                price_data=price_data_json if isinstance(price_data_json, str) else json.dumps(price_data_json),
                rebalance_frequency=rebalance_freq,
                drift_threshold=drift_threshold,
                taa_rules=None,
                initial_capital=initial_capital,
                signal_data=None,
            )
            
            if not result.get("success"):
                raise RuntimeError(f"Backtest failed: {result.get('error')}")
            
            return mark_agent_complete(state, "BacktestAgent", result)
            
        except ImportError as e:
            raise RuntimeError(
                f"BacktestAgent module not available: {e}\n"
                "Cannot run backtest without BacktestAgent."
            )
    
    except (ValueError, DataCalculationError, RuntimeError) as e:
        logger.error(f"BacktestAgent error: {e}")
        return {
            **mark_agent_complete(state, "BacktestAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"BacktestAgent: {str(e)}"),
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "BacktestAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"BacktestAgent unexpected error: {str(e)}"),
        }
    
    finally:
        # ✅ ROBUST TRACING END
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)

            
# =============================================================================
# SYNTHESIZER NODE
# =============================================================================

# The intents the chain in synthesizer_node formats, stated once beside it. A
# second statement of schemas.INTENTS, checked at import rather than derived,
# as graph.AGENT_NODES is against AGENTS: three branches condition on what
# ran, so a mapping would not be the chain. clarification_needed is the one
# registry value with no
# branch - router_node writes its final_response and the graph exits before
# the synthesizer (KNOWN_GAPS, "Clarification exits the graph on a proxy").
SYNTHESIZER_INTENTS = frozenset({
    "optimization", "macro_analysis", "rebalancing", "backtest", "data_fetch",
    "risk_analysis", "out_of_scope", "compliance",
})
_UNSYNTHESIZED_INTENTS = frozenset({"clarification_needed"})


def _check_synthesizer_intents(handled) -> None:
    expected = set(INTENTS) - _UNSYNTHESIZED_INTENTS
    if set(handled) != expected:
        raise RuntimeError(
            "intent registry and synthesizer chain disagree: schemas.INTENTS "
            f"formats {sorted(expected)}, nodes.SYNTHESIZER_INTENTS has "
            f"{sorted(handled)}. An intent is added to both or to neither."
        )


_check_synthesizer_intents(SYNTHESIZER_INTENTS)


async def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizer node - combines results from all agents into final response.
    
    This is where we create the user-facing response.
    """
    try:
        decision = state.get("router_decision") or {}
        intent = decision.get("intent", "unknown")
        sub_results = state.get("sub_results") or {}
        errors = state.get("errors") or []
        
        # Build response based on intent
        lines = []
        
        if errors:
            lines.append("⚠️ Some issues occurred during analysis:")
            for err in errors[:3]:
                lines.append(f"  - {err}")
            lines.append("")
        
        # Intent-specific formatting
        if intent == "optimization":
            lines.extend(_format_optimization_response(sub_results))
        elif intent == "macro_analysis":
            lines.extend(_format_macro_response(sub_results))
        elif intent == "rebalancing":
            lines.extend(_format_rebalance_response(sub_results))
        elif intent == "backtest":
            lines.extend(_format_backtest_response(sub_results))
        elif intent == "data_fetch" and "PortfolioAnalysisAgent" in sub_results:
            lines.extend(_format_analysis_response(decision, sub_results))
        elif intent == "risk_analysis" and "PortfolioAnalysisAgent" in sub_results:
            lines.extend(_format_analysis_response(decision, sub_results))
        elif intent == "risk_analysis":
            lines.extend(_format_risk_response(sub_results))
        elif intent == "out_of_scope":
            lines.extend(_format_out_of_scope_response())
        elif intent == "compliance":
            lines.extend(_format_compliance_response(decision, sub_results))
        else:
            lines.append("Analysis complete. See details below:")
            for agent, result in sub_results.items():
                lines.append(f"\n{agent}: {'✓' if result.get('success') else '✗'}")
        
        response = "\n".join(lines)
        return set_final_response(state, response)
        
    except Exception as e:
        return set_final_response(state, f"Error synthesizing response: {str(e)}")


# The scope boundary as benchmark.md Part 2 draws it today: security selection
# is out, portfolio mechanics on what is already held are in. Fixed text, not
# model output, so the refusal cannot grow a recommendation. Its eventual home
# is a clause in the IPS, cited like any other; until the IPS lands it lives
# here. tests/benchmark/run_cases.py asserts on the first sentence.
OUT_OF_SCOPE_RESPONSE = [
    "🚫 **OUT OF SCOPE**",
    "",
    "This asks for something outside what this system does.",
    "",
    "It answers questions about the portfolio you already hold - allocation, "
    "P&L per position, volatility - and checks them against your investment "
    "policy. It does not screen, pick, or say whether to buy or sell an "
    "instrument, forecast prices or returns, assess tax, or place orders. "
    "No recommendation is given here.",
]


def _format_compliance_response(decision: Dict, sub_results: Dict) -> List[str]:
    """Format the compliance block. Cites clause ids and the owner's clause
    text; prints the figures the checker published and computes none - the
    benchmark runner holds every percentage in this prose to a finding.

    Three renderings, chosen by what the block carries: a topic lookup, a
    hypothetical weight (no total was measured), or the portfolio check.
    Every reading gives a condition or a citation and no recommendation.

    The portfolio check has a selection axis with two values, both read
    from the router's parameters. `tickers`, the way the P&L formatter reads
    it: filled means the findings on those subjects, empty means every
    finding. `status`, the model's: "breach" means the findings in breach,
    the list "which of my positions are over the limit?" asks for. Both at
    once means both filters. Selection is rendering only - the node checks
    every clause on every run and the block is the full check whatever is
    shown. "Is my JNJ position over any limit?" answers with JNJ's two
    concentration findings, not the 63-line report.
    """
    result = sub_results.get("ComplianceAgent", {})
    if not result.get("success"):
        return ["⚠️ Compliance check failed", "", result.get("error", "unknown error")]
    block = result.get("compliance") or {}
    policy = block.get("policy") or {}
    findings = block.get("findings") or []
    parameters = decision.get("parameters") or {}
    subjects = parameters.get("tickers") or []
    status = parameters.get("status")

    if block.get("topic") is not None:
        return _format_policy_lookup(block, policy)
    if block.get("total_value") is None and findings:
        return _format_hypothetical(findings, policy)
    return _format_policy_check(block, policy, findings, subjects, status)


def _format_policy_lookup(block: Dict, policy: Dict) -> List[str]:
    """What the policy says about a topic. Nothing on it: one sentence, no
    clause id, no nearest clause - the retrieval failure 3.4 exists to
    refuse. Something on it: each clause, id and text verbatim."""
    asked = (block.get("topic") or {}).get("asked", "")
    clause_ids = (block.get("topic") or {}).get("clauses") or []
    if block.get("no_clause") or not clause_ids:
        return [
            "📜 **INVESTMENT POLICY**",
            "",
            f"The investment policy contains nothing on {asked}.",
            "",
            f"It has {len(policy)} clauses and none of them is about this. "
            "Nothing is read into the nearest clause.",
        ]
    lines = ["📜 **INVESTMENT POLICY**", "", f"What the policy says about {asked}:", ""]
    for cid in clause_ids:
        lines.append(f"**{cid}** — {policy.get(cid, {}).get('text', '')}")
    return lines


def _format_hypothetical(findings: List[Dict], policy: Dict) -> List[str]:
    """A proposed weight in one position against the concentration limits.
    Refused or permitted per clause, the clause text, the distance. No
    weighing up: the vocabulary is the clause text and the figures."""
    refused = [f for f in findings if f.get("status") == "refused"]
    weight = findings[0].get("observed")
    lines = [
        "🚫 **NOT PERMITTED BY THE POLICY**" if refused else "✅ **PERMITTED BY THE POLICY**",
        "",
        f"A weight of {weight:.2%} of total value in one position:",
        "",
    ]
    for f in findings:
        lines.append(f"**{f['clause']}** — {policy.get(f['clause'], {}).get('text', '')}")
        if f.get("status") == "refused":
            lines.append(f"  {f['observed']:.2%} against a limit of {f['limit']:.0%}: "
                         f"refused, {f['distance_pp']:+.2f} pp over the limit.")
        else:
            lines.append(f"  {f['observed']:.2%} against a limit of {f['limit']:.0%}: "
                         "within the limit.")
        lines.append("")
    lines.append("**Not done:** no recommendation. The policy states the limit and the "
                 "answer stops there.")
    return lines


def _format_policy_check(block: Dict, policy: Dict, findings: List[Dict],
                         subjects: List[str] = (), status: Optional[str] = None) -> List[str]:
    """The portfolio against every checkable clause, then the conditions
    IPS-5.2 asks for, then the statements the check did not compute, so
    "all rules" is visibly all of them.

    With `subjects` named, only the findings on them: for a position that
    is its instrument and issuer clauses (IPS-4.1, IPS-4.2). IPS-4.3 limits
    the sector, not the position, and the asset-class clauses limit the
    class, so neither is a finding on a ticker. A named subject the check
    has no finding on is said so, and nothing else is printed for it: it is
    not among the holdings the check covered.

    With `status` set, the body is the findings of that status - the breach
    list, every clause included, since the class and sector limits are
    limits too - and the check's coverage stays visible in one line each:
    the clauses within their limits by id with their subjects, the exempt
    funds by name, the statements by id. The model sets status on "does my
    allocation violate any rule" as readily as on "which are over" (read
    from its output, 9 September), so the failure direction is designed in:
    a status the model over-sets shortens the answer and hides nothing.
    No finding of that status is said so, and the coverage still follows.

    Under either selection the statements' text is left out - nothing about
    one position or one breach is in it - and a "Not shown" line names what
    was left out, so the answer says what it did not do (Part 3b)."""
    heading = []
    lines = []
    if subjects:
        selected = [f for f in findings if f.get("subject") in subjects]
        missing = [s for s in subjects if not any(f.get("subject") == s for f in findings)]
        if not selected:
            return [
                "📋 **INVESTMENT POLICY CHECK**",
                "",
                f"The check has no finding on {', '.join(missing)}: not among the "
                "holdings it covered. Nothing else was asked about.",
            ]
        findings = selected
        heading.append(", ".join(s for s in subjects if s not in missing))
        if missing:
            lines.append(f"No finding on {', '.join(missing)}: not among the holdings "
                         "the check covered.")
            lines.append("")
    pool = findings
    if status is not None:
        findings = [f for f in findings if f.get("status") == status]
        heading.append("breaches" if status == "breach" else status)

    title = "📋 **INVESTMENT POLICY CHECK" + (" — " + " — ".join(heading) if heading else "") + "**"
    lines = [title, ""] + lines

    as_of = block.get("as_of") or {}
    if as_of.get("worst_case"):
        if as_of.get("uniform"):
            lines.append(f"**Priced as of {as_of['worst_case']}** — the close "
                         f"for every holding.")
        else:
            lines.append(f"**Priced as of {as_of['worst_case']}** — the oldest "
                         f"close among the holdings ({as_of.get('stalest')}). "
                         f"No figure below is fresher than that.")
        lines.append("")
    if block.get("total_value") is not None:
        lines.append(f"**Total portfolio value:** {block['total_value']:,.2f} "
                     "(including cash; every limit is a share of it)")
        lines.append("")

    if status is not None and not findings:
        lines.append(f"No finding is in {status}"
                     + (f" on {', '.join(subjects)}" if subjects else "") + ".")
    else:
        by_clause: Dict[str, List[Dict]] = {}
        for f in findings:
            by_clause.setdefault(f["clause"], []).append(f)

        lines.append("**Findings by clause**")
        for cid, rows in by_clause.items():
            lines.append("")
            lines.append(f"**{cid}** — {policy.get(cid, {}).get('text', '')}")
            for f in rows:
                if f.get("status") == "exempt":
                    lines.append(f"  {f['subject']}: exempt — a fund, not attributed to an issuer.")
                elif f.get("status") == "breach":
                    lines.append(f"  {f['subject']}: {f['observed']:.2%} of total against "
                                 f"{f['bound']} {f['limit']:.0%} → BREACH, "
                                 f"{f['distance_pp']:+.2f} pp ({f['distance_value']:,.2f}).")
                else:
                    lines.append(f"  {f['subject']}: {f['observed']:.2%} of total against "
                                 f"{f['bound']} {f['limit']:.0%} → within.")

        lines.append("")
        breaches = [f for f in findings if f.get("status") == "breach"]
        lines.append("**What would have to change** (IPS-5.2: the amount that returns each "
                     "figure to its limit, stated as a condition, not a trade)")
        if not breaches:
            lines.append("  No limit is breached.")
        for f in breaches:
            direction = "down" if f["bound"] == "max" else "up"
            lines.append(f"  {f['clause']} {f['subject']}: {direction} {f['distance_pp']:.2f} pp "
                         f"of total ({f['distance_value']:,.2f} at unchanged total).")

    statements = block.get("statements") or []
    selected = bool(subjects) or status is not None
    if status is not None:
        # The coverage, one line each, no figures: what the check found within
        # its limits, what it exempted, what it cited without computing. A
        # band clause emits one finding per bound, so "within" is per
        # (clause, subject) with no bound in breach, the subject named once.
        breached = {(f["clause"], f["subject"]) for f in pool if f.get("status") == "breach"}
        within: Dict[str, List[str]] = {}
        exempt: Dict[str, List[str]] = {}
        for f in pool:
            key = (f["clause"], f["subject"])
            if f.get("status") == "ok" and key not in breached:
                subs = within.setdefault(f["clause"], [])
                if f["subject"] not in subs:
                    subs.append(f["subject"])
            elif f.get("status") == "exempt":
                exempt.setdefault(f["clause"], []).append(f["subject"])
        if within:
            lines.append("")
            lines.append("**Within their limits:** "
                         + "; ".join(f"{cid} {', '.join(subs)}" for cid, subs in within.items()))
        for cid, subs in exempt.items():
            lines.append("")
            lines.append(f"**Exempt under {cid}**, funds not attributed to an issuer: "
                         + ", ".join(subs))
        if statements and not subjects:
            lines.append("")
            lines.append("**Statements**, cited and not computed: "
                         + ", ".join(st["clause"] for st in statements))
    elif statements and not selected:
        lines.append("")
        lines.append("**Policy statements** — cited, not computed")
        for st in statements:
            lines.append(f"  **{st['clause']}** — {st.get('text', '')}")

    lines.append("")
    lines.append("**Not done:** no recommendation, no target weight, no instrument to "
                 "trade. Which instruments meet a condition is outside this document "
                 "(IPS-5.2).")
    if selected:
        left_out = []
        if subjects:
            left_out.append("the other holdings, the asset-class and sector clauses")
        if status is not None:
            left_out.append("the figures of the findings within their limits")
        left_out.append("the policy statements' text")
        lines.append(f"**Not shown:** {', '.join(left_out)}. Ask about the portfolio "
                     "for the full check.")
    return lines


def _format_out_of_scope_response() -> List[str]:
    """Out-of-scope request: nothing ran, so there is nothing to format."""
    return list(OUT_OF_SCOPE_RESPONSE)


def _format_optimization_response(sub_results: Dict) -> List[str]:
    """Format optimization results."""
    lines = ["📊 **PORTFOLIO OPTIMIZATION RESULTS**", ""]
    
    opt = sub_results.get("OptimizationAgent", {})
    if not opt.get("success"):
        lines.append("⚠️ Optimization failed")
        return lines
    
    # ✅ TRUST THE CONTRACT: 
    # We validated in optimization_agent_node that 'optimal_weights' exists 
    # and contains only floats. No string parsing needed here.
    weights = opt.get("optimal_weights", {})
    
    if weights:
        lines.append("**Optimal Allocation:**")
        # Sort by weight value (guaranteed float)
        for ticker, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            # Format float to percentage string
            lines.append(f"  • {ticker}: {weight*100:.1f}%")
    
    lines.append("")
    lines.append("**Expected Metrics:**")
    
    # ✅ TRUST THE CONTRACT: Metrics are guaranteed floats
    ret = opt.get('expected_return', 0.0)
    vol = opt.get('expected_volatility', 0.0)
    sharpe = opt.get('sharpe_ratio', 0.0)
    
    lines.append(f"  • Return: {ret*100:.2f}%")
    lines.append(f"  • Volatility: {vol*100:.2f}%")
    lines.append(f"  • Sharpe Ratio: {sharpe:.2f}")
    
    return lines


def _format_macro_response(sub_results: Dict) -> List[str]:
    """Format macro analysis results."""
    lines = ["🌍 **MACRO ENVIRONMENT ANALYSIS**", ""]
    
    macro = sub_results.get("MacroAgent", {})
    if macro.get("success"):
        snapshot = macro.get("snapshot", {})
        regime = macro.get("regime", {})
        
        vix = snapshot.get("vix", {})
        yc = snapshot.get("yield_curve", {})
        
        lines.append(f"**Market Regime:** {regime.get('regime', 'N/A')}")
        lines.append(f"**Risk Stance:** {regime.get('risk_stance', 'N/A')}")
        lines.append("")
        lines.append("**Indicators:**")
        lines.append(f"  • VIX: {vix.get('value', 'N/A')} ({vix.get('regime', 'N/A')})")
        lines.append(f"  • Yield Curve: {yc.get('status', 'N/A')} (slope: {yc.get('slope', 'N/A')})")
        
    
    return lines


def _format_rebalance_response(sub_results: Dict) -> List[str]:
    """Format rebalancing results."""
    lines = ["⚖️ **REBALANCING ANALYSIS**", ""]
    
    rebal = sub_results.get("RebalanceAgent", {})
    if rebal.get("success"):
        decision = rebal.get("decision", {})
        trades = rebal.get("trades", [])
        
        lines.append(f"**Recommendation:** {decision.get('recommendation', 'N/A').upper()}")
        lines.append(f"**Max Drift:** {decision.get('max_drift', 0):.1%}")
        
        if trades:
            lines.append("")
            lines.append("**Proposed Trades:**")
            for trade in trades[:5]:
                lines.append(
                    f"  • {trade['action']} {trade['shares']:.0f} {trade['ticker']} "
                    f"(~€{trade.get('value', 0):,.0f})"
                )
            
            lines.append("")
            lines.append(f"**Est. Transaction Cost:** €{rebal.get('total_cost', 0):.2f}")
    
    return lines


def _format_backtest_response(sub_results: Dict) -> List[str]:
    """Format backtest results."""
    lines = ["📈 **BACKTEST RESULTS**", ""]
    
    bt = sub_results.get("BacktestAgent", {})
    if bt.get("success"):
        # Handle flat vs nested metrics structure
        backtest_metrics = bt.get("backtest_metrics", {})
        metrics = backtest_metrics if backtest_metrics else bt
        
        # Use metrics dictionary for values, fallback to bt for top-level keys
        lines.append(f"**Period:** {bt.get('period', metrics.get('start_date', 'N/A'))}")
        lines.append("")
        lines.append("**Performance:**")

        # Helper to format safely (handles both float and string inputs)
        def fmt(val, is_pct=True):
            if isinstance(val, (int, float)):
                return f"{val:.1%}" if is_pct else f"{val:.2f}"
            return str(val)

        lines.append(f"  • Total Return: {fmt(metrics.get('total_return', 0))}")
        lines.append(f"  • CAGR: {fmt(metrics.get('cagr', 0))}")
        lines.append(f"  • Volatility: {fmt(metrics.get('volatility', 0))}")
        lines.append(f"  • Sharpe Ratio: {fmt(metrics.get('sharpe_ratio', 0), is_pct=False)}")
        lines.append("")
        lines.append("**Risk:**")
        lines.append(f"  • Max Drawdown: {fmt(metrics.get('max_drawdown', 0))}")
        lines.append(f"  • Drawdown Date: {metrics.get('max_drawdown_date', 'N/A')}")
        lines.append("")
        lines.append("⚠️ Past performance does not guarantee future results.")
    
    return lines


def _format_analysis_response(decision: Dict, sub_results: Dict) -> List[str]:
    """Select which of PortfolioAnalysisAgent's figures the question asked for.

    The agent computes every figure; the router's `measure` says which one the
    user wanted. Dispatching on anything else - `tickers` being non-empty, the
    intent, the task description - was tried on paper and fails: the router
    fills `tickers` from the portfolio on every allocation query (rule 2), the
    intent is `data_fetch` for all of them, and the task description is free
    text nothing can assert on.

    A plan naming the agent with no measure is a router error and raises
    rather than picking a formatter, because whichever one it picked would
    answer a question the user did not ask with figures that look right.
    """
    parameters = decision.get("parameters") or {}
    measure = parameters.get("measure")

    if measure == "allocation":
        return _format_allocation_response(sub_results, parameters.get("group_by"))
    if measure == "position_pnl":
        return _format_pnl_response(sub_results, parameters.get("tickers") or [])
    if measure == "portfolio_volatility":
        return _format_portfolio_volatility_response(sub_results)
    raise ValueError(
        f"PortfolioAnalysisAgent ran but the router set measure={measure!r}. "
        "Nothing to select; see ExtractedParameters.measure."
    )


def _format_allocation_response(sub_results: Dict, group_by: Optional[str] = None) -> List[str]:
    """Format the allocation PortfolioAnalysisAgent computed.

    Formats only. Every figure is read from the agent's result unchanged; the
    only arithmetic is rendering a stored fraction as a percentage.

    The as-of date is read, not derived. PortfolioAnalysisAgent reduces the
    per-holding dates to a worst case and publishes it; computing it here would
    put the figure only in the answer text, where the runner cannot assert on
    it. Whether those dates agree is read too, for the same reason - the one
    branch below selects wording, it does not compare dates.

    `group_by` narrows the rendering, not the computation: all three views
    are always computed and published, and the one the user named is the one
    printed. With no `group_by` all three are printed. The position view is
    Part 7's IPS-4.1 table, largest first, so "what is my biggest position"
    is its first line.
    """
    analysis = sub_results.get("PortfolioAnalysisAgent", {})
    if not analysis.get("success"):
        return ["Allocation could not be computed.",
                f"  {analysis.get('error', 'No error recorded.')}"]

    allocation = analysis.get("allocation") or {}
    by_class = allocation.get("by_asset_class") if group_by in (None, "asset_class") else None
    by_sector = allocation.get("by_sector") if group_by in (None, "sector") else None
    by_position = allocation.get("by_position") if group_by in (None, "position") else None
    by_class = by_class or {}
    by_sector = by_sector or {}
    by_position = by_position or {}

    lines = ["**PORTFOLIO ALLOCATION**", ""]

    as_of = allocation.get("as_of") or {}
    if as_of.get("worst_case"):
        if as_of.get("uniform"):
            lines.append(f"**Priced as of {as_of['worst_case']}** — the close "
                         f"for every holding.")
        else:
            lines.append(f"**Priced as of {as_of['worst_case']}** — the oldest "
                         f"close among the holdings ({as_of.get('stalest')}). "
                         f"No figure below is fresher than that.")
        lines.append("")

    if by_class:
        lines.append(f"**Total portfolio value:** {by_class['total_value']:,.2f}")
        lines.append(f"  invested {by_class['invested_value']:,.2f} "
                     f"+ cash {by_class['cash_balance']:,.2f}")
        lines.append("")
        # Each header names the denominator by the share field's own word
        # and gives its amount from the block; no label travels in the data.
        lines.append(f"**By asset class**, % of total portfolio value "
                     f"{by_class['total_value']:,.2f}, cash included:")
        for line in by_class.get("lines", []):
            pct = line.get("pct_of_total")
            pct_str = f"{pct:.2%}" if pct is not None else "n/a"
            lines.append(f"  - {line['label']:<13}{pct_str:>8}"
                         f"{line['market_value']:>15,.2f}")

    if by_sector:
        if by_class:
            lines.append("")
        # Three shares per line, each read from the block: of sectored value,
        # of invested value (Part 3), and of total portfolio value including
        # cash (Part 7, the IPS-4.3 figure and the answer to "what share of
        # my portfolio"). Every amount is the sector block's own, so the
        # columns are labelled when the asset-class block is not rendered.
        lines.append(f"**By sector**, % of sectored value {by_sector['sectored_value']:,.2f}, "
                     f"of invested value {by_sector['invested_value']:,.2f}, "
                     f"and of total portfolio value {by_sector['total_value']:,.2f}:")
        for line in by_sector.get("lines", []):
            of_sectored = line.get("pct_of_sectored")
            of_invested = line.get("pct_of_invested")
            of_total = line.get("pct_of_total")
            sectored_str = f"{of_sectored:.2%}" if of_sectored is not None else "n/a"
            invested_str = f"{of_invested:.2%}" if of_invested is not None else "n/a"
            total_str = f"{of_total:.2%}" if of_total is not None else "n/a"
            held = ", ".join(line.get("tickers", []))
            lines.append(f"  - {line['label']:<13}{sectored_str:>8}{invested_str:>9}"
                         f"{total_str:>9}{line['market_value']:>15,.2f}   {held}")

    if by_position:
        if by_class or by_sector:
            lines.append("")
        # One line per holding, largest first as published; two shares, of
        # total portfolio value (the IPS-4.1 figure) and of invested value.
        lines.append(f"**By position**, largest first, % of total portfolio value "
                     f"{by_position['total_value']:,.2f} and of invested value "
                     f"{by_position['invested_value']:,.2f}:")
        for line in by_position.get("lines", []):
            of_total = line.get("pct_of_total")
            of_invested = line.get("pct_of_invested")
            total_str = f"{of_total:.2%}" if of_total is not None else "n/a"
            invested_str = f"{of_invested:.2%}" if of_invested is not None else "n/a"
            lines.append(f"  - {line['label']:<13}{total_str:>8}{invested_str:>9}"
                         f"{line['market_value']:>15,.2f}")

    lines.append("")
    if group_by is None:
        lines.append("**Not done.** The question named no breakdown, so all three are")
        lines.append("shown. Fund holdings are counted at fund level; there is no")
        lines.append("look-through.")
    else:
        lines.append("**Not done.** Fund holdings are counted at fund level; there")
        lines.append("is no look-through.")
    return lines


def _format_pnl_response(sub_results: Dict, tickers: List[str]) -> List[str]:
    """Format the position P&L PortfolioAnalysisAgent computed.

    Formats only; every figure is read from the agent's result. `tickers`
    selects which positions to print - empty means all of them, since the
    router leaves it empty when the user named none. A requested ticker that
    is not held is said so, not dropped: dropping it would answer a question
    about a position the portfolio does not contain with figures about others.

    One holding, one close, so the as-of date is per position and printed
    beside it rather than reduced. Price return only, per expected_values.md
    D4, and the answer says so because on five of the nine holdings it
    understates the return.
    """
    analysis = sub_results.get("PortfolioAnalysisAgent", {})
    if not analysis.get("success"):
        return ["Position P&L could not be computed.",
                f"  {analysis.get('error', 'No error recorded.')}"]

    pnl = analysis.get("position_pnl") or {}
    if not pnl:
        return ["No position P&L was published for this request."]

    wanted = [t.upper() for t in tickers] or sorted(pnl)
    not_held = [t for t in wanted if t not in pnl]
    shown = [t for t in wanted if t in pnl]

    lines = ["**POSITION P&L SINCE PURCHASE**", ""]
    for t in not_held:
        lines.append(f"**{t} is not held in this portfolio.**")
    if not_held:
        lines.append("")

    for t in shown:
        p = pnl[t]
        sign = "+" if p["pnl_abs"] >= 0 else "-"
        lines.append(f"**{t}** — {sign}{abs(p['pnl_abs']):,.2f} ({p['pnl_pct']:+.2%}) "
                     f"since {p.get('purchase_date') or 'an unrecorded purchase date'}")
        lines.append(f"  {p['quantity']:,.0f} shares, cost {p['cost_basis']:,.2f} "
                     f"at {p['average_price']:,.2f} average")
        lines.append(f"  now {p['market_value']:,.2f} at {p['price']:,.2f}, "
                     f"priced as of {p['as_of']}")
        lines.append("")

    lines.append("**Not done.** Price return only: dividends are not attributed to")
    lines.append("the portfolio, so income is not included (expected_values.md D4).")
    return lines



def _format_risk_response(sub_results: Dict) -> List[str]:
    """Format the risk figures DataAgent produced.

    Per holding only. Portfolio-level volatility needs the holding weights
    against the covariance matrix and does not exist yet (expected_values.md
    D7). Benchmark 1.3 asks for exactly that, so this names the gap rather than
    letting nine per-holding numbers stand in for the one number asked for.

    The window comes from `prices["period"]`, which is the range actually
    returned, not the router's requested period. The router emits null when the
    user names no timeframe and the window is then resolved from config two
    files away, so the requested value is absent exactly when the reader most
    needs to be told what was measured.
    """
    data = sub_results.get("DataAgent", {})
    if not data.get("success"):
        return ["Risk figures could not be loaded.",
                f"  {data.get('error', 'No error recorded.')}"]

    vols = (data.get("covariance") or {}).get("annualized_volatilities_raw") or {}
    if not vols:
        return ["No volatilities were computed for this request."]

    prices = data.get("prices") or {}
    window = prices.get("period")
    observations = prices.get("num_observations")

    lines = ["**RISK**", ""]
    if window:
        basis = f"**Annualised volatility per holding**, {window}"
        if observations:
            basis = f"{basis}, {observations} closes"
        lines.append(f"{basis}:")
    else:
        lines.append("**Annualised volatility per holding**, window not reported:")
    for ticker, vol in sorted(vols.items(), key=lambda kv: -kv[1]):
        lines.append(f"  - {ticker:<6}{vol:>8.2%}")

    lines.append("")
    lines.append("**Not done.** These are per holding. The portfolio's own volatility")
    lines.append("is a different number - weights against the covariance matrix -")
    lines.append("and is answered when the question asks for it. No as-of date is")
    lines.append("attached to the per-holding figures (benchmark 3.3).")
    return lines


def _format_portfolio_volatility_response(sub_results: Dict) -> List[str]:
    """Format the portfolio volatility PortfolioAnalysisAgent computed.

    Formats only. Benchmark 1.3 passes on the basis being traceable, so every
    element of the basis is printed from the published summary: method,
    window, observation count, weights basis and their pricing date, and the
    annualisation factor. Nothing here is derived; a basis the synthesizer
    computed would exist only as text.
    """
    analysis = sub_results.get("PortfolioAnalysisAgent", {})
    if not analysis.get("success"):
        return ["Portfolio volatility could not be computed.",
                f"  {analysis.get('error', 'No error recorded.')}"]

    pv = analysis.get("portfolio_volatility") or {}
    if not pv:
        return ["No portfolio volatility was published for this request."]

    window = pv.get("window") or {}
    lines = ["**PORTFOLIO VOLATILITY**", ""]
    lines.append(f"**{pv['annualised']:.2%} annualised**")
    lines.append("")
    lines.append("**Basis:**")
    lines.append(f"  - Method: sqrt(w'Σw) on a {pv.get('covariance_method') or 'unstated'} "
                 f"covariance matrix of daily returns")
    lines.append(f"  - Window: {window.get('start')} to {window.get('end')}, "
                 f"{window.get('closes')} closes")
    lines.append(f"  - Weights: {pv.get('weights_basis')}, priced as of "
                 f"{pv.get('weights_as_of')}")
    lines.append(f"  - Annualisation: x sqrt({pv.get('annualisation')})")
    lines.append("")
    lines.append("**Not done.** Cash is excluded from the weights, so this is the")
    lines.append("volatility of the invested assets rather than of the total")
    lines.append("portfolio. It is one window under one regime; it is not an")
    lines.append("average of the per-holding volatilities.")
    return lines



# =============================================================================
# HELPER CLASS FOR TRACING
# =============================================================================

class AgentTraceHelper:
    """Helper to work with existing tracer when inside a request context."""
    
    def __init__(self, tracer, request_id: str, agent_name: str):
        self.tracer = tracer
        self.request_id = request_id
        self.agent_name = agent_name
        self._entered = False
    
    def __enter__(self):
        from observability.tracer import AgentTrace
        self._trace = AgentTrace(self.tracer, self.request_id, self.agent_name)
        self._trace.__enter__()
        self._entered = True
        return self._trace
    
    def __exit__(self, *args):
        if self._entered:
            self._trace.__exit__(*args)
    
    def log_thinking(self, thought: str):
        if self._entered:
            self._trace.log_thinking(thought)