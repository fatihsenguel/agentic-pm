"""
Rebalance Agent for Quant Portfolio Manager.

The Rebalance Agent is responsible for:
- Analyzing portfolio drift
- Determining if rebalancing is needed
- Generating trade lists
- Estimating transaction costs and tax impact

⚠️ CRITICAL DESIGN PRINCIPLE:
All calculations are performed by rebalance_tools.py (pure math).
This agent is ONLY an interface - it does NOT perform calculations.
The LLM's role is to:
1. Understand user requests
2. Extract parameters
3. Call the appropriate tools
4. Format and explain the results

This separation ensures:
- Compliance / Audit requirements
- Reproducibility (same inputs = same outputs)
- Regulatory approval
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

import importlib
from config import config



class RebalanceAgent:
    """
    Rebalance Agent for portfolio rebalancing analysis.
    
    ⚠️ This agent uses rebalance_tools.py for ALL calculations.
    The agent itself does NOT perform any math.
    
    Capabilities:
    - analyze_rebalance: Full rebalancing analysis
    - calculate_drift: Portfolio drift calculation
    - generate_trades: Trade list generation
    - estimate_costs: Cost estimation
    """
    
    # ==================== TOOL METHODS ====================
    
    def analyze_rebalance_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float = 100000,
        prices: Optional[Dict[str, float]] = None,
        drift_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Perform complete rebalancing analysis.
        
        ⚠️ Delegates to rebalance_tools.py - NO calculations here.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target/optimal weights
            portfolio_value: Total portfolio value
            prices: Current prices (optional, uses defaults if not provided)
            drift_threshold: Custom drift threshold (optional)
        
        Returns:
            Complete rebalancing analysis
        """
        # Import the pure math module
        from portfolio_tool.tools.rebalance_tools import (
            analyze_rebalance,
            RebalanceConfig
        )
        
        # Use default prices if not provided
        if prices is None or not prices:
            # Get from data manager if possible
            try:
                from portfolio_tool.data_manager import get_data_manager
                from datetime import datetime
                
                dm = get_data_manager()
                prices = {}
                
                # Get specific tickers involved in the rebalance
                involved_tickers = set(current_weights.keys()) | set(target_weights.keys())
                
                # Fetch REAL prices from DB
                missing_prices = []
                for ticker in involved_tickers:
                    if ticker == "CASH":
                        prices[ticker] = 1.0
                        continue
                        
                    # ✅ STRICT: Get the actual latest price
                    latest_price = dm.get_latest_price(ticker)
                    if latest_price:
                        prices[ticker] = float(latest_price)
                    else:
                        missing_prices.append(ticker)
                
                # ✅ STRICT: Fail if data is missing
                if missing_prices:
                    raise ValueError(f"Cannot rebalance: Missing prices for {missing_prices}. Run DataAgent first.")
                    
            except Exception as e:
                # Don't mask the error with a placeholder
                return {
                    "success": False,
                    "error": f"Price data retrieval failed: {str(e)}"
                }
        
        # Configure
        rebalance_config = RebalanceConfig(
            drift_threshold_percent=drift_threshold or config.rebalance.default_drift_threshold,
            transaction_cost_bps=config.rebalance.default_transaction_cost_bps,
            capital_gains_rate=config.rebalance.capital_gains_rate,
        )
        
        # Delegate to pure math function
        try:
            result = analyze_rebalance(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                prices=prices,
                config=rebalance_config,
            )
            
            return {
                "success": True,
                **result.to_dict(),
                "summary": result.to_summary(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def calculate_drift_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Calculate portfolio drift only.
        
        Quick check without full trade generation.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
        
        Returns:
            Drift analysis
        """
        from portfolio_tool.tools.rebalance_tools import (
            calculate_drift,
            calculate_max_drift,
            should_rebalance
        )
        
        try:
            drift = calculate_drift(current_weights, target_weights)
            max_drift = calculate_max_drift(drift)
            should_reb, recommendation = should_rebalance(
                drift, 
                config.rebalance.default_drift_threshold
            )
            
            return {
                "success": True,
                "drift_by_asset": drift,
                "drift_formatted": {k: f"{v:+.2%}" for k, v in drift.items()},
                "max_drift": max_drift,
                "max_drift_formatted": f"{max_drift:.2%}",
                "threshold": config.rebalance.default_drift_threshold,
                "should_rebalance": should_reb,
                "recommendation": recommendation,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def generate_trades_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        prices: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Generate trade list to rebalance portfolio.
        
        Args:
            current_weights: Current weights
            target_weights: Target weights
            portfolio_value: Total portfolio value
            prices: Current prices per ticker
        
        Returns:
            Trade list with costs
        """
        from portfolio_tool.tools.rebalance_tools import (
            generate_trades,
            calculate_rebalance_costs,
            RebalanceConfig
        )
        
        try:
            config = RebalanceConfig(
                transaction_cost_bps=config.rebalance.default_transaction_cost_bps,
            )
            
            trades = generate_trades(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                prices=prices,
                config=config,
            )
            
            tx_cost, tax_cost, total_cost = calculate_rebalance_costs(trades)
            
            return {
                "success": True,
                "num_trades": len(trades),
                "trades": [t.to_dict() for t in trades],
                "total_trade_value": sum(abs(t.trade_value) for t in trades),
                "transaction_costs": tx_cost,
                "estimated_taxes": tax_cost,
                "total_costs": total_cost,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def quick_drift_check_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Quick one-line drift status check.
        
        Args:
            current_weights: Current weights
            target_weights: Target weights
        
        Returns:
            Simple status message
        """
        from portfolio_tool.tools.rebalance_tools import quick_drift_check
        
        try:
            message = quick_drift_check(
                current_weights=current_weights,
                target_weights=target_weights,
                threshold=config.rebalance.default_drift_threshold
            )
            
            return {
                "success": True,
                "status": message,
                "needs_attention": "REBALANCE NEEDED" in message,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# ==================== FACTORY FUNCTION ====================

def create_rebalance_agent() -> RebalanceAgent:
    """
    Factory function to create a Rebalance Agent.

    Returns:
        RebalanceAgent
    """
    return RebalanceAgent()
