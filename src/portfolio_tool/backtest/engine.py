"""
Backtest Engine - DETERMINISTIC Portfolio Simulation.

⚠️ CRITICAL: This module is 100% DETERMINISTIC.

The BacktestEngine:
- Takes a Strategy (pre-defined rules)
- Takes historical market data
- Simulates day-by-day portfolio evolution
- Returns performance metrics

The BacktestEngine NEVER:
- Calls an LLM
- Uses randomness
- Makes decisions based on anything other than pre-defined rules
- Accesses external data during the simulation

Same inputs = Same outputs. Always. Guaranteed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import pandas as pd
import numpy as np

from .strategies import Strategy, TAARule, RebalanceRule


@dataclass
class Trade:
    """Record of a single trade."""
    date: datetime
    asset: str
    shares_before: float
    shares_after: float
    price: float
    value: float
    cost: float  # Transaction cost
    reason: str  # "rebalance", "taa_rule", "initial"


@dataclass
class DailySnapshot:
    """Daily portfolio state snapshot."""
    date: datetime
    total_value: float
    cash: float
    positions: Dict[str, float]  # asset -> value
    weights: Dict[str, float]    # asset -> weight
    active_taa_rule: Optional[str] = None


@dataclass
class BacktestResult:
    """
    Complete backtest results.
    
    Contains:
    - Performance metrics (return, vol, Sharpe, etc.)
    - Daily portfolio values
    - Trade history
    - Drawdown analysis
    """
    
    # Strategy info
    strategy_name: str
    
    # Time period
    start_date: datetime
    end_date: datetime
    trading_days: int
    
    # Performance metrics
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Additional metrics
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR
    win_rate: float  # % of positive days
    best_day: float
    worst_day: float
    
    # Data series
    daily_values: pd.Series
    daily_returns: pd.Series
    drawdown_series: pd.Series
    
    # Trade analysis
    trades: List[Trade]
    total_trades: int
    total_transaction_costs: float
    turnover: float  # Annual turnover
    
    # TAA analysis
    taa_triggers: Dict[str, int]  # rule_name -> trigger count
    time_in_taa: float  # % of time TAA rules were active
    
    # Benchmark comparison (if available)
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy_name": self.strategy_name,
            "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
            "trading_days": self.trading_days,
            "total_return": f"{self.total_return:.2%}",
            "cagr": f"{self.cagr:.2%}",
            "volatility": f"{self.volatility:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "sortino_ratio": f"{self.sortino_ratio:.2f}",
            "max_drawdown": f"{self.max_drawdown:.2%}",
            "calmar_ratio": f"{self.calmar_ratio:.2f}",
            "var_95": f"{self.var_95:.2%}",
            "win_rate": f"{self.win_rate:.1%}",
            "total_trades": self.total_trades,
            "transaction_costs": f"{self.total_transaction_costs:.2f}",
            "annual_turnover": f"{self.turnover:.1%}",
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Backtest Results: {self.strategy_name}",
            "=" * 50,
            f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
            f"Trading Days: {self.trading_days}",
            "",
            "Performance Metrics:",
            f"  Total Return:    {self.total_return:>10.2%}",
            f"  CAGR:            {self.cagr:>10.2%}",
            f"  Volatility:      {self.volatility:>10.2%}",
            f"  Sharpe Ratio:    {self.sharpe_ratio:>10.2f}",
            f"  Sortino Ratio:   {self.sortino_ratio:>10.2f}",
            f"  Max Drawdown:    {self.max_drawdown:>10.2%}",
            f"  Calmar Ratio:    {self.calmar_ratio:>10.2f}",
            "",
            "Risk Metrics:",
            f"  VaR (95%):       {self.var_95:>10.2%}",
            f"  CVaR (95%):      {self.cvar_95:>10.2%}",
            f"  Best Day:        {self.best_day:>10.2%}",
            f"  Worst Day:       {self.worst_day:>10.2%}",
            f"  Win Rate:        {self.win_rate:>10.1%}",
            "",
            "Trading Activity:",
            f"  Total Trades:    {self.total_trades:>10}",
            f"  Annual Turnover: {self.turnover:>10.1%}",
            f"  Transaction Costs: ${self.total_transaction_costs:>7.2f}",
        ]
        
        if self.taa_triggers:
            lines.append("")
            lines.append("TAA Rule Triggers:")
            for rule, count in self.taa_triggers.items():
                lines.append(f"  {rule}: {count} times")
            lines.append(f"  Time in TAA: {self.time_in_taa:.1%}")
        
        if self.benchmark_return is not None:
            lines.extend([
                "",
                "vs Benchmark:",
                f"  Benchmark Return: {self.benchmark_return:>8.2%}",
                f"  Alpha:            {self.alpha:>8.2%}" if self.alpha else "",
                f"  Beta:             {self.beta:>8.2f}" if self.beta else "",
            ])
        
        return "\n".join(lines)


class Portfolio:
    """
    Portfolio state manager.
    
    Tracks:
    - Cash balance
    - Share positions
    - Current values and weights
    """
    
    def __init__(self, initial_capital: float, initial_weights: Dict[str, float]):
        """Initialize portfolio."""
        self.initial_capital = initial_capital
        self.target_weights = initial_weights.copy()
        
        self.cash = initial_capital
        self.shares: Dict[str, float] = {asset: 0.0 for asset in initial_weights}
        self.prices: Dict[str, float] = {}
        
        self.last_rebalance_date: Optional[datetime] = None
    
    @property
    def total_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(
            self.shares.get(asset, 0) * self.prices.get(asset, 0)
            for asset in self.shares
        )
        return self.cash + positions_value
    
    def get_weights(self) -> Dict[str, float]:
        """Calculate current weights."""
        total = self.total_value
        if total == 0:
            return {asset: 0.0 for asset in self.shares}
        
        weights = {}
        for asset in self.shares:
            value = self.shares[asset] * self.prices.get(asset, 0)
            weights[asset] = value / total
        
        # Cash weight
        weights["CASH"] = self.cash / total
        
        return weights
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update prices for mark-to-market."""
        self.prices.update(prices)
    
    def execute_trades(
        self,
        target_weights: Dict[str, float],
        prices: Dict[str, float],
        transaction_cost: float,
        date: datetime,
        reason: str
    ) -> List[Trade]:
        """
        Execute trades to reach target weights.
        
        Returns list of trades executed.
        """
        self.update_prices(prices)
        
        trades = []
        total_value = self.total_value
        
        # Calculate target values
        target_values = {
            asset: total_value * weight
            for asset, weight in target_weights.items()
            if asset != "CASH"
        }
        
        # Calculate current values
        current_values = {
            asset: self.shares.get(asset, 0) * prices.get(asset, 0)
            for asset in target_values
        }
        
        # Execute trades
        total_cost = 0.0
        
        for asset in target_values:
            if asset not in prices or prices[asset] <= 0:
                continue
            
            current_val = current_values.get(asset, 0)
            target_val = target_values[asset]
            
            if abs(target_val - current_val) < 1.0:  # Skip tiny trades
                continue
            
            # Calculate shares to trade
            current_shares = self.shares.get(asset, 0)
            target_shares = target_val / prices[asset]
            shares_delta = target_shares - current_shares
            
            # Transaction cost
            trade_value = abs(shares_delta * prices[asset])
            cost = trade_value * transaction_cost
            total_cost += cost
            
            # Record trade
            trades.append(Trade(
                date=date,
                asset=asset,
                shares_before=current_shares,
                shares_after=target_shares,
                price=prices[asset],
                value=trade_value,
                cost=cost,
                reason=reason
            ))
            
            # Update positions
            if asset not in self.shares:
                self.shares[asset] = 0.0
            
            # Adjust cash and shares
            self.cash -= shares_delta * prices[asset]
            self.shares[asset] = target_shares
        
        # Deduct transaction costs from cash
        self.cash -= total_cost
        
        self.last_rebalance_date = date
        
        return trades


class BacktestEngine:
    """
    DETERMINISTIC Backtest Engine.
    
    ⚠️ CRITICAL: This class MUST NOT use any LLM.
    All decisions are based on pre-defined rules in the Strategy.
    Same inputs = Same outputs. Always.
    
    Usage:
        engine = BacktestEngine(transaction_cost=0.001)
        result = engine.run(
            strategy=my_strategy,
            price_data=historical_prices,
            initial_capital=100_000
        )
    """
    
    def __init__(
        self,
        transaction_cost: float = 0.001,  # 10 bps
        risk_free_rate: float = 0.0
    ):
        """
        Initialize backtest engine.
        
        Args:
            transaction_cost: Cost per trade as fraction of trade value
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.transaction_cost = transaction_cost
        self.risk_free_rate = risk_free_rate
    
    def run(
        self,
        strategy: Strategy,
        price_data: pd.DataFrame,
        initial_capital: float = 100_000,
        signal_data: Optional[pd.DataFrame] = None
    ) -> BacktestResult:
        """
        Run backtest simulation.
        
        ⚠️ This method is DETERMINISTIC.
        Same strategy + Same data = Same result. Always.
        
        Args:
            strategy: Strategy to backtest
            price_data: DataFrame with asset prices (index=date, columns=tickers)
            initial_capital: Starting capital
            signal_data: Optional DataFrame with TAA signals (e.g., VIX)
            
        Returns:
            BacktestResult with full performance analysis
        """
        # Validate inputs
        if price_data.empty:
            raise ValueError("Price data is empty")
        
        # Ensure datetime index
        if not isinstance(price_data.index, pd.DatetimeIndex):
            price_data.index = pd.to_datetime(price_data.index)
        
        # Sort by date
        price_data = price_data.sort_index()
        
        # Merge signal data if provided
        if signal_data is not None:
            if not isinstance(signal_data.index, pd.DatetimeIndex):
                signal_data.index = pd.to_datetime(signal_data.index)
            market_data = price_data.join(signal_data, how='left')
        else:
            market_data = price_data.copy()
        
        # Initialize portfolio
        portfolio = Portfolio(initial_capital, strategy.initial_weights)
        
        # Storage for results
        daily_values = []
        snapshots = []
        all_trades = []
        taa_triggers = {rule.name: 0 for rule in strategy.taa_rules}
        taa_days = 0
        
        # Get dates
        dates = market_data.index.tolist()
        
        # Initial purchase
        first_date = dates[0]
        first_prices = self._get_prices(market_data.loc[first_date], strategy.assets)
        
        initial_trades = portfolio.execute_trades(
            strategy.initial_weights,
            first_prices,
            self.transaction_cost,
            first_date,
            "initial"
        )
        all_trades.extend(initial_trades)
        
        previous_data = None
        current_target_weights = strategy.initial_weights.copy()
        
        # Main simulation loop
        for date in dates:
            current_data = market_data.loc[date]
            prices = self._get_prices(current_data, strategy.assets)
            
            # Update portfolio values
            portfolio.update_prices(prices)
            
            # 1. Check TAA rules (DETERMINISTIC)
            new_weights, triggered_rule = strategy.get_target_weights(
                current_data, previous_data
            )
            
            if triggered_rule:
                taa_triggers[triggered_rule] += 1
                taa_days += 1
                
                # Execute TAA rebalance if weights changed
                if new_weights != current_target_weights:
                    taa_trades = portfolio.execute_trades(
                        new_weights,
                        prices,
                        self.transaction_cost,
                        date,
                        f"taa:{triggered_rule}"
                    )
                    all_trades.extend(taa_trades)
                    current_target_weights = new_weights
            
            else:
                # 2. Check regular rebalancing (DETERMINISTIC)
                should_rebal, reason = strategy.rebalance_rule.should_rebalance(
                    date,
                    portfolio.last_rebalance_date,
                    portfolio.get_weights(),
                    strategy.initial_weights
                )
                
                if should_rebal:
                    rebal_trades = portfolio.execute_trades(
                        strategy.initial_weights,
                        prices,
                        self.transaction_cost,
                        date,
                        f"rebalance:{reason}"
                    )
                    all_trades.extend(rebal_trades)
                    current_target_weights = strategy.initial_weights.copy()
            
            # Record daily value
            daily_values.append({
                "date": date,
                "value": portfolio.total_value,
                "taa_active": triggered_rule
            })
            
            previous_data = current_data
        
        # Build result
        return self._build_result(
            strategy=strategy,
            daily_values=daily_values,
            trades=all_trades,
            taa_triggers=taa_triggers,
            taa_days=taa_days,
            initial_capital=initial_capital,
            price_data=price_data
        )
    
    def _get_prices(self, row: pd.Series, assets: List[str]) -> Dict[str, float]:
        """Extract prices for assets from data row."""
        prices = {}
        for asset in assets:
            if asset in row.index and not pd.isna(row[asset]):
                prices[asset] = float(row[asset])
        return prices
    
    def _build_result(
        self,
        strategy: Strategy,
        daily_values: List[Dict],
        trades: List[Trade],
        taa_triggers: Dict[str, int],
        taa_days: int,
        initial_capital: float,
        price_data: pd.DataFrame
    ) -> BacktestResult:
        """Build BacktestResult from simulation data."""
        
        # Convert to series
        df = pd.DataFrame(daily_values)
        df.set_index("date", inplace=True)
        values = df["value"]
        
        # Calculate returns
        returns = values.pct_change().dropna()
        
        # Basic metrics
        total_return = (values.iloc[-1] / values.iloc[0]) - 1
        trading_days = len(values)
        years = trading_days / 252
        
        # CAGR
        cagr = (values.iloc[-1] / values.iloc[0]) ** (1 / years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe ratio
        excess_returns = returns - self.risk_free_rate / 252
        sharpe = (excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino = (returns.mean() * 252 - self.risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Calmar ratio
        calmar = cagr / max_drawdown if max_drawdown > 0 else 0
        
        # VaR and CVaR
        var_95 = abs(np.percentile(returns, 5))
        cvar_95 = abs(returns[returns <= -var_95].mean()) if len(returns[returns <= -var_95]) > 0 else var_95
        
        # Win rate
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        
        # Best/worst day
        best_day = returns.max() if len(returns) > 0 else 0
        worst_day = returns.min() if len(returns) > 0 else 0
        
        # Trading metrics
        total_trades = len(trades)
        total_costs = sum(t.cost for t in trades)
        
        # Turnover (simplified: sum of all trade values / average portfolio value / years)
        total_trade_value = sum(t.value for t in trades)
        avg_value = values.mean()
        turnover = (total_trade_value / avg_value / years) if years > 0 and avg_value > 0 else 0
        
        # Time in TAA
        time_in_taa = taa_days / trading_days if trading_days > 0 else 0
        
        # Benchmark comparison
        benchmark_return = None
        alpha = None
        beta = None
        
        if strategy.benchmark and strategy.benchmark in price_data.columns:
            bench = price_data[strategy.benchmark]
            bench_return = (bench.iloc[-1] / bench.iloc[0]) - 1
            benchmark_return = bench_return
            alpha = total_return - bench_return
            
            # Beta calculation
            bench_returns = bench.pct_change().dropna()
            if len(bench_returns) == len(returns):
                cov = np.cov(returns, bench_returns)[0, 1]
                bench_var = bench_returns.var()
                beta = cov / bench_var if bench_var > 0 else 1.0
        
        return BacktestResult(
            strategy_name=strategy.name,
            start_date=values.index[0],
            end_date=values.index[-1],
            trading_days=trading_days,
            total_return=total_return,
            cagr=cagr,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar,
            var_95=var_95,
            cvar_95=cvar_95,
            win_rate=win_rate,
            best_day=best_day,
            worst_day=worst_day,
            daily_values=values,
            daily_returns=returns,
            drawdown_series=drawdown,
            trades=trades,
            total_trades=total_trades,
            total_transaction_costs=total_costs,
            turnover=turnover,
            taa_triggers=taa_triggers,
            time_in_taa=time_in_taa,
            benchmark_return=benchmark_return,
            alpha=alpha,
            beta=beta,
        )
    
    def compare_strategies(
        self,
        strategies: List[Strategy],
        price_data: pd.DataFrame,
        initial_capital: float = 100_000,
        signal_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, BacktestResult]:
        """
        Run backtest for multiple strategies and compare.
        
        Returns dict of strategy_name -> BacktestResult
        """
        results = {}
        
        for strategy in strategies:
            result = self.run(strategy, price_data, initial_capital, signal_data)
            results[strategy.name] = result
        
        return results
