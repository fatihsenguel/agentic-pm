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

from .state import (
    AgentState,
    set_router_decision,
    mark_agent_complete,
    add_shared_data,
    add_error,
    add_warning,
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
    
    # Check cache first
    cached_holdings = state.get("portfolio_holdings")
    if cached_holdings:
        tickers = [h["ticker"] for h in cached_holdings]
        return PortfolioContext(
            tickers=tickers,
            holdings=cached_holdings,
            cash_balance=cash_balance,
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
            "purchase_date": (
                h["purchase_date"].isoformat() if h.get("purchase_date") else None
            ),
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
    request_ctx = None
    agent_ctx = None
    
    try:
        # Start tracing
        if tracer:
            request_ctx = tracer.trace_request(
                request_id=state.get("request_id"),
                user_input=get_user_message(state)[:100]
            )
            request_ctx.__enter__()
            agent_ctx = request_ctx.trace_agent("Router")
            agent_ctx.__enter__()
        
        # Get user message
        user_message = get_user_message(state)
        
        if not user_message:
            return add_error(state, "No user message found")
        
        # Call Smart Router
        router = get_router()
        portfolio_id = state.get("portfolio_id")
        decision, validation = await router.route(user_message, portfolio_id=portfolio_id)
        
        # Log validation issues
        for error in validation.errors:
            add_warning(state, f"Validation: {error}")
        
        # Check if clarification needed
        if decision.intent == "clarification_needed":
            return {
                **set_final_response(state, decision.clarification_question or "Could you please clarify your request?"),
                "router_decision": _decision_to_dict(decision),
            }
        
        # Set router decision and initialize execution
        return set_router_decision(state, _decision_to_dict(decision))
        
    except Exception as e:
        return add_error(state, f"Router error: {str(e)}")
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)
        if request_ctx:
            request_ctx.__exit__(None, None, None)


def _decision_to_dict(decision) -> Dict[str, Any]:
    """Convert RouterDecision to dict for state storage."""
    return {
        "intent": decision.intent if isinstance(decision.intent, str) else decision.intent.value,
        "confidence": decision.confidence,
        "agents_needed": [
            {
                "agent": t.agent if isinstance(t.agent, str) else t.agent.value,
                "task_description": t.task_description,
                "priority": t.priority,
            }
            for t in decision.agents_needed
        ],
        # Every extracted field, from the schema. A hand-picked key list here
        # was a second statement of ExtractedParameters and dropped any field
        # it did not name - a router output that validated and then vanished
        # before any node could read it.
        "parameters": decision.parameters.model_dump(),
        "execution_order": decision.execution_order,
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
        
        # Get period from router decision
        router_decision = state.get("router_decision") or {}
        parameters = router_decision.get("parameters", {})
        period = parameters.get("period", "3Y")
        
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
                "as_of_dates": price_result.get("as_of_dates", {}),
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

    Reference: expected_values.md Parts 1-4, decisions D1-D8.
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

        from portfolio_tool.quant.allocation import (
            allocation_by_asset_class,
            allocation_by_sector,
            position_pnl,
        )

        by_class = allocation_by_asset_class(holdings, prices, cash_balance)
        by_sector = allocation_by_sector(holdings, prices)
        pnl = position_pnl(holdings, prices)

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
                    "pct_of_denominator": line.pct_of_denominator,
                    "pct_of_invested": line.pct_of_invested,
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

        position_pnl_summary = {
            t: {
                "quantity": p.quantity,
                "average_price": p.average_price,
                "price": p.price,
                "cost_basis": round(p.cost_basis, 2),
                "market_value": round(p.market_value, 2),
                "pnl_abs": round(p.pnl_abs, 2),
                "pnl_pct": p.pnl_pct,
                "purchase_date": p.purchase_date,
                "as_of": as_of_dates[t],
            }
            for t, p in pnl.items()
        }

        allocation_summary = {
            "by_asset_class": {
                "lines": _lines(by_class),
                "denominator": by_class.denominator_label,
                "invested_value": round(by_class.invested_value, 2),
                "cash_balance": round(by_class.cash_balance, 2),
                "total_value": round(by_class.total_value, 2),
            },
            "by_sector": {
                "lines": _lines(by_sector),
                "denominator": by_sector.denominator_label,
                "invested_value": round(by_sector.invested_value, 2),
                "sectored_value": round(by_sector.total_value, 2),
            },
            "as_of": {
                "worst_case": as_of_dates[stalest],
                "stalest": stalest,
                "uniform": uniform,
            },
        }

        print(f"  Total portfolio value: {by_class.total_value:,.2f}")
        for line in by_class.lines:
            print(f"    {line.label:<16} {line.pct_of_denominator:>7.2%}")
        print(f"  Position P&L computed for {len(pnl)} positions")
        print(f"  Portfolio volatility: {vol:.4%} over {window['closes']} closes")

        result = {
            "success": True,
            "agent_name": "PortfolioAnalysisAgent",
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
        elif intent == "combined":
            # Combined: show all relevant results
            if "MacroAgent" in sub_results:
                lines.extend(_format_macro_response(sub_results))
                lines.append("")
            if "RebalanceAgent" in sub_results:
                lines.extend(_format_rebalance_response(sub_results))
            if "OptimizationAgent" in sub_results:
                lines.extend(_format_optimization_response(sub_results))
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
        
        # TAA signal if available
        taa = rebal.get("taa_signal")
        if taa:
            lines.append("")
            lines.append(f"**Tactical Signal:** {taa.get('regime', 'N/A')} regime")
    
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

    `group_by` narrows the rendering, not the computation: both breakdowns are
    always computed and published, and the one the user named is the one
    printed. With no `group_by` both are printed.
    """
    analysis = sub_results.get("PortfolioAnalysisAgent", {})
    if not analysis.get("success"):
        return ["Allocation could not be computed.",
                f"  {analysis.get('error', 'No error recorded.')}"]

    allocation = analysis.get("allocation") or {}
    by_class = allocation.get("by_asset_class") if group_by in (None, "asset_class") else None
    by_sector = allocation.get("by_sector") if group_by in (None, "sector") else None
    by_class = by_class or {}
    by_sector = by_sector or {}

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
        lines.append(f"**By asset class**, % of {by_class['denominator']}:")
        for line in by_class.get("lines", []):
            pct = line.get("pct_of_denominator")
            pct_str = f"{pct:.2%}" if pct is not None else "n/a"
            lines.append(f"  - {line['label']:<13}{pct_str:>8}"
                         f"{line['market_value']:>15,.2f}")

    if by_sector:
        if by_class:
            lines.append("")
        lines.append(f"**By sector**, % of {by_sector['denominator']} "
                     f"and of invested value {by_sector['invested_value']:,.2f}:")
        for line in by_sector.get("lines", []):
            of_sectored = line.get("pct_of_denominator")
            of_invested = line.get("pct_of_invested")
            sectored_str = f"{of_sectored:.2%}" if of_sectored is not None else "n/a"
            invested_str = f"{of_invested:.2%}" if of_invested is not None else "n/a"
            held = ", ".join(line.get("tickers", []))
            lines.append(f"  - {line['label']:<13}{sectored_str:>8}{invested_str:>9}"
                         f"{line['market_value']:>15,.2f}   {held}")

    lines.append("")
    if group_by is None:
        lines.append("**Not done.** The question named no breakdown, so both are")
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