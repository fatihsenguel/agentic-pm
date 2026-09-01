# src/agents/nodes.py
# Purpose: LangGraph node functions for each agent
# Principle: Nodes are thin wrappers that call agent logic and update state
# Phase: 6.2 - LangGraph State Machine
# PATCHED: Phase 6.5 - Fixed data_agent_node to handle data_management intent
# 
# PRODUCTION STANDARDS:
# - NO fallback data (fail fast with clear errors)
# - NO guessing or defaults for financial data
# - NO silent failures
# - Clear error messages with actionable solutions

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.config import config
import logging
logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional, Literal, List, Tuple
from langchain_core.messages import AIMessage, HumanMessage

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.data_tools import (
    fetch_stock_prices, 
    list_tracked_assets, 
    get_asset_info, 
    fetch_fundamentals,
    fetch_financial_statements,
    fetch_earnings_history,
    get_latest_price,
    query_financial_data,
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.portfolio_manager import PortfolioManager

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.portfolio_tools import (
    list_portfolios,
    get_portfolio_details,
    get_portfolio_holdings,
    get_portfolio_summary,
    create_portfolio,
    add_holding_to_portfolio,
    update_portfolio_holding,
    remove_holding_from_portfolio,
    delete_portfolio,
    find_portfolio_by_name,
)

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.compliance_agent import ComplianceAgent
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.decision_schemas import ComplianceStatus, ComplianceReport

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.schemas import AgentResponse, QueryIntent
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

# NEW: Decision engine imports
from .decision_engine import (
    run_decision_assessment,
    should_generate_decision_summary,
    extract_macro_regime_from_results,
    extract_vix_from_results
)
from .decision_schemas import DecisionType, RiskStatus


# Import observability
try:
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.observability import get_tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    def get_tracer():
        return None


# Colors for Debugging
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GREEN = "\033[92m"
RESET = "\033[0m"

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
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.portfolio_manager import PortfolioManager
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


def load_portfolio_context_optional(state: "AgentState") -> Tuple[List[str], Optional[List[Dict]]]:
    """
    Load portfolio tickers - returns empty list if none found (for admin operations).
    Unlike load_portfolio_context(), this doesn't raise an error if no tickers.
    """
    portfolio_id = state.get("portfolio_id")
    router_decision = state.get("router_decision") or {}
    parameters = router_decision.get("parameters", {})
    tickers = parameters.get("tickers", [])
    
    if portfolio_id:
        try:
            pm = PortfolioManager()
            holdings = pm.get_holdings(portfolio_id)
            if holdings:
                return [h["ticker"] for h in holdings], holdings
        except Exception as e:
            logger.warning(f"Could not load portfolio {portfolio_id}: {e}")
    
    return tickers, None


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


def cache_portfolio_holdings(state: "AgentState", holdings: List[Dict]) -> None:
    """
    Cache portfolio holdings in state to avoid repeated DB calls.
    
    Args:
        state: Current agent state
        holdings: Holdings loaded from portfolio manager
    """
    if holdings:
        state["portfolio_holdings"] = holdings
        logger.debug(f"Cached {len(holdings)} holdings in state")


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
    """Router node - determines which agents to call and in what order."""
    from .smart_router import get_router
    from langchain_core.messages import HumanMessage, AIMessage
    
    tracer = get_tracer()
    request_ctx = None
    agent_ctx = None

    print(f"\n{CYAN}🐛 [DEBUG] Router Node Started{RESET}")

    try:
        # ✅ ROBUST TRACING START
        if tracer:
            try:
                user_msg = get_user_message(state) or "unknown"
                request_ctx = tracer.trace_request(user_input=user_msg[:100])
                request_ctx.__enter__()
                agent_ctx = request_ctx.trace_agent("Router")
                agent_ctx.__enter__()
            except Exception as e:
                logger.warning(f"Tracing failed in Router (ignoring): {e}")

        # 1. Get user message
        user_message = get_user_message(state)
        if not user_message:
            return {
                **set_final_response(state, {
                    "success": False,
                    "agent_name": "Router",
                    "error": "No user message found in state"
                }),
            }
        
        print(f"  Message: {user_message[:80]}...")
        
        # 2. Build conversation history from messages
        messages = state.get("messages", [])
        conversation_history = []
        for msg in messages[:-1]:  # Exclude the current message
            if hasattr(msg, 'content'):
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                conversation_history.append({"role": role, "content": msg.content})
            elif isinstance(msg, dict):
                conversation_history.append(msg)
        
        # 3. Get portfolio ID for context
        portfolio_id = state.get("portfolio_id")
        
        # 4. Call router
        router = get_router()
        decision, validation = await router.route(
            user_message=user_message,
            conversation_history=conversation_history,
            portfolio_id=portfolio_id
        )
        
        if not decision:
            return {
                **set_final_response(state, {
                    "success": False,
                    "agent_name": "Router",
                    "error": f"Router failed: {validation.errors}"
                }),
            }
        
        print(f"  Query Intent: {decision.query_intent}")
        print(f"  Execution Intent: {decision.execution_intent}")
        print(f"  Agents: {decision.execution_order}")
        print(f"  Parameters: {decision.parameters}")
        
        # 5. Handle clarification needed
        intent_value = decision.intent.value if hasattr(decision.intent, 'value') else decision.intent
        if intent_value == "clarification_needed":
            return {
                **set_router_decision(state, _decision_to_dict(decision)),
                **set_final_response(state, {
                    "success": True,
                    "agent_name": "Router",
                    "data": {
                        "summary": decision.clarification_question,
                        "details": {"intent": "clarification_needed"}
                    }
                }),
            }
        
        # 6. Store decision and continue
        return set_router_decision(state, _decision_to_dict(decision))
    
    except Exception as e:
        import traceback
        logger.error(f"Router error:\n{traceback.format_exc()}")
        return {
            **set_final_response(state, {
                "success": False,
                "agent_name": "Router",
                "error": f"Router exception: {str(e)}"
            }),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


def _decision_to_dict(decision) -> Dict[str, Any]:
    """Convert RouterDecision to dict for state storage."""
    return {
        "query_intent": decision.query_intent.value if hasattr(decision.query_intent, 'value') else decision.query_intent,  # ADD THIS
        "execution_intent": decision.execution_intent.value if hasattr(decision.execution_intent, 'value') else decision.execution_intent,  # ADD THIS
        "intent": decision.intent if isinstance(decision.intent, str) else decision.intent.value,  # Keep for backward compat
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
            "command": decision.parameters.command,
            # ⭐ NEW FIELDS
            "report_type": getattr(decision.parameters, 'report_type', None),
            "data_type": getattr(decision.parameters, 'data_type', None),
            "limit": getattr(decision.parameters, 'limit', 30),
            "portfolio_name": getattr(decision.parameters, 'portfolio_name', None),
            "quantity": getattr(decision.parameters, 'quantity', None),
            "price": getattr(decision.parameters, 'price', None),
        },
        "execution_plan": decision.execution_plan,
        "execution_order": decision.execution_order,
    }


# =============================================================================
# DATA AGENT NODE - STRICT MODE (PATCHED FOR PHASE 6.5)
# =============================================================================

async def data_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Data Agent node - handles both:
    1. Data fetching for analysis (optimization, rebalancing, etc.)
    2. Admin/data management operations (list assets, update DB, etc.)
    
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
        logger.warning(f"Tracing failed in DataAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print("DATA AGENT - Processing Request")
        print("="*80)
        
        # ⭐ CRITICAL: Check intent to determine which handler to use
        router_decision = state.get("router_decision") or {}
        intent = router_decision.get("intent", "data_fetch")
        parameters = router_decision.get("parameters", {})
        
        print(f"  Intent: {intent}")
        print(f"  Parameters: {parameters}")
        
        # =================================================================
        # BRANCH 1: DATA MANAGEMENT (Admin Operations)
        # =================================================================
        if intent == "data_management":
            return await _handle_data_management_node(state, parameters)
        
        if intent in ("portfolio_management", "portfolio_mgmt"):
            return await _handle_portfolio_management_node(state, parameters)

        # =================================================================
        # BRANCH 2: DATA FETCH (For Analysis - Optimization, Rebalancing, etc.)
        # =================================================================
        return await _handle_data_fetch_node(state, parameters)
    
    except (PortfolioContextError, DataCalculationError, RuntimeError) as e:
        logger.error(f"DataAgent error: {e}")
        return {
            **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"DataAgent: {str(e)}"),
        }
    
    except Exception as e:
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


async def _handle_data_management_node(state: AgentState, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle admin/data management operations.
    
    Commands:
    - list_assets: Show all tracked assets
    - update_prices / fetch_prices: Refresh price data
    - get_info: Get detailed info for a ticker
    - fetch_fundamentals: Get fundamental data
    """
    command = parameters.get("command", "list_assets")
    tickers = parameters.get("tickers", [])
    portfolio_id = parameters.get("portfolio_id")
    
    print(f"  {GREEN}[Admin Mode]{RESET} Command: {command}")
    
    result_data = {}
    
    try:
        # =====================================================================
        # COMMAND: list_assets
        # =====================================================================
        if command == "list_assets":
            # list_tracked_assets takes no arguments - call directly
            tool_result = list_tracked_assets.func()
            
            if tool_result.get("success"):
                assets = tool_result.get("data", [])
                result_data = {
                    "success": True,
                    "message": f"Found {len(assets)} tracked assets in the database.",
                    "assets": assets,
                    "count": len(assets)
                }
            else:
                result_data = {
                    "success": False,
                    "error": tool_result.get("error", "Failed to list assets")
                }
        
        # =====================================================================
        # COMMAND: get_info
        # =====================================================================
        elif command == "get_info":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for get_info command."
                }
            else:
                # For single-ticker commands, prefer the LAST ticker (user-specified)
                # Router puts portfolio tickers first, user tickers last
                ticker = tickers[-1] if len(tickers) > 1 else tickers[0]
                tool_result = get_asset_info.invoke(ticker)
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Retrieved info for {ticker}.",
                        "asset_info": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to get info for {ticker}")
                    }
        
        # =====================================================================
        # COMMAND: update_prices / fetch_prices
        # =====================================================================
        elif command in ["update_prices", "fetch_prices"]:
            # If no tickers provided, try to get from portfolio
            if not tickers and portfolio_id:
                tickers, _ = load_portfolio_context_optional(state)
            
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No tickers specified for price update. Provide tickers or portfolio_id."
                }
            else:
                ticker_str = ",".join(tickers)
                print(f"  Updating prices for: {ticker_str}")
                
                tool_result = fetch_stock_prices.invoke({"ticker": ticker_str})
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Successfully updated prices for {len(tickers)} ticker(s): {ticker_str}",
                        "tickers_updated": tickers,
                        "details": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to update prices for {ticker_str}")
                    }
        
        # =====================================================================
        # COMMAND: fetch_fundamentals
        # =====================================================================
        elif command == "fetch_fundamentals":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for fetch_fundamentals command."
                }
            else:
                ticker = tickers[0]
                print(f"  Fetching fundamentals for: {ticker}")
                
                tool_result = fetch_fundamentals.invoke(ticker)
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Successfully fetched fundamentals for {ticker}.",
                        "fundamentals": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to fetch fundamentals for {ticker}")
                    }
        # =====================================================================
        # COMMAND: fetch_financial_statements (NEW)
        # =====================================================================
        elif command == "fetch_financial_statements":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for fetch_financial_statements command."
                }
            else:
                ticker = tickers[0]
                report_type = parameters.get("report_type", "balance_sheet")
                
                # Validate report_type
                valid_types = ["balance_sheet", "income_statement", "cash_flow"]
                if report_type not in valid_types:
                    report_type = "balance_sheet"
                
                print(f"  Fetching {report_type} for: {ticker}")
                
                tool_result = fetch_financial_statements.invoke({
                    "ticker": ticker, 
                    "report_type": report_type
                })
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Successfully fetched {report_type} for {ticker}.",
                        "report_type": report_type,
                        "details": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to fetch {report_type} for {ticker}")
                    }
        
        # =====================================================================
        # COMMAND: fetch_earnings_history (NEW)
        # =====================================================================
        elif command == "fetch_earnings_history":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for fetch_earnings_history command."
                }
            else:
                ticker = tickers[0]
                print(f"  Fetching earnings history for: {ticker}")
                
                tool_result = fetch_earnings_history.invoke({"ticker": ticker})
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Successfully fetched quarterly earnings for {ticker}.",
                        "details": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to fetch earnings for {ticker}")
                    }
        
        # =====================================================================
        # COMMAND: get_latest_price (NEW)
        # =====================================================================
        elif command == "get_latest_price":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for get_latest_price command."
                }
            else:
                ticker = tickers[0]
                print(f"  Getting latest price for: {ticker}")
                
                tool_result = get_latest_price.invoke({"ticker": ticker})
                
                if tool_result.get("success"):
                    price_data = tool_result.get("data", {})
                    result_data = {
                        "success": True,
                        "message": f"Latest price for {ticker}: ${price_data.get('close', 'N/A')} (as of {price_data.get('date', 'N/A')})",
                        "price": price_data
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to get price for {ticker}")
                    }
        
        # =====================================================================
        # COMMAND: query_data (NEW)
        # =====================================================================
        elif command == "query_data":
            if not tickers:
                result_data = {
                    "success": False,
                    "error": "No ticker specified for query_data command."
                }
            else:
                ticker = tickers[0]
                data_type = parameters.get("data_type", "prices")
                limit = parameters.get("limit", 30)
                
                # Validate data_type
                valid_types = ["prices", "earnings", "statements", "fundamentals"]
                if data_type not in valid_types:
                    data_type = "prices"
                
                # Ensure limit is within bounds
                if not isinstance(limit, int) or limit < 1:
                    limit = 30
                if limit > 100:
                    limit = 100
                
                print(f"  Querying {data_type} for {ticker} (limit: {limit})")
                
                tool_result = query_financial_data.invoke({
                    "data_type": data_type,
                    "ticker": ticker,
                    "limit": limit
                })
                
                if tool_result.get("success"):
                    record_count = tool_result.get("count", 0)
                    result_data = {
                        "success": True,
                        "message": f"Retrieved {record_count} {data_type} records for {ticker}.",
                        "data_type": data_type,
                        "count": record_count,
                        "details": tool_result
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to query {data_type} for {ticker}")
                    }

        # =====================================================================
        # UNKNOWN COMMAND
        # =====================================================================
        else:
            result_data = {
                "success": False,
                "error": f"Unknown data management command: {command}. Valid commands: list_assets, update_prices, get_info, fetch_fundamentals, fetch_financial_statements, fetch_earnings_history, get_latest_price, query_data"
            }
    
    except Exception as e:
        result_data = {
            "success": False,
            "error": f"Data management error: {str(e)}"
        }
    
    # Build AgentResponse
    response = AgentResponse(
        success=result_data.get("success", False),
        agent_name="DataAgent",
        data=result_data,
        error=result_data.get("error")
    )
    
    status_icon = "✓" if result_data.get("success") else "✗"
    print(f"  {status_icon} Admin operation complete: {result_data.get('message', result_data.get('error', 'Unknown'))}")
    
    return mark_agent_complete(state, "DataAgent", response.model_dump())

async def _handle_portfolio_management_node(state: AgentState, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle portfolio management operations.
    
    Commands:
    - list_portfolios: Show all portfolios
    - get_holdings: Get holdings for a portfolio
    - get_portfolio_summary: Get portfolio value and allocation
    - create_portfolio: Create a new portfolio
    - add_holding: Add a stock to a portfolio
    - remove_holding: Remove a holding
    - delete_portfolio: Delete a portfolio
    """
    command = parameters.get("command", "list_portfolios")
    portfolio_id = parameters.get("portfolio_id")
    portfolio_name = parameters.get("portfolio_name")
    tickers = parameters.get("tickers", [])
    
    print(f"  {GREEN}[Portfolio Mode]{RESET} Command: {command}")
    
    result_data = {}
    
    try:
        # =====================================================================
        # COMMAND: list_portfolios
        # =====================================================================
        if command == "list_portfolios":
            tool_result = list_portfolios.func()
            
            if tool_result.get("success"):
                portfolios = tool_result.get("portfolios", [])
                if portfolios:
                    portfolio_list = "\n".join([
                        f"  • ID {p['id']}: {p['name']} - {p.get('description', 'No description')}"
                        for p in portfolios
                    ])
                    result_data = {
                        "success": True,
                        "message": f"Found {len(portfolios)} portfolio(s):\n{portfolio_list}",
                        "portfolios": portfolios,
                        "count": len(portfolios)
                    }
                else:
                    result_data = {
                        "success": True,
                        "message": "No portfolios found. Use 'create portfolio' to create one.",
                        "portfolios": [],
                        "count": 0
                    }
            else:
                result_data = {
                    "success": False,
                    "error": tool_result.get("error", "Failed to list portfolios")
                }
        
        # =====================================================================
        # COMMAND: get_holdings
        # =====================================================================
        elif command == "get_holdings":
            # If portfolio_name provided but not ID, search for it
            if portfolio_name and not portfolio_id:
                search_result = find_portfolio_by_name.func(portfolio_name)
                if search_result.get("success") and search_result.get("matches"):
                    matches = search_result["matches"]
                    if len(matches) == 1:
                        portfolio_id = matches[0]["id"]
                    else:
                        # Multiple matches - ask for clarification
                        match_list = "\n".join([f"  • ID {p['id']}: {p['name']}" for p in matches])
                        result_data = {
                            "success": False,
                            "error": f"Found multiple portfolios matching '{portfolio_name}':\n{match_list}\nPlease specify the portfolio ID."
                        }
                else:
                    result_data = {
                        "success": False,
                        "error": f"No portfolio found matching '{portfolio_name}'."
                    }
            
            if portfolio_id and "error" not in result_data:
                tool_result = get_portfolio_holdings.func(portfolio_id)
                
                if tool_result.get("success"):
                    holdings = tool_result.get("holdings", [])
                    portfolio_name_result = tool_result.get("portfolio_name", f"Portfolio {portfolio_id}")
                    
                    if holdings:
                        holdings_list = "\n".join([
                            f"  • {h['ticker']}: {h['quantity']} shares @ ${h['average_price']:.2f}"
                            for h in holdings
                        ])
                        result_data = {
                            "success": True,
                            "message": f"Holdings in '{portfolio_name_result}':\n{holdings_list}",
                            "holdings": holdings,
                            "tickers": tool_result.get("tickers", []),
                            "count": len(holdings)
                        }
                    else:
                        result_data = {
                            "success": True,
                            "message": f"Portfolio '{portfolio_name_result}' has no holdings yet.",
                            "holdings": [],
                            "count": 0
                        }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to get holdings for portfolio {portfolio_id}")
                    }
            elif not portfolio_id and "error" not in result_data:
                result_data = {
                    "success": False,
                    "error": "Please specify a portfolio ID or name. Use 'list portfolios' to see available portfolios."
                }
        
        # =====================================================================
        # COMMAND: get_portfolio_summary
        # =====================================================================
        elif command == "get_portfolio_summary":
            if not portfolio_id:
                result_data = {
                    "success": False,
                    "error": "Please specify a portfolio ID. Use 'list portfolios' to see available portfolios."
                }
            else:
                tool_result = get_portfolio_summary.func(portfolio_id)
                
                if tool_result.get("success"):
                    summary = tool_result.get("summary", {})
                    result_data = {
                        "success": True,
                        "message": f"Portfolio Summary:\n"
                                   f"  • Name: {summary.get('name', 'Unknown')}\n"
                                   f"  • Total Value: ${summary.get('total_value', 0):,.2f}\n"
                                   f"  • Holdings: {summary.get('holdings_count', 0)} positions",
                        "summary": summary
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to get summary for portfolio {portfolio_id}")
                    }
        
        # =====================================================================
        # COMMAND: create_portfolio
        # =====================================================================
        elif command == "create_portfolio":
            if not portfolio_name:
                result_data = {
                    "success": False,
                    "error": "Please provide a name for the new portfolio."
                }
            else:
                tool_result = create_portfolio.func(portfolio_name, "")
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": f"Portfolio '{portfolio_name}' created successfully with ID {tool_result.get('portfolio_id')}.",
                        "portfolio_id": tool_result.get("portfolio_id")
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", "Failed to create portfolio")
                    }
        
        # =====================================================================
        # COMMAND: add_holding
        # =====================================================================
        elif command == "add_holding":
            if not portfolio_id:
                result_data = {
                    "success": False,
                    "error": "Please specify a portfolio ID to add the holding to."
                }
            elif not tickers:
                result_data = {
                    "success": False,
                    "error": "Please specify a ticker symbol to add."
                }
            else:
                ticker = tickers[-1] if len(tickers) > 1 else tickers[0]  # Prefer user-specified
                quantity = parameters.get("quantity", 0)
                price = parameters.get("price", 0)
                
                if not quantity or quantity <= 0:
                    result_data = {
                        "success": False,
                        "error": "Please specify a valid quantity (number of shares)."
                    }
                elif not price or price <= 0:
                    result_data = {
                        "success": False,
                        "error": "Please specify a valid price per share."
                    }
                else:
                    tool_result = add_holding_to_portfolio.func(
                        portfolio_id=portfolio_id,
                        ticker=ticker,
                        quantity=quantity,
                        average_price=price
                    )
                    
                    if tool_result.get("success"):
                        result_data = {
                            "success": True,
                            "message": f"Added {quantity} shares of {ticker} at ${price:.2f} to portfolio {portfolio_id}.",
                            "holding_id": tool_result.get("holding_id")
                        }
                    else:
                        result_data = {
                            "success": False,
                            "error": tool_result.get("error", "Failed to add holding")
                        }
        
        # =====================================================================
        # COMMAND: delete_portfolio
        # =====================================================================
        elif command == "delete_portfolio":
            if not portfolio_id:
                result_data = {
                    "success": False,
                    "error": "Please specify a portfolio ID to delete."
                }
            else:
                tool_result = delete_portfolio.func(portfolio_id)
                
                if tool_result.get("success"):
                    result_data = {
                        "success": True,
                        "message": tool_result.get("message", f"Portfolio {portfolio_id} deleted.")
                    }
                else:
                    result_data = {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to delete portfolio {portfolio_id}")
                    }
        
        # =====================================================================
        # UNKNOWN COMMAND
        # =====================================================================
        else:
            result_data = {
                "success": False,
                "error": f"Unknown portfolio command: {command}. Valid commands: list_portfolios, get_holdings, get_portfolio_summary, create_portfolio, add_holding, delete_portfolio"
            }
    
    except Exception as e:
        result_data = {
            "success": False,
            "error": f"Portfolio management error: {str(e)}"
        }
    
    # Build AgentResponse
    response = AgentResponse(
        success=result_data.get("success", False),
        agent_name="DataAgent",
        data=result_data,
        error=result_data.get("error")
    )
    
    status_icon = "✓" if result_data.get("success") else "✗"
    print(f"  {status_icon} Portfolio operation complete")
    
    return mark_agent_complete(state, "DataAgent", response.model_dump())

async def _handle_data_fetch_node(state: AgentState, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle data fetching for analysis operations.
    This is the original data_agent_node logic for optimization, rebalancing, etc.
    """
    print(f"  {CYAN}[Analysis Mode]{RESET} Fetching market data")
    
    # =========================================================================
    # FIX 1: RESOLVE portfolio_name → portfolio_id (if name provided but not ID)
    # =========================================================================
    portfolio_id = parameters.get("portfolio_id")
    portfolio_name = parameters.get("portfolio_name")
    
    if portfolio_name and not portfolio_id:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.portfolio_tools import find_portfolio_by_name
        search_result = find_portfolio_by_name.func(portfolio_name)
        if search_result.get("success") and search_result.get("matches"):
            matches = search_result["matches"]
            if len(matches) == 1:
                portfolio_id = matches[0]["id"]
                parameters["portfolio_id"] = portfolio_id  # Update for downstream use
                print(f"  Resolved '{portfolio_name}' → portfolio_id={portfolio_id}")
            else:
                # Multiple matches - return error
                match_list = ", ".join([f"ID {p['id']}: {p['name']}" for p in matches])
                error_msg = f"Multiple portfolios match '{portfolio_name}': {match_list}. Please specify ID."
                return {
                    **mark_agent_complete(state, "DataAgent", {"success": False, "error": error_msg}),
                    **add_error(state, f"DataAgent: {error_msg}"),
                }
        else:
            error_msg = f"No portfolio found matching '{portfolio_name}'."
            return {
                **mark_agent_complete(state, "DataAgent", {"success": False, "error": error_msg}),
                **add_error(state, f"DataAgent: {error_msg}"),
            }
    
    # =========================================================================
    # Load portfolio context
    # =========================================================================
    holdings = []  # Initialize holdings
    
    # ⭐ STRICT: Load portfolio context (fails if invalid)
    try:
        tickers, holdings = load_portfolio_context(state)
    except PortfolioContextError as e:
        # If no tickers from context, try loading from portfolio_id in parameters
        if portfolio_id:
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.portfolio_tools import get_portfolio_holdings
            holdings_result = get_portfolio_holdings.func(portfolio_id)
            if holdings_result.get("success"):
                tickers = holdings_result.get("tickers", [])
                holdings = holdings_result.get("holdings", [])
                print(f"  Loaded {len(tickers)} tickers from portfolio {portfolio_id}: {tickers}")
            else:
                logger.error(f"Portfolio context error: {e}")
                return {
                    **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
                    **add_error(state, f"DataAgent: {str(e)}"),
                }
        else:
            logger.error(f"Portfolio context error: {e}")
            return {
                **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
                **add_error(state, f"DataAgent: {str(e)}"),
            }
    
    # Get period from router decision
    period = parameters.get("period", "3Y")
    
    print(f"  Tickers: {tickers}")
    print(f"  Period: {period}")
    print(f"  Portfolio ID: {portfolio_id}")
    
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
            "expected_returns": expected_returns,
        }
        
        if "price_data" in price_result:
            shared_updates["price_data_json"] = price_result.get("price_data")
        
        print(f"  ✓ Data loaded successfully")
        print(f"  ✓ Expected returns: {list(expected_returns.keys())}")
        
        # =========================================================================
        # FIX 2: Return holdings in state so decision summary can use them
        # =========================================================================
        return {
            **mark_agent_complete(state, "DataAgent", result),
            "shared_data": {**state.get("shared_data", {}), **shared_updates},
            "portfolio_holdings": holdings,  # ← FIX 2: Include holdings in state update
        }
    
    except DataCalculationError:
        raise
    except ImportError as e:
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

            slope = yc_data.get("slope")
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
            
            return mark_agent_complete(state, "MacroAgent", result)
            
        except ImportError as e:
            logger.warning(f"MacroAgent not available: {e}")
            raise RuntimeError(f"MacroAgent module not available: {e}")
            
    except (DataCalculationError, RuntimeError) as e:
        logger.error(f"MacroAgent error: {e}")
        return {
            **mark_agent_complete(state, "MacroAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"MacroAgent: {str(e)}"),
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "MacroAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"MacroAgent unexpected error: {str(e)}"),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# OPTIMIZATION AGENT NODE
# =============================================================================

async def optimization_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Optimization Agent node - calculates optimal portfolio weights.
    
    REQUIRES: DataAgent must have run first (covariance, returns in shared_data)
    """
    tracer = get_tracer()
    agent_ctx = None

    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("OptimizationAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in OptimizationAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print("OPTIMIZATION AGENT - Computing Optimal Weights")
        print("="*80)
        
        # ✅ STRICT: Verify DataAgent has run
        shared_data = state.get("shared_data", {})
        
        if not shared_data.get("covariance_matrix"):
            raise DataCalculationError(
                "No covariance matrix found in shared_data.\n"
                "DataAgent must run before OptimizationAgent.\n"
                "\n"
                "Check that:\n"
                "  1. DataAgent is in the execution_order\n"
                "  2. DataAgent completed successfully\n"
                "  3. Covariance calculation didn't fail"
            )
        
        if not shared_data.get("expected_returns"):
            raise DataCalculationError(
                "No expected returns found in shared_data.\n"
                "DataAgent must calculate returns before optimization."
            )
        
        # Get parameters
        router_decision = state.get("router_decision", {})
        parameters = router_decision.get("parameters", {})
        
        max_volatility = parameters.get("max_volatility")
        target_return = parameters.get("target_return")
        
        print(f"  Constraints: max_vol={max_volatility}, target_ret={target_return}")
        
        # Run optimization
        from .optimization_agent import create_optimization_agent
        agent = create_optimization_agent(verbose=False)
        
        tickers = shared_data.get("tickers", [])
        cov_matrix = shared_data.get("covariance_matrix")
        expected_returns = shared_data.get("expected_returns")
        
        print(f"  Tickers: {tickers}")
        print(f"  Expected returns: {expected_returns}")
        
        import json
        # Call the optimization tool
        method = config.optimization.default_method  # "max_sharpe"

        opt_result = agent.optimize_portfolio_tool(
            tickers=",".join(tickers),
            expected_returns=json.dumps(expected_returns),
            covariance_matrix=json.dumps(cov_matrix),
            method=method,
            max_volatility=max_volatility,
            min_weight=config.optimization.default_min_weight,
            max_weight=config.optimization.default_max_weight,
)
        print(f"  [DEBUG] opt_result: {opt_result}")
        if not opt_result.get("success"):
            raise DataCalculationError(
                f"Optimization failed: {opt_result.get('error', 'Unknown error')}"
            )
        
        # ✅ STRICT: Validate weights are floats
        weights = opt_result.get("weights") or opt_result.get("optimal_weights", {})
        for ticker, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise DataCalculationError(
                    f"Weight for {ticker} must be numeric, got {type(weight)}"
                )
        
        result = {
            "success": True,
            "optimal_weights": weights,
            "expected_return": opt_result.get("expected_return", 0),
            "expected_volatility": opt_result.get("expected_volatility", 0),
            "sharpe_ratio": opt_result.get("sharpe_ratio", 0),
            "method": opt_result.get("method", "mean_variance"),
        }
        
        # Also store in shared_data for downstream agents
        shared_updates = {
            "optimal_weights": weights,
        }
        
        print(f"  ✓ Optimization complete")
        print(f"  ✓ Sharpe: {result['sharpe_ratio']:.2f}")
        
        return {
            **mark_agent_complete(state, "OptimizationAgent", result),
            "shared_data": {**state.get("shared_data", {}), **shared_updates},
        }
        
    except DataCalculationError as e:
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
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# REBALANCE AGENT NODE
# =============================================================================

async def rebalance_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Rebalance Agent node - calculates drift and generates trades.
    """
    tracer = get_tracer()
    agent_ctx = None

    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("RebalanceAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in RebalanceAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print("REBALANCE AGENT - Analyzing Drift")
        print("="*80)
        
        # Get portfolio context
        try:
            tickers, holdings = load_portfolio_context(state)
        except PortfolioContextError as e:
            logger.error(f"Portfolio context error: {e}")
            return {
                **mark_agent_complete(state, "RebalanceAgent", {"success": False, "error": str(e)}),
                **add_error(state, f"RebalanceAgent: {str(e)}"),
            }
        
        # Get current positions and prices
        current_positions = get_current_positions(holdings)
        cost_basis = get_cost_basis(holdings)
        
        shared_data = state.get("shared_data", {})
        latest_prices = shared_data.get("latest_prices", {})
        
        # Get target weights (from optimization or state)
        target_weights = shared_data.get("optimal_weights")
        
        if not target_weights:
            # No optimization ran - use equal weight as default
            target_weights = {t: 1.0/len(tickers) for t in tickers}
            logger.warning("No optimal weights found, using equal weight")
        
        print(f"  Tickers: {tickers}")
        print(f"  Target weights: {target_weights}")
        
        # Calculate current weights
        if latest_prices and current_positions:
            total_value = sum(
                current_positions.get(t, 0) * latest_prices.get(t, 0)
                for t in tickers
            )
            if total_value > 0:
                current_weights = {
                    t: (current_positions.get(t, 0) * latest_prices.get(t, 0)) / total_value
                    for t in tickers
                }
            else:
                current_weights = {t: 0 for t in tickers}
        else:
            current_weights = {t: 0 for t in tickers}
        
        # Calculate drift
        max_drift = 0
        drifts = {}
        for ticker in tickers:
            current = current_weights.get(ticker, 0)
            target = target_weights.get(ticker, 0)
            drift = abs(current - target)
            drifts[ticker] = drift
            max_drift = max(max_drift, drift)
        
        # Get threshold from config
        threshold = config.rebalance.default_drift_threshold / 100
        
        # Determine recommendation
        if max_drift > threshold * 2:
            recommendation = "full_rebalance"
            should_rebalance = True
        elif max_drift > threshold:
            recommendation = "partial_rebalance"
            should_rebalance = True
        else:
            recommendation = "no_action"
            should_rebalance = False
        
        # Generate trades (simplified)
        trades = []
        if should_rebalance and latest_prices:
            portfolio_value = sum(
                current_positions.get(t, 0) * latest_prices.get(t, 0)
                for t in tickers
            ) or 100000  # Default if no positions
            
            for ticker in tickers:
                current_value = current_positions.get(ticker, 0) * latest_prices.get(ticker, 1)
                target_value = portfolio_value * target_weights.get(ticker, 0)
                diff = target_value - current_value
                
                if abs(diff) > 100:  # Minimum trade threshold
                    price = latest_prices.get(ticker, 1)
                    shares = abs(diff) / price
                    trades.append({
                        "ticker": ticker,
                        "action": "BUY" if diff > 0 else "SELL",
                        "shares": round(shares, 2),
                        "value": abs(diff),
                        "price": price
                    })
        
        result = {
            "success": True,
            "decision": {
                "should_rebalance": should_rebalance,
                "recommendation": recommendation,
                "max_drift": max_drift,
                "threshold": threshold,
            },
            "current_weights": current_weights,
            "target_weights": target_weights,
            "drifts": drifts,
            "trades": trades,
            "total_cost": len(trades) * 5.0,  # Simplified cost estimate
        }
        
        print(f"  ✓ Analysis complete")
        print(f"  ✓ Max drift: {max_drift:.2%}")
        print(f"  ✓ Recommendation: {recommendation}")
        
        return mark_agent_complete(state, "RebalanceAgent", result)
        
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "RebalanceAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"RebalanceAgent unexpected error: {str(e)}"),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# BACKTEST AGENT NODE
# =============================================================================

async def backtest_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Backtest Agent node - simulates historical performance.
    """
    tracer = get_tracer()
    agent_ctx = None

    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("BacktestAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in BacktestAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print("BACKTEST AGENT - Running Historical Simulation")
        print("="*80)
        
        # Get weights to backtest
        shared_data = state.get("shared_data", {})
        weights = shared_data.get("optimal_weights")
        
        if not weights:
            raise DataCalculationError(
                "No weights found to backtest.\n"
                "Run optimization first or provide weights."
            )
        
        # Get parameters
        router_decision = state.get("router_decision", {})
        parameters = router_decision.get("parameters", {})
        period = parameters.get("period", "5Y")
        
        print(f"  Weights: {weights}")
        print(f"  Period: {period}")
        
        # Run backtest
        from .backtest_agent import create_backtest_agent
        agent = create_backtest_agent(verbose=False)
        
        tickers = list(weights.keys())
        
        bt_result = agent.run_backtest_tool(
            tickers=",".join(tickers),
            weights=weights,
            period=period
        )
        
        if not bt_result.get("success"):
            raise DataCalculationError(
                f"Backtest failed: {bt_result.get('error', 'Unknown error')}"
            )
        
        result = {
            "success": True,
            "period": period,
            "backtest_metrics": bt_result.get("metrics", {}),
            "weights_used": weights,
        }
        
        print(f"  ✓ Backtest complete")
        
        return mark_agent_complete(state, "BacktestAgent", result)
    
    except DataCalculationError as e:
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
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


# =============================================================================
# RAG AGENT NODE (Phase 6.7 - Add to nodes.py)
# =============================================================================

async def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    RAG Agent node - searches documents and extracts insights for decisions.
    
    This agent is called when document context is needed:
    - query_intent == "decision" and documents are indexed
    - execution_intent == "document_search"
    - User asks about filings, earnings, Fed minutes
    
    Returns DocumentInsights that feed into the Decision Engine.
    """
    tracer = get_tracer()
    agent_ctx = None
    
    try:
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("RAGAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in RAGAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print("RAG AGENT - Document Research")
        print("="*80)
        
        # Extract context from state
        router_decision = state.get("router_decision") or {}
        parameters = router_decision.get("parameters", {})
        user_message = get_user_message(state)
        
        print(f"  Query: {user_message[:80] if user_message else 'None'}...")
        
        # Build research context
        context = {
            "ticker": parameters.get("tickers", [None])[0] if parameters.get("tickers") else None,
            "portfolio_holdings": state.get("portfolio_holdings"),
            "include_fed_sentiment": _should_include_fed_sentiment(user_message, router_decision),
        }
        
        # Import and run RAG Agent
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        insights = agent.research(
            query=user_message or "portfolio analysis",
            context=context,
        )
        
        # Check if we found useful documents
        has_results = bool(insights.get("sources"))
        
        result = {
            "success": True,
            "insights": insights,
            "sources": insights.get("sources", []),
            "key_findings": insights.get("key_findings", []),
            "risk_factors": insights.get("risk_factors", []),
            "fed_sentiment": insights.get("fed_sentiment"),
            "citations": insights.get("citations", []),
            "has_document_context": has_results,
        }
        
        # Store insights in shared_data for synthesizer/decision engine
        state_updates = mark_agent_complete(state, "RAGAgent", result)
        state_updates = {
            **state_updates,
            **add_shared_data(state, "document_insights", insights),
        }
        
        if insights.get("fed_sentiment"):
            state_updates = {
                **state_updates,
                **add_shared_data(state, "fed_sentiment", insights["fed_sentiment"].get("score", 0)),
            }
        
        print(f"  ✓ Found {len(insights.get('sources', []))} sources")
        print(f"  ✓ Key findings: {len(insights.get('key_findings', []))}")
        print(f"  ✓ Risk factors: {len(insights.get('risk_factors', []))}")
        
        return state_updates
        
    except ImportError as e:
        logger.warning(f"RAG module not available: {e}")
        return mark_agent_complete(state, "RAGAgent", {
            "success": True,  # Don't fail the pipeline
            "insights": {},
            "has_document_context": False,
            "warning": f"RAG module not available: {e}",
        })
    
    except Exception as e:
        import traceback
        logger.error(f"RAGAgent error:\n{traceback.format_exc()}")
        return {
            **mark_agent_complete(state, "RAGAgent", {
                "success": False,
                "error": str(e),
                "has_document_context": False,
            }),
            **add_warning(state, f"RAGAgent: {str(e)}"),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)

async def compliance_agent_node(state: "AgentState") -> Dict[str, Any]:
    """
    Compliance Agent node - checks portfolio against IPS constraints.
    
    Phase: 7.3 - Router & Graph Integration
    
    Handles:
    - Full compliance check (all constraints)
    - ESG screening
    - Allocation limit checks
    - Concentration limit checks
    - Single security screening
    
    Commands (from router):
    - compliance_check: Full IPS compliance check
    - esg_check: ESG-only screening
    - allocation_check: Allocation limits only
    - concentration_check: Concentration limits only
    - security_check: Single security ESG check
    """
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.compliance_agent import ComplianceAgent
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.decision_schemas import ComplianceStatus
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.esg_screener import check_security_esg
    
    tracer = get_tracer()
    agent_ctx = None
    
    try:
        # Tracing setup
        if tracer and hasattr(tracer, "get_current_request"):
            req = tracer.get_current_request()
            if req:
                agent_ctx = req.trace_agent("ComplianceAgent")
                agent_ctx.__enter__()
    except Exception as e:
        logger.warning(f"Tracing failed in ComplianceAgent (ignoring): {e}")
    
    try:
        print("\n" + "="*80)
        print(f"{GREEN}COMPLIANCE AGENT - IPS Compliance Check{RESET}")
        print("="*80)
        
        # Get parameters from router decision
        router_decision = state.get("router_decision") or {}
        parameters = router_decision.get("parameters", {})
        command = parameters.get("command", "compliance_check")
        portfolio_id = parameters.get("portfolio_id") or state.get("portfolio_id")
        client_id = parameters.get("client_id")
        tickers = parameters.get("tickers", [])
        
        print(f"  Command: {command}")
        print(f"  Portfolio ID: {portfolio_id}")
        print(f"  Client ID: {client_id}")
        
        # =====================================================================
        # BRANCH 1: Single Security ESG Check
        # =====================================================================
        if command == "security_check" and tickers:
            ticker = tickers[0] if isinstance(tickers, list) else tickers
            print(f"  Checking security: {ticker}")
            
            result = check_security_esg(ticker=ticker)
            
            if result["excluded"]:
                response = {
                    "success": True,
                    "command": "security_check",
                    "ticker": ticker,
                    "allowed": False,
                    "category": result["category"],
                    "reason": result["reason"],
                    "company_name": result.get("company_name"),
                    "message": f"❌ {ticker} is NOT allowed - {result['category'].replace('_', ' ').title()} exclusion: {result['reason']}"
                }
            else:
                response = {
                    "success": True,
                    "command": "security_check",
                    "ticker": ticker,
                    "allowed": True,
                    "message": f"✅ {ticker} is allowed under current ESG policy"
                }
            
            print(f"  Result: {'Excluded' if result['excluded'] else 'Allowed'}")
            
            return {
                **mark_agent_complete(state, "ComplianceAgent", response),
            }
        
        # =====================================================================
        # BRANCH 2: Full Portfolio Compliance Check
        # =====================================================================
        if not portfolio_id:
            return {
                **mark_agent_complete(state, "ComplianceAgent", {
                    "success": False,
                    "error": "No portfolio specified. Please provide portfolio_id."
                }),
                **add_error(state, "ComplianceAgent: No portfolio specified"),
            }
        
        # Initialize compliance agent
        agent = ComplianceAgent()
        
        try:
            # Run compliance check
            report = agent.run_compliance_check(
                portfolio_id=portfolio_id,
                client_id=client_id,
                include_passing=(command == "compliance_report")  # Full report includes passing
            )
            
            # Build response
            response = {
                "success": True,
                "command": command,
                "portfolio_id": report.portfolio_id,
                "portfolio_name": report.portfolio_name,
                "client_id": report.client_id,
                "client_name": report.client_name,
                "compliance_run_id": report.compliance_run_id,
                "status": report.status.value,
                "is_compliant": report.status == ComplianceStatus.COMPLIANT,
                "total_aum": report.total_aum,
                "num_positions": report.num_positions,
                "num_breaches": report.num_breaches,
                "num_critical": report.num_critical,
                "num_warnings": len(report.warnings),
                "allocation": report.allocation,
                "breaches": [
                    {
                        "type": b.constraint_type.value,
                        "name": b.constraint_name,
                        "severity": b.severity.value if b.severity else None,
                        "ticker": b.ticker,
                        "asset_class": b.asset_class,
                        "current_value": b.current_value,
                        "limit_value": b.limit_value,
                        "message": b.message,
                        "action": b.action
                    }
                    for b in report.breaches
                ],
                "warnings": [
                    {
                        "type": w.constraint_type.value,
                        "name": w.constraint_name,
                        "message": w.message
                    }
                    for w in report.warnings
                ],
                "recommendations": report.recommendations,
                "remediation_trades": [
                    {
                        "action": t.action,
                        "ticker": t.ticker,
                        "shares": t.shares,
                        "estimated_value": t.estimated_value,
                        "reason": t.reason,
                        "priority": t.priority
                    }
                    for t in report.remediation_trades
                ],
                # Store formatted report for synthesizer
                "formatted_report": report.format_full_report(),
                "formatted_summary": report.format_summary()
            }
            
            # Log summary
            print(f"  Status: {report.status.value.upper()}")
            print(f"  Breaches: {report.num_breaches} ({report.num_critical} critical)")
            print(f"  Total AUM: ${report.total_aum:,.2f}")
            
        finally:
            agent.close()
        
        return {
            **mark_agent_complete(state, "ComplianceAgent", response),
        }
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"ComplianceAgent error:\n{error_detail}")
        
        return {
            **mark_agent_complete(state, "ComplianceAgent", {
                "success": False,
                "error": str(e)
            }),
            **add_error(state, f"ComplianceAgent: {str(e)}"),
        }
    
    finally:
        if agent_ctx:
            agent_ctx.__exit__(None, None, None)


def _should_include_fed_sentiment(user_message: str, router_decision: Dict) -> bool:
    """Determine if Fed sentiment analysis should be included."""
    if not user_message:
        return False
    
    # Check query for Fed-related keywords
    fed_keywords = ["fed", "fomc", "interest rate", "monetary", "powell", "inflation"]
    query_lower = user_message.lower()
    
    if any(kw in query_lower for kw in fed_keywords):
        return True
    
    # Check if macro analysis is part of the plan
    execution_order = router_decision.get("execution_order", [])
    if "MacroAgent" in execution_order:
        return True
    
    return False
            
# =============================================================================
# SYNTHESIZER NODE
# =============================================================================

async def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizer node - combines results from all agents into a strict AgentResponse.
    
    PHASE 6.6 UPDATE:
    - For DECISION queries: Generates PMDecisionSummary FIRST
    - For other queries: Standard formatting (no action bias)
    """
    try:
        # 1. Extract State
        decision = state.get("router_decision") or {}
        
        # Extract both intents
        query_intent = decision.get("query_intent", "unknown")
        execution_intent = decision.get("execution_intent") or decision.get("intent", "unknown")
        
        sub_results = state.get("sub_results") or {}
        errors = state.get("errors") or []
        
        # DEBUG: Check what we're receiving
        print(f"  [DEBUG] query_intent: {query_intent}")
        print(f"  [DEBUG] OptimizationAgent result keys: {sub_results.get('OptimizationAgent', {}).keys()}")
        print(f"  [DEBUG] sub_results keys: {sub_results.keys()}")
        print(f"  [DEBUG] OptimizationAgent: {sub_results.get('OptimizationAgent', 'NOT FOUND')}")
        print(f"  [DEBUG] DataAgent data: {sub_results.get('DataAgent', {}).get('data', {}).keys()}")
        print(f"  [DEBUG] shared_data: {state.get('shared_data', {}).keys()}")

        # 2. Prepare Output Containers
        lines: List[str] = []
        structured_data: Dict[str, Any] = {}
        status = True
        
        # 3. Handle Top-Level Errors
        if errors:
            lines.append("⚠️ **Notices:**")
            for err in errors[:3]:
                lines.append(f"- {err}")
            lines.append("")
        
        # =====================================================================
        # 4. DECISION SUMMARY (Only for DECISION queries)
        # =====================================================================
        if should_generate_decision_summary(query_intent):
            decision_summary = _generate_decision_summary(sub_results, decision, state)
            if decision_summary:
                lines.append(decision_summary)
                lines.append("")  # Separator before detailed results
        
        # =====================================================================
        # 5. Intent-Specific Formatting (based on execution_intent)
        # =====================================================================
        
        if execution_intent == "data_management":
            data_result = sub_results.get("DataAgent", {})
            
            if data_result.get("success"):
                lines.append("✅ **Data Operation Complete**")
                
                inner_data = data_result.get("data", {})
                msg = inner_data.get("message") or inner_data.get("reasoning")
                if msg:
                    lines.append(str(msg))
                
                assets = inner_data.get("assets", [])
                if assets:
                    lines.append("")
                    lines.append("**Tracked Assets:**")
                    for asset in assets[:20]:
                        if isinstance(asset, dict):
                            ticker = asset.get("ticker", "?")
                            name = asset.get("name", "")
                            lines.append(f"  • {ticker}: {name}")
                        else:
                            lines.append(f"  • {asset}")
                    if len(assets) > 20:
                        lines.append(f"  ... and {len(assets) - 20} more")
                
                if "metrics" in inner_data:
                    structured_data["metrics"] = inner_data["metrics"]
            else:
                status = False
                lines.append("❌ **Data Operation Failed**")
                lines.append(f"Error: {data_result.get('error', 'Unknown error')}")

        elif execution_intent in ("portfolio_management", "portfolio_mgmt"):
            data_result = sub_results.get("DataAgent", {})
            
            if data_result.get("success"):
                lines.append("✅ **Portfolio Operation Complete**")
                
                inner_data = data_result.get("data", {})
                msg = inner_data.get("message") or inner_data.get("reasoning")
                if msg:
                    lines.append(str(msg))
                
                if "portfolios" in inner_data:
                    structured_data["portfolios"] = inner_data["portfolios"]
                if "holdings" in inner_data:
                    structured_data["holdings"] = inner_data["holdings"]
                if "summary" in inner_data:
                    structured_data["summary"] = inner_data["summary"]
            else:
                status = False
                lines.append("❌ **Portfolio Operation Failed**")
                error_msg = data_result.get("error") or data_result.get("data", {}).get("error", "Unknown error")
                lines.append(f"Error: {error_msg}")

        elif execution_intent == "optimization":
            lines.extend(_format_optimization_response(sub_results, include_recommendation=(query_intent == "decision")))
            
        elif execution_intent == "macro_analysis":
            lines.extend(_format_macro_response(sub_results, include_recommendation=(query_intent == "decision")))
            
        elif execution_intent == "rebalancing":
            lines.extend(_format_rebalance_response(sub_results, include_recommendation=(query_intent == "decision")))
            
        elif execution_intent == "backtest":
            lines.extend(_format_backtest_response(sub_results))
            
        elif execution_intent == "combined":
            if "MacroAgent" in sub_results:
                lines.extend(_format_macro_response(sub_results, include_recommendation=(query_intent == "decision")))
                lines.append("")
            if "RebalanceAgent" in sub_results:
                lines.extend(_format_rebalance_response(sub_results, include_recommendation=(query_intent == "decision")))
            if "OptimizationAgent" in sub_results:
                lines.extend(_format_optimization_response(sub_results, include_recommendation=(query_intent == "decision")))
        
        elif execution_intent == "compliance_check":
            lines.extend(_format_compliance_response(sub_results, include_recommendation=(query_intent == "decision")))
        
        else:
            lines.append("Analysis complete. Component status:")
            for agent, result in sub_results.items():
                succeeded = result.get('success', False)
                icon = '✓' if succeeded else '✗'
                lines.append(f"- {agent}: {icon}")
                if not succeeded:
                    status = False
                    lines.append(f"  Error: {result.get('error')}")

                
        if "RAGAgent" in sub_results:
            doc_lines = _format_document_insights(sub_results)
            if doc_lines:
                lines.append("")
                lines.extend(doc_lines)

        if "ComplianceAgent" in sub_results and execution_intent != "compliance_check":
            lines.append("")
            lines.extend(_format_compliance_response(sub_results, include_recommendation=(query_intent == "decision")))

        # =====================================================================
        # 6. Construct Strict Output (AgentResponse)
        # =====================================================================
        final_response = AgentResponse(
            success=status,
            agent_name="Synthesizer",
            data={
                "summary": "\n".join(lines),
                "details": structured_data,
                "query_intent": query_intent,
                "execution_intent": execution_intent,
                "original_intent": execution_intent
            },
            error=None if status else "One or more sub-tasks failed."
        )

        return set_final_response(state, final_response.model_dump())
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_response = AgentResponse(
            success=False,
            agent_name="Synthesizer",
            error=f"Critical Synthesis Error: {str(e)}"
        )
        return set_final_response(state, error_response.model_dump())
    


# =============================================================================
# DECISION SUMMARY GENERATOR (NEW)
# =============================================================================

def _generate_decision_summary(sub_results: Dict, router_decision: Dict, state: Dict) -> str:
    """
    Generate PMDecisionSummary for DECISION queries.
    
    FIXED: Now extracts CURRENT weights from portfolio holdings,
    not from optimization results.
    
    Args:
        sub_results: Results from all agents
        router_decision: Router's decision dict
        state: Full agent state (needed for portfolio_holdings)
    """
    try:
        from .decision_engine import (
            run_decision_assessment,
            extract_macro_regime_from_results,
            extract_vix_from_results
        )
        
        # FIXED: Get current weights from HOLDINGS, not optimization
        current_weights = _extract_current_weights_from_state(state, sub_results)
        
        # Get target/proposed weights from optimization
        target_weights = _extract_target_weights(sub_results)
        
        if not current_weights:
            # Can't assess without current weights - skip decision summary
            return ""
        
        # If no target weights (optimization didn't run), use current as target
        if not target_weights:
            target_weights = current_weights
        
        # Calculate drift between current and target
        max_drift = _calculate_max_drift(current_weights, target_weights)
        
        # Extract macro context
        macro_result = sub_results.get("MacroAgent", {})
        macro_regime = extract_macro_regime_from_results(macro_result)
        vix_level = extract_vix_from_results(macro_result)
        
        # Extract volatility if available
        opt_result = sub_results.get("OptimizationAgent", {})
        volatility = opt_result.get("expected_volatility")
        
        # Extract document insights from shared_data (Phase 6.7)
        shared_data = state.get("shared_data", {})
        document_insights = shared_data.get("document_insights")
        
        # Run decision assessment with document context
        risk, decision = run_decision_assessment(
            current_weights=current_weights,
            target_weights=target_weights,
            max_drift=max_drift,
            macro_regime=macro_regime,
            vix_level=vix_level,
            portfolio_volatility=volatility,
            trigger="user_request",
            document_insights=document_insights,  # NEW: Phase 6.7
        )
        
        # =====================================================================
        # LOG DECISION TO DATABASE
        # =====================================================================
        try:
            from .decision_logger import log_decision_from_summary
            
            # Get context from state
            portfolio_id = state.get("portfolio_id") or router_decision.get("parameters", {}).get("portfolio_id")
            request_id = state.get("request_id")
            
            # Get original user query
            user_query = None
            messages = state.get("messages", [])
            if messages:
                from langchain_core.messages import HumanMessage
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        user_query = msg.content
                        break
            
            log_decision_from_summary(
                decision=decision,
                risk=risk,
                current_weights=current_weights,
                proposed_weights=target_weights,
                max_drift=max_drift,
                macro_regime=macro_regime,
                vix_level=vix_level,
                portfolio_id=portfolio_id,
                request_id=request_id,
                user_query=user_query,
            )
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"[WARNING] Decision logging failed: {e}")

        # Format output with BOTH current and proposed allocations
        output_lines = [decision.format_summary()]
        
        # Add current vs proposed comparison if they differ
        if target_weights and target_weights != current_weights:
            output_lines.append("")
            output_lines.append("═" * 60)
            output_lines.append("ALLOCATION COMPARISON")
            output_lines.append("═" * 60)
            output_lines.append("")
            output_lines.append("**Current Allocation:**")
            for ticker, weight in sorted(current_weights.items(), key=lambda x: x[1], reverse=True):
                output_lines.append(f"  • {ticker}: {weight*100:.1f}%")
            output_lines.append("")
            output_lines.append("**Proposed Allocation:**")
            for ticker, weight in sorted(target_weights.items(), key=lambda x: x[1], reverse=True):
                change = (weight - current_weights.get(ticker, 0)) * 100
                change_str = f" ({change:+.1f}%)" if abs(change) > 0.1 else ""
                output_lines.append(f"  • {ticker}: {weight*100:.1f}%{change_str}")
        
        return "\n".join(output_lines)
        
    except Exception as e:
        # Don't crash synthesizer if decision engine fails
        print(f"[WARNING] Decision summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return ""

def _extract_target_weights(sub_results: Dict) -> Dict[str, float]:
    """Extract target portfolio weights from agent results."""
    # Try RebalanceAgent
    rebal = sub_results.get("RebalanceAgent", {})
    if rebal.get("success"):
        weights = rebal.get("target_weights") or rebal.get("data", {}).get("target_weights")
        if weights:
            return weights
    
    # Try OptimizationAgent (optimal = target)
    opt = sub_results.get("OptimizationAgent", {})
    if opt.get("success"):
        return opt.get("optimal_weights", {})
    
    return {}

def _extract_current_weights_from_state(state: Dict, sub_results: Dict) -> Dict[str, float]:
    """
    Extract CURRENT portfolio weights from state.
    
    Priority order:
    1. Calculate from portfolio_holdings + latest_prices (most accurate)
    2. Get from RebalanceAgent.current_weights (if rebalance ran)
    3. Return empty dict (triggers skip of decision summary)
    
    NEVER use OptimizationAgent weights - those are PROPOSED, not CURRENT.
    """
    # Method 1: Calculate from holdings + prices
    holdings = state.get("portfolio_holdings", [])
    shared_data = state.get("shared_data", {})
    latest_prices = shared_data.get("latest_prices", {})
    
    if holdings and latest_prices:
        # Calculate current value of each holding
        values = {}
        for h in holdings:
            ticker = h.get("ticker")
            quantity = h.get("quantity", 0)
            price = latest_prices.get(ticker, 0)
            if ticker and quantity and price:
                values[ticker] = quantity * price
        
        total_value = sum(values.values())
        if total_value > 0:
            weights = {ticker: value / total_value for ticker, value in values.items()}
            print(f"  [DEBUG] Current weights from holdings: {weights}")
            return weights
    
    # Method 2: Try RebalanceAgent (if it ran)
    rebal = sub_results.get("RebalanceAgent", {})
    if rebal.get("success"):
        weights = rebal.get("current_weights") or rebal.get("data", {}).get("current_weights")
        if weights:
            print(f"  [DEBUG] Current weights from RebalanceAgent: {weights}")
            return weights
    
    # Method 3: If we have holdings but no prices, use equal weights as fallback
    if holdings:
        tickers = [h.get("ticker") for h in holdings if h.get("ticker")]
        if tickers:
            equal_weight = 1.0 / len(tickers)
            weights = {t: equal_weight for t in tickers}
            print(f"  [DEBUG] Current weights (equal fallback): {weights}")
            return weights
    
    # No current weights available
    print(f"  [DEBUG] No current weights available - skipping decision summary")
    return {}

def _extract_target_weights(sub_results: Dict) -> Dict[str, float]:
    """Extract target/proposed portfolio weights from agent results."""
    # Try RebalanceAgent first
    rebal = sub_results.get("RebalanceAgent", {})
    if rebal.get("success"):
        weights = rebal.get("target_weights") or rebal.get("data", {}).get("target_weights")
        if weights:
            return weights
    
    # Try OptimizationAgent (optimal = proposed target)
    opt = sub_results.get("OptimizationAgent", {})
    if opt.get("success"):
        return opt.get("optimal_weights", {})
    
    return {}

def _calculate_max_drift(current: Dict[str, float], target: Dict[str, float]) -> float:
    """Calculate maximum drift between current and target weights."""
    if not current or not target:
        return 0.0
    
    all_tickers = set(current.keys()) | set(target.keys())
    max_drift = 0.0
    
    for ticker in all_tickers:
        curr_weight = current.get(ticker, 0)
        tgt_weight = target.get(ticker, 0)
        drift = abs(curr_weight - tgt_weight)
        max_drift = max(max_drift, drift)
    
    return max_drift

# =============================================================================
# HELPER FUNCTIONS (PRESERVED from original + include_recommendation param)
# =============================================================================

def _format_optimization_response(sub_results: Dict, include_recommendation: bool = True) -> List[str]:
    """
    Format optimization results.
    PRESERVED: Original structure with flat keys (optimal_weights, expected_return, etc.)
    ADDED: include_recommendation parameter for query_intent awareness
    """
    lines = ["📊 **PORTFOLIO OPTIMIZATION RESULTS**", ""]
    
    opt = sub_results.get("OptimizationAgent", {})
    if not opt.get("success"):
        lines.append("⚠️ Optimization failed")
        lines.append(f"Error: {opt.get('error', 'Unknown')}")
        return lines
    
    # PRESERVED: Original uses flat "optimal_weights" key
    weights = opt.get("optimal_weights", {})
    
    if weights:
        lines.append("**Optimal Allocation:**")
        for ticker, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {ticker}: {weight*100:.1f}%")
    
    lines.append("")
    lines.append("**Expected Metrics:**")
    
    # PRESERVED: Original uses flat keys directly on opt
    ret = opt.get('expected_return', 0.0)
    vol = opt.get('expected_volatility', 0.0)
    sharpe = opt.get('sharpe_ratio', 0.0)
    
    lines.append(f"  • Return: {ret*100:.2f}%")
    lines.append(f"  • Volatility: {vol*100:.2f}%")
    lines.append(f"  • Sharpe Ratio: {sharpe:.2f}")
    
    # NEW: Only add recommendation for DECISION queries
    if include_recommendation and weights:
        lines.append("")
        lines.append("**Recommendation:** Consider rebalancing to these target weights.")
    
    return lines


def _format_macro_response(sub_results: Dict, include_recommendation: bool = True) -> List[str]:
    """
    Format macro analysis results.
    PRESERVED: Original nested structure (snapshot -> vix, yield_curve; regime -> regime, risk_stance)
    ADDED: include_recommendation parameter for query_intent awareness
    """
    lines = ["🌍 **MACRO ENVIRONMENT ANALYSIS**", ""]
    
    macro = sub_results.get("MacroAgent", {})
    if not macro.get("success"):
        lines.append("⚠️ Macro analysis unavailable")
        return lines
    
    # PRESERVED: Original nested structure
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
    
    # MODIFIED: Only show recommendation for DECISION queries
    adj = regime.get('equity_adjustment', 0)
    if include_recommendation and adj != 0:
        lines.append("")
        lines.append(f"**Recommendation:** Adjust equity by {adj:+.0%}")
    elif not include_recommendation and adj != 0:
        # For INFORMATION queries, just state the signal without "recommendation"
        lines.append("")
        lines.append(f"**Tactical Signal:** Equity adjustment signal: {adj:+.0%}")
    
    return lines


def _format_rebalance_response(sub_results: Dict, include_recommendation: bool = True) -> List[str]:
    """
    Format rebalancing results.
    PRESERVED: Original structure with decision, trades, taa_signal, total_cost
    ADDED: include_recommendation parameter for query_intent awareness
    """
    lines = ["⚖️ **REBALANCING ANALYSIS**", ""]
    
    rebal = sub_results.get("RebalanceAgent", {})
    if not rebal.get("success"):
        lines.append("⚠️ Rebalancing analysis unavailable")
        return lines
    
    # PRESERVED: Original structure
    decision = rebal.get("decision", {})
    trades = rebal.get("trades", [])
    
    # MODIFIED: Show recommendation only for DECISION queries
    if include_recommendation:
        lines.append(f"**Recommendation:** {decision.get('recommendation', 'N/A').upper()}")
    else:
        lines.append(f"**Status:** {decision.get('recommendation', 'N/A').upper()}")
    
    lines.append(f"**Max Drift:** {decision.get('max_drift', 0):.1%}")
    
    # PRESERVED: Trades section (always show for transparency)
    if trades:
        lines.append("")
        if include_recommendation:
            lines.append("**Proposed Trades:**")
        else:
            lines.append("**Required Trades (if rebalancing):**")
        
        for trade in trades[:5]:
            lines.append(
                f"  • {trade['action']} {trade['shares']:.0f} {trade['ticker']} "
                f"(~€{trade.get('value', 0):,.0f})"
            )
        
        lines.append("")
        lines.append(f"**Est. Transaction Cost:** €{rebal.get('total_cost', 0):.2f}")
    
    # PRESERVED: TAA signal if available
    taa = rebal.get("taa_signal")
    if taa:
        lines.append("")
        lines.append(f"**Tactical Signal:** {taa.get('regime', 'N/A')} regime")
    
    return lines


def _format_backtest_response(sub_results: Dict) -> List[str]:
    """
    Format backtest results.
    PRESERVED: Original structure with period, metrics, disclaimer
    NOTE: Backtest is always informational (no include_recommendation needed)
    """
    lines = ["📈 **BACKTEST RESULTS**", ""]
    
    bt = sub_results.get("BacktestAgent", {})
    if not bt.get("success"):
        lines.append("⚠️ Backtest failed")
        return lines
    
    # PRESERVED: Original logic
    backtest_metrics = bt.get("backtest_metrics", {})
    metrics = backtest_metrics if backtest_metrics else bt
    
    # PRESERVED: Period display
    lines.append(f"**Period:** {bt.get('period', metrics.get('start_date', 'N/A'))}")
    lines.append("")
    lines.append("**Performance:**")

    # PRESERVED: Smart formatter helper
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
    
    # PRESERVED: Disclaimer
    lines.append("⚠️ Past performance does not guarantee future results.")
    
    return lines

def _format_document_insights(sub_results: Dict) -> List[str]:
    """
    Format document research results.
    Called when RAGAgent has run and found documents.
    """
    lines = ["📄 **DOCUMENT INSIGHTS**", ""]
    
    rag = sub_results.get("RAGAgent", {})
    
    if not rag.get("success") or not rag.get("has_document_context"):
        return []  # No document context - skip this section
    
    insights = rag.get("insights", {})
    
    # Sources used
    sources = insights.get("sources", [])
    if sources:
        lines.append("**Sources:**")
        for source in sources[:3]:
            lines.append(f"  • {source}")
        lines.append("")
    
    # Key findings
    findings = insights.get("key_findings", [])
    if findings:
        lines.append("**Key Findings:**")
        for finding in findings[:3]:
            # Truncate long findings
            finding_short = finding[:150] + "..." if len(finding) > 150 else finding
            lines.append(f"  • {finding_short}")
        lines.append("")
    
    # Risk factors from documents
    risk_factors = insights.get("risk_factors", [])
    if risk_factors:
        lines.append("**Document Risk Factors:**")
        for risk in risk_factors[:3]:
            lines.append(f"  ⚠️ {risk}")
        lines.append("")
    
    # Fed sentiment (if analyzed)
    fed = insights.get("fed_sentiment")
    if fed and fed.get("success"):
        score = fed.get("score", 0)
        confidence = fed.get("confidence", 0)
        method = fed.get("method", "unknown")
        
        stance = "Hawkish" if score > 0.3 else "Dovish" if score < -0.3 else "Neutral"
        
        lines.append("**Fed Sentiment:**")
        lines.append(f"  • Stance: {stance} (score: {score:+.2f})")
        lines.append(f"  • Confidence: {confidence:.0%}")
        lines.append(f"  • Method: {method}")
        lines.append("")
    
    return lines

def _format_compliance_response(sub_results: Dict, include_recommendation: bool = True) -> List[str]:
    """
    Format compliance check results.
    
    Phase: 7.3 - Router & Graph Integration
    """
    lines = ["📋 **COMPLIANCE REPORT**", ""]
    
    compliance = sub_results.get("ComplianceAgent", {})
    
    if not compliance.get("success"):
        error = compliance.get("error", "Unknown error")
        lines.append(f"⚠️ Compliance check failed: {error}")
        return lines
    
    # Single security check
    if compliance.get("command") == "security_check":
        ticker = compliance.get("ticker", "Unknown")
        if compliance.get("allowed"):
            lines.append(f"✅ **{ticker}** is allowed under current ESG policy")
        else:
            category = compliance.get("category", "").replace("_", " ").title()
            reason = compliance.get("reason", "")
            lines.append(f"❌ **{ticker}** is NOT allowed")
            lines.append(f"   Category: {category}")
            lines.append(f"   Reason: {reason}")
        return lines
    
    # Full compliance report
    status = compliance.get("status", "unknown")
    status_emoji = {
        "compliant": "✅ COMPLIANT",
        "warning": "⚠️ WARNING",
        "non_compliant": "🔴 NON-COMPLIANT"
    }
    
    lines.append(f"**Portfolio:** {compliance.get('portfolio_name', 'N/A')}")
    lines.append(f"**Client:** {compliance.get('client_name', 'N/A')} ({compliance.get('client_id', 'N/A')})")
    lines.append(f"**Status:** {status_emoji.get(status, status.upper())}")
    lines.append("")
    
    # Summary metrics
    lines.append(f"**Total AUM:** ${compliance.get('total_aum', 0):,.2f}")
    lines.append(f"**Positions:** {compliance.get('num_positions', 0)}")
    lines.append(f"**Breaches:** {compliance.get('num_breaches', 0)} ({compliance.get('num_critical', 0)} critical)")
    lines.append("")
    
    # Allocation
    allocation = compliance.get("allocation", {})
    if allocation:
        lines.append("**Asset Allocation:**")
        for asset_class, weight in sorted(allocation.items(), key=lambda x: -x[1]):
            lines.append(f"  • {asset_class.title()}: {weight:.1%}")
        lines.append("")
    
    # Breaches
    breaches = compliance.get("breaches", [])
    if breaches:
        lines.append("**Breaches:**")
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "ℹ️"}
        
        for b in breaches[:5]:  # Limit to 5 for readability
            sev = severity_emoji.get(b.get("severity", ""), "")
            ticker_or_class = b.get("ticker") or b.get("asset_class") or "N/A"
            lines.append(f"  {sev} [{b.get('type', 'N/A').upper()}] {ticker_or_class}: {b.get('message', '')}")
        
        if len(breaches) > 5:
            lines.append(f"  ... and {len(breaches) - 5} more")
        lines.append("")
    
    # Remediation trades (only for DECISION queries)
    if include_recommendation:
        trades = compliance.get("remediation_trades", [])
        if trades:
            lines.append("**Recommended Trades:**")
            for t in trades[:4]:
                action = t.get("action", "")
                ticker = t.get("ticker", "")
                shares = t.get("shares")
                value = t.get("estimated_value", 0)
                
                if shares:
                    lines.append(f"  • {action} {shares:.0f} shares of {ticker} (~${value:,.0f})")
                else:
                    lines.append(f"  • {action} {ticker} (~${value:,.0f})")
            lines.append("")
    
    # Run ID for audit
    lines.append(f"*Run ID: {compliance.get('compliance_run_id', 'N/A')}*")
    
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
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.observability.tracer import AgentTrace
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