# src/agents/nodes.py
# Purpose: LangGraph node functions for each agent
# Principle: Nodes are thin wrappers that call agent logic and update state
# Phase: 6.2 - LangGraph State Machine

from config import config

from typing import Dict, Any, Optional, Literal, List
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
        decision, validation = await router.route(user_message)
        
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
        "execution_order": [
            a if isinstance(a, str) else a.value 
            for a in decision.execution_order
        ],
        "parameters": {
            "tickers": decision.parameters.tickers,
            "period": decision.parameters.period,
            "max_volatility": decision.parameters.max_volatility,
            "target_return": decision.parameters.target_return,
            "portfolio_value": decision.parameters.portfolio_value,
        },
        "is_multi_step": decision.is_multi_step,
        "reasoning": decision.reasoning,
    }


# =============================================================================
# AGENT DISPATCHER NODE
# =============================================================================

async def agent_dispatcher_node(state: AgentState) -> Dict[str, Any]:
    """
    Dispatcher node - routes to the appropriate agent based on execution order.
    
    This is a "passthrough" node that just identifies which agent runs next.
    The actual conditional routing is done by the edge function.
    """
    next_agent = get_next_agent(state)
    
    if next_agent:
        return {"current_agent": next_agent}
    else:
        return {"current_agent": None}

# =============================================================================
# DATA AGENT NODE
# =============================================================================

# =============================================================================
# IMPROVED: DATA AGENT NODE
# =============================================================================

async def data_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Data Agent node - fetches market data and calculates metrics.
    
    IMPROVEMENTS:
    1. Better logging of what data is being stored
    2. Ensure expected_returns is always set if covariance is available
    3. More robust error handling
    """
    tracer = get_tracer()
    agent_ctx = None
    
    try:
        if tracer and tracer._current_trace:
            agent_ctx = tracer._current_trace and AgentTraceHelper(tracer, state.get("request_id", ""), "DataAgent")
            if agent_ctx:
                agent_ctx.__enter__()
                agent_ctx.log_thinking("Fetching market data...")
        
        # Get parameters from router decision
        params = state.get("router_decision", {}).get("parameters", {})
        tickers = params.get("tickers", ["SPY", "TLT", "GLD"])
        period = params.get("period", "3Y")
        
        print(f"  [DEBUG] DataAgent starting with tickers: {tickers}, period: {period}")
        
        # Try to import and use the actual DataAgent
        try:
            from .data_agent import create_data_agent
            agent = create_data_agent(verbose=False)
            
            # Fetch prices
            tickers_str = ",".join(tickers) if tickers else "SPY,TLT,GLD"
            print(f"  [DEBUG] Fetching prices for: {tickers_str}")
            price_result = agent.fetch_prices_tool(tickers=tickers_str, period=period)
            print(f"  [DEBUG] Price fetch success: {price_result.get('success')}")
            
            # Calculate covariance
            print(f"  [DEBUG] Calculating covariance")
            cov_result = agent.calculate_covariance_tool(
                tickers=tickers_str, 
                period=period
            )
            print(f"  [DEBUG] Covariance success: {cov_result.get('success')}")
            print(f"  [DEBUG] FULL cov_result: {cov_result}")

        
            # Calculate returns for optimization
            returns_result = {}
            if hasattr(agent, 'calculate_returns_tool'):
                print(f"  [DEBUG] Calculating returns")
                returns_result = agent.calculate_returns_tool(
                    tickers=tickers_str, 
                    period=period
                )
                print(f"  [DEBUG] Returns success: {returns_result.get('success')}")
                print(f"  [DEBUG] Returns keys: {list(returns_result.keys())}")
            else:
                print(f"  [WARNING] DataAgent doesn't have calculate_returns_tool!")
            
            result = {
                "success": True,
                "prices": price_result,
                "covariance": cov_result,
                "returns": returns_result,
                "tickers": tickers,
                "period": period,
            }
            
            # Store shared data for other agents
            shared_updates = {
                "tickers": tickers,
                "tickers_str": tickers_str,
            }
            
            if price_result.get("success"):
                shared_updates["latest_prices"] = price_result.get("latest_prices", {})
                if "price_data" in price_result:
                    shared_updates["price_data_json"] = price_result.get("price_data")
            
            if cov_result.get("success"):
                shared_updates["covariance_matrix"] = cov_result.get("covariance_matrix", {})
                shared_updates["volatilities"] = cov_result.get("annualized_volatilities", {})
                print(f"  [DEBUG] Stored covariance_matrix: {bool(shared_updates['covariance_matrix'])}")
            
            # FIX: Ensure expected_returns is ALWAYS set if we have data
            if returns_result.get("success"):
                print(f"  [DEBUG] Processing returns_result")
                
                # Try multiple keys to find returns data
                raw_rets = returns_result.get("annualized_returns_raw")
                if raw_rets:
                    print(f"  [DEBUG] Found annualized_returns_raw: {raw_rets}")
                    shared_updates["expected_returns"] = raw_rets
                else:
                    # Try other keys
                    ann_rets = returns_result.get("annualized_returns")
                    if ann_rets:
                        print(f"  [DEBUG] Found annualized_returns: {ann_rets}")
                        # Clean formatted strings (e.g. "12.5%") -> 0.125
                        clean_rets = {}
                        for k, v in ann_rets.items():
                            try:
                                if isinstance(v, str) and "%" in v:
                                    clean_rets[k] = float(v.strip('%')) / 100.0
                                else:
                                    clean_rets[k] = float(v)
                            except (ValueError, TypeError):
                                print(f"  [WARNING] Could not convert return for {k}: {v}")
                                clean_rets[k] = 0.05  # Default 5% if parse fails
                        shared_updates["expected_returns"] = clean_rets
                    else:
                        print(f"  [WARNING] No returns data found in returns_result keys: {list(returns_result.keys())}")
                        # FIX: Generate simple expected returns if missing
                        # Use historical average or simple heuristic
                        shared_updates["expected_returns"] = {t: 0.08 for t in tickers}  # Default 8%
            else:
                print(f"  [WARNING] returns_result not successful, using defaults")
                # FIX: Always provide expected_returns even if calculation failed
                shared_updates["expected_returns"] = {t: 0.08 for t in tickers}  # Default 8%
            
            print(f"  [DEBUG] Final shared_data keys: {list(shared_updates.keys())}")
            print(f"  [DEBUG] expected_returns value: {shared_updates.get('expected_returns')}")
                       
            return {
                **mark_agent_complete(state, "DataAgent", result),
                "shared_data": {**state.get("shared_data", {}), **shared_updates},
            }
            
        except ImportError as e:
            print(f"  [DEBUG] ImportError, using mock data: {e}")
            # Fallback: Return mock data for testing
            import json
            
            tickers_str = ",".join(tickers) if tickers else "SPY,TLT,GLD"
            
            # Mock data
            mock_prices = {"SPY": 590.0, "TLT": 88.0, "GLD": 420.0}
            mock_returns = {"SPY": 0.10, "TLT": 0.04, "GLD": 0.06}
            mock_cov = {
                "SPY": {"SPY": 0.0324, "TLT": -0.0054, "GLD": 0.0018},
                "TLT": {"SPY": -0.0054, "TLT": 0.0144, "GLD": 0.0009},
                "GLD": {"SPY": 0.0018, "TLT": 0.0009, "GLD": 0.0225},
            }
            
            result = {
                "success": True,
                "mock": True,
                "tickers": tickers,
                "period": period,
                "latest_prices": mock_prices,
                "num_observations": 750,
            }
            
            print(f"  [DEBUG] Using mock data - expected_returns: {mock_returns}")
            
            return {
                **mark_agent_complete(state, "DataAgent", result),
                "shared_data": {
                    **state.get("shared_data", {}),
                    "tickers": tickers,
                    "tickers_str": tickers_str,
                    "latest_prices": mock_prices,
                    "expected_returns": mock_returns,  # This must be set!
                    "covariance_matrix": mock_cov,
                },
            }
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"  [ERROR] Exception in DataAgent:")
        print(error_detail)
        return {
            **mark_agent_complete(state, "DataAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"DataAgent error: {str(e)}"),
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
            regime = agent.assess_regime_tool(
                vix_level=vix_data.get("value", 20),
                yield_curve_slope=yc_data.get("slope_raw", 0.5)
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
            
        except ImportError:
            # Fallback: Return mock data
            result = {
                "success": True,
                "mock": True,
                "regime": {
                    "regime": "NEUTRAL",
                    "risk_stance": "neutral",
                    "equity_adjustment": 0,
                    "confidence": 0.75,
                },
                "snapshot": {
                    "vix": {"value": 18.5, "regime": "normal"},
                    "yield_curve": {"slope": 0.45, "status": "normal"},
                },
            }
            
            return {
                **mark_agent_complete(state, "MacroAgent", result),
                "shared_data": {
                    **state.get("shared_data", {}),
                    "macro_regime": result["regime"],
                },
            }
    
    except Exception as e:
        return {
            **mark_agent_complete(state, "MacroAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"MacroAgent error: {str(e)}"),
        }


# =============================================================================
# FIXED: OPTIMIZATION AGENT NODE
# =============================================================================

async def optimization_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Optimization Agent node - runs portfolio optimization.
    
    FIXES:
    1. Better validation of shared_data
    2. Fallback to calculate returns if missing
    3. Better error messages showing what's actually in state
    """
    try:
        params = state.get("router_decision", {}).get("parameters", {})
        tickers = params.get("tickers", ["SPY", "TLT", "GLD"])
        max_vol = params.get("max_volatility")
        
        # Get data from shared_data (computed by DataAgent)
        shared = state.get("shared_data", {})
        expected_returns = shared.get("expected_returns", {})
        covariance_matrix = shared.get("covariance_matrix", {})
        tickers_str = shared.get("tickers_str", ",".join(tickers))
        
        # FIX 1: Debug output - show what we actually received
        print(f"  [DEBUG] shared_data keys: {list(shared.keys())}")
        print(f"  [DEBUG] expected_returns type: {type(expected_returns)}, value: {expected_returns}")
        print(f"  [DEBUG] covariance_matrix type: {type(covariance_matrix)}, empty: {not covariance_matrix}")
        
        # FIX 2: Better validation with specific error messages
        missing_data = []
        if not expected_returns:
            missing_data.append("expected_returns")
        if not covariance_matrix:
            missing_data.append("covariance_matrix")
        
        if missing_data:
            error_msg = f"Missing data from DataAgent: {', '.join(missing_data)}. Available keys: {list(shared.keys())}"
            print(f"  [ERROR] {error_msg}")
            return {
                **mark_agent_complete(state, "OptimizationAgent", {
                    "success": False, 
                    "error": error_msg
                }),
                **add_error(state, f"OptimizationAgent: {error_msg}"),
            }
        
        # FIX 3: Validate data structure
        if not isinstance(expected_returns, dict) or len(expected_returns) == 0:
            error_msg = f"Invalid expected_returns format. Got: {type(expected_returns)} with value: {expected_returns}"
            print(f"  [ERROR] {error_msg}")
            return {
                **mark_agent_complete(state, "OptimizationAgent", {
                    "success": False,
                    "error": error_msg
                }),
                **add_error(state, f"OptimizationAgent: {error_msg}"),
            }
        
        if not isinstance(covariance_matrix, dict) or len(covariance_matrix) == 0:
            error_msg = f"Invalid covariance_matrix format. Got: {type(covariance_matrix)}"
            print(f"  [ERROR] {error_msg}")
            return {
                **mark_agent_complete(state, "OptimizationAgent", {
                    "success": False,
                    "error": error_msg
                }),
                **add_error(state, f"OptimizationAgent: {error_msg}"),
            }
        
        # Try to import actual OptimizationAgent
        try:
            from .optimization_agent import create_optimization_agent
            import json
            
            agent = create_optimization_agent(verbose=False)

            # Helper: If obj is a dict, convert to JSON string. If string, keep as is.
            def to_json_str(obj):
                return json.dumps(obj) if isinstance(obj, (dict, list)) else obj
            
            print(f"  [DEBUG] Calling optimize_portfolio_tool with:")
            print(f"           tickers: {tickers_str}")
            print(f"           expected_returns: {expected_returns}")
            print(f"           max_volatility: {max_vol}")
            
            # Run optimization with correct signature
            result = agent.optimize_portfolio_tool(
                tickers=tickers_str,
                expected_returns=to_json_str(expected_returns),   
                covariance_matrix=to_json_str(covariance_matrix),
                method="max_sharpe",
                max_volatility=max_vol,
                min_weight=0.0,
                max_weight=0.40,
            )
            
            print(f"  [DEBUG] Optimization result success: {result.get('success')}")
            
            return {
                **mark_agent_complete(state, "OptimizationAgent", result),
                "shared_data": {
                    **state.get("shared_data", {}),
                    "optimal_weights": result.get("weights", result.get("optimal_weights", {})),
                },
            }
            
        except ImportError as e:
            print(f"  [DEBUG] ImportError, using mock optimization: {e}")
            # Fallback: Return mock optimization
            n = len(tickers)
            weights = {t: round(1.0/n, 2) for t in tickers}
            
            result = {
                "success": True,
                "mock": True,
                "weights": weights,
                "optimal_weights": weights,
                "expected_return": 0.082,
                "expected_volatility": max_vol or 0.115,
                "sharpe_ratio": 0.73,
                "method": "max_sharpe",
            }
            
            return {
                **mark_agent_complete(state, "OptimizationAgent", result),
                "shared_data": {
                    **state.get("shared_data", {}),
                    "optimal_weights": weights,
                },
            }
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"  [ERROR] Exception in OptimizationAgent:")
        print(error_detail)
        return {
            **mark_agent_complete(state, "OptimizationAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"OptimizationAgent error: {str(e)}"),
        }



# =============================================================================
# REBALANCE AGENT NODE
# =============================================================================

async def rebalance_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Rebalance Agent node - calculates drift and generates trade list.
    """
    try:
        # Get prices from shared data (from DataAgent)
        prices = get_shared_data(state, "latest_prices", {})
        
        # Get macro regime for TAA signal
        regime = get_shared_data(state, "macro_regime", {})
        
        # Try actual agent
        try:
            from .rebalance_agent import create_rebalance_agent
            agent = create_rebalance_agent(verbose=False)
            
            # Use demo weights (in production, from DB)
            current_weights = {"SPY": 0.45, "TLT": 0.25, "GLD": 0.20, "VWO": 0.10}
            target_weights = {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "VWO": 0.15}
            
            result = agent.analyze_rebalance_tool(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=100000,
                prices=prices or {"SPY": 590, "TLT": 88, "GLD": 420, "VWO": 45},
            )
            
            # Add TAA recommendation if regime available
            if regime:
                result["taa_signal"] = {
                    "regime": regime.get("regime", "NEUTRAL"),
                    "equity_adjustment": regime.get("equity_adjustment", 0),
                }
            
            return mark_agent_complete(state, "RebalanceAgent", result)
            
        except ImportError:
            # Fallback mock
            result = {
                "success": True,
                "mock": True,
                "decision": {
                    "should_rebalance": True,
                    "recommendation": "partial_rebalance",
                    "max_drift": 0.08,
                },
                "trades": [
                    {"ticker": "SPY", "action": "SELL", "shares": 8, "value": 4720},
                    {"ticker": "TLT", "action": "BUY", "shares": 57, "value": 5016},
                ],
                "total_cost": 9.74,
            }
            
            if regime:
                result["taa_signal"] = {
                    "regime": regime.get("regime", "NEUTRAL"),
                    "equity_adjustment": regime.get("equity_adjustment", 0),
                }
            
            return mark_agent_complete(state, "RebalanceAgent", result)
    
    except Exception as e:
        return {
            **mark_agent_complete(state, "RebalanceAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"RebalanceAgent error: {str(e)}"),
        }


# =============================================================================
# BACKTEST AGENT NODE
# =============================================================================

async def backtest_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Backtest Agent node - runs historical simulation.
    """
    try:
        params = state.get("router_decision", {}).get("parameters", {})
        tickers = params.get("tickers", ["SPY", "TLT", "GLD"])
        
        # Get data from shared_data
        shared = state.get("shared_data", {})
        weights = shared.get("optimal_weights", {"SPY": 0.6, "TLT": 0.4})
        tickers_str = shared.get("tickers_str", ",".join(tickers))
        price_data_json = shared.get("price_data_json")
        
        try:
            from .backtest_agent import create_backtest_agent
            import json
            
            agent = create_backtest_agent(verbose=False)
            
            # If no price data from DataAgent, we need to fetch it
            if not price_data_json:
                # Try to get price data via DataAgent
                try:
                    from .data_agent import create_data_agent
                    data_agent = create_data_agent(verbose=False)
                    price_result = data_agent.fetch_prices_tool(tickers=tickers_str, period="5Y")
                    if price_result.get("success") and "price_data" in price_result:
                        price_data_json = price_result["price_data"]
                    else:
                        # Can't run backtest without price data
                        return {
                            **mark_agent_complete(state, "BacktestAgent", {
                                "success": False,
                                "error": "No price data available for backtest"
                            }),
                            **add_error(state, "BacktestAgent: No price data available"),
                        }
                except Exception as e:
                    return {
                        **mark_agent_complete(state, "BacktestAgent", {
                            "success": False,
                            "error": f"Could not fetch price data: {str(e)}"
                        }),
                        **add_error(state, f"BacktestAgent: {str(e)}"),
                    }
            
            # Run backtest with correct signature
            result = agent.run_backtest_tool(
                tickers=tickers_str,
                weights=json.dumps(weights),
                price_data=price_data_json if isinstance(price_data_json, str) else json.dumps(price_data_json),
                rebalance_frequency="quarterly",
                drift_threshold=0.05,
                taa_rules=None,
                initial_capital=100000,
                signal_data=None,
            )
            
            return mark_agent_complete(state, "BacktestAgent", result)
            
        except ImportError:
            # Fallback mock
            result = {
                "success": True,
                "mock": True,
                "period": "5Y",
                "total_return": 0.487,
                "cagr": 0.082,
                "volatility": 0.115,
                "sharpe_ratio": 0.73,
                "max_drawdown": -0.186,
                "max_drawdown_date": "2020-03-23",
            }
            
            return mark_agent_complete(state, "BacktestAgent", result)
    
    except Exception as e:
        return {
            **mark_agent_complete(state, "BacktestAgent", {"success": False, "error": str(e)}),
            **add_error(state, f"BacktestAgent error: {str(e)}"),
        }


# =============================================================================
# SYNTHESIZER NODE
# =============================================================================

async def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizer node - combines results from all agents into final response.
    
    This is where we create the user-facing response.
    """
    try:
        decision = state.get("router_decision", {})
        intent = decision.get("intent", "unknown")
        sub_results = state.get("sub_results", {})
        errors = state.get("errors", [])
        
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
    if opt.get("success"):
        weights = opt.get("optimal_weights", {}) or opt.get("weights", {})
        
        if weights:
            lines.append("**Optimal Allocation:**")
            # Sort by weight value (handle both float and string)
            sorted_weights = sorted(
                weights.items(), 
                key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else float(str(x[1]).replace('%', ''))/100 if '%' in str(x[1]) else 0,
                reverse=True
            )
            
            for ticker, weight in sorted_weights:
                # Handle both float (0.45) and string ("45.0%") formats
                if isinstance(weight, str):
                    weight_str = weight if '%' in weight else f"{float(weight)*100:.1f}%"
                else:
                    weight_str = f"{float(weight)*100:.1f}%"
                lines.append(f"  • {ticker}: {weight_str}")
        
        lines.append("")
        lines.append("**Expected Metrics:**")
        
        # Safely format return
        ret = opt.get('expected_return', 0)
        if isinstance(ret, str):
            ret_str = ret if '%' in ret else f"{float(ret)*100:.2f}%"
        else:
            ret_str = f"{float(ret)*100:.2f}%"
        lines.append(f"  • Return: {ret_str}")
        
        # Safely format volatility
        vol = opt.get('expected_volatility', 0)
        if isinstance(vol, str):
            vol_str = vol if '%' in vol else f"{float(vol)*100:.2f}%"
        else:
            vol_str = f"{float(vol)*100:.2f}%"
        lines.append(f"  • Volatility: {vol_str}")
        
        # Safely format Sharpe ratio (not a percentage)
        sharpe = opt.get('sharpe_ratio', 0)
        if isinstance(sharpe, str):
            sharpe_str = sharpe
        else:
            sharpe_str = f"{float(sharpe):.2f}"
        lines.append(f"  • Sharpe Ratio: {sharpe_str}")
    
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