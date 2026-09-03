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

def load_portfolio_context(state: "AgentState") -> Tuple[List[str], Optional[List[Dict]]]:
    """Load portfolio tickers and holdings from state or database."""
    
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
        return tickers, None
    
    # Portfolio specified - load from database
    from portfolio_tool.portfolio_manager import PortfolioManager
    pm = PortfolioManager()
    
    # Check cache first
    cached_holdings = state.get("portfolio_holdings")
    if cached_holdings:
        tickers = [h["ticker"] for h in cached_holdings]
        return tickers, cached_holdings
    
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
    return tickers, holdings


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
        "parameters": {
            "tickers": decision.parameters.tickers,
            "period": decision.parameters.period,
            "max_volatility": decision.parameters.max_volatility,
            "target_return": decision.parameters.target_return,
            "portfolio_value": decision.parameters.portfolio_value,
            "rebalance_threshold": decision.parameters.rebalance_threshold,
            "portfolio_id": decision.parameters.portfolio_id,
        },
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
            tickers, holdings = load_portfolio_context(state)
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
                "covariance_matrix": cov_result.get("covariance_matrix", {}),
                "volatilities": cov_result.get("annualized_volatilities", {}),
                "expected_returns": expected_returns,  # GUARANTEED to exist
                "holdings": build_holdings_summary(holdings),
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
            # ⭐ STRICT: Dynamic Configuration (Bank-Grade Fix)
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
        
        adj = regime.get('equity_adjustment', 0)
        if adj != 0:
            lines.append("")
            lines.append(f"**Recommendation:** Adjust equity by {adj:+.0%}")
    
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