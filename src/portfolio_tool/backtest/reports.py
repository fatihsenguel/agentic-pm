"""
Report Generation for Backtesting.

Generates formatted reports and comparisons from backtest results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from .engine import BacktestResult


@dataclass
class BacktestReport:
    """Complete backtest report."""
    
    result: BacktestResult
    
    # Generated content
    summary: str
    monthly_returns: pd.DataFrame
    annual_returns: pd.Series
    drawdown_analysis: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": self.result.to_dict(),
            "monthly_returns": self.monthly_returns.to_dict() if self.monthly_returns is not None else None,
            "annual_returns": self.annual_returns.to_dict() if self.annual_returns is not None else None,
            "drawdown_analysis": self.drawdown_analysis,
        }


def generate_performance_summary(result: BacktestResult) -> str:
    """
    Generate a formatted performance summary.
    
    Args:
        result: BacktestResult from backtest
        
    Returns:
        Formatted string summary
    """
    lines = [
        "=" * 60,
        f"BACKTEST REPORT: {result.strategy_name}",
        "=" * 60,
        "",
        f"Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}",
        f"Duration: {result.trading_days} trading days ({result.trading_days/252:.1f} years)",
        "",
        "PERFORMANCE SUMMARY",
        "-" * 40,
        f"  Total Return:     {result.total_return:>12.2%}",
        f"  CAGR:             {result.cagr:>12.2%}",
        f"  Volatility:       {result.volatility:>12.2%}",
        "",
        "RISK-ADJUSTED METRICS",
        "-" * 40,
        f"  Sharpe Ratio:     {result.sharpe_ratio:>12.2f}",
        f"  Sortino Ratio:    {result.sortino_ratio:>12.2f}",
        f"  Calmar Ratio:     {result.calmar_ratio:>12.2f}",
        "",
        "RISK METRICS",
        "-" * 40,
        f"  Max Drawdown:     {result.max_drawdown:>12.2%}",
        f"  VaR (95%):        {result.var_95:>12.2%}",
        f"  CVaR (95%):       {result.cvar_95:>12.2%}",
        "",
        "RETURN DISTRIBUTION",
        "-" * 40,
        f"  Win Rate:         {result.win_rate:>12.1%}",
        f"  Best Day:         {result.best_day:>12.2%}",
        f"  Worst Day:        {result.worst_day:>12.2%}",
        "",
        "TRADING ACTIVITY",
        "-" * 40,
        f"  Total Trades:     {result.total_trades:>12}",
        f"  Annual Turnover:  {result.turnover:>12.1%}",
        f"  Total Costs:      ${result.total_transaction_costs:>11.2f}",
    ]
    
    # Benchmark comparison
    if result.benchmark_return is not None:
        lines.extend([
            "",
            "VS BENCHMARK",
            "-" * 40,
            f"  Benchmark Return: {result.benchmark_return:>12.2%}",
            f"  Alpha:            {result.alpha:>12.2%}" if result.alpha else "",
            f"  Beta:             {result.beta:>12.2f}" if result.beta else "",
        ])
    
    # TAA analysis
    if result.taa_triggers and any(v > 0 for v in result.taa_triggers.values()):
        lines.extend([
            "",
            "TAA RULE TRIGGERS",
            "-" * 40,
        ])
        for rule, count in result.taa_triggers.items():
            if count > 0:
                lines.append(f"  {rule}: {count} times")
        lines.append(f"  Time in TAA mode: {result.time_in_taa:>8.1%}")
    
    lines.extend([
        "",
        "=" * 60,
    ])
    
    return "\n".join(lines)


def generate_monthly_returns_table(result: BacktestResult) -> pd.DataFrame:
    """
    Generate monthly returns table.
    
    Returns DataFrame with years as rows, months as columns.
    """
    # Resample to monthly returns
    monthly = result.daily_values.resample('M').last()
    monthly_returns = monthly.pct_change().dropna()
    
    # Create pivot table
    df = pd.DataFrame({
        'year': monthly_returns.index.year,
        'month': monthly_returns.index.month,
        'return': monthly_returns.values
    })
    
    pivot = df.pivot(index='year', columns='month', values='return')
    pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.columns)]
    
    # Add annual return column
    annual = result.daily_values.resample('Y').last().pct_change().dropna()
    annual.index = annual.index.year
    pivot['Annual'] = annual
    
    return pivot


def generate_annual_returns(result: BacktestResult) -> pd.Series:
    """Generate annual returns series."""
    annual = result.daily_values.resample('Y').last()
    annual_returns = annual.pct_change().dropna()
    annual_returns.index = annual_returns.index.year
    return annual_returns


def analyze_drawdowns(result: BacktestResult, top_n: int = 5) -> Dict[str, Any]:
    """
    Analyze drawdown periods.
    
    Returns info about top N drawdowns.
    """
    drawdown = result.drawdown_series
    
    # Find drawdown periods
    in_drawdown = drawdown < 0
    
    # Identify separate drawdown periods
    drawdown_periods = []
    start_idx = None
    
    for i, (date, dd) in enumerate(drawdown.items()):
        if dd < 0 and start_idx is None:
            start_idx = i
        elif dd >= 0 and start_idx is not None:
            # End of drawdown period
            period_dd = drawdown.iloc[start_idx:i]
            max_dd_idx = period_dd.idxmin()
            
            drawdown_periods.append({
                'start': drawdown.index[start_idx],
                'trough': max_dd_idx,
                'end': date,
                'max_drawdown': abs(period_dd.min()),
                'duration_days': (date - drawdown.index[start_idx]).days,
                'recovery_days': (date - max_dd_idx).days if max_dd_idx else 0
            })
            start_idx = None
    
    # Handle ongoing drawdown
    if start_idx is not None:
        period_dd = drawdown.iloc[start_idx:]
        max_dd_idx = period_dd.idxmin()
        drawdown_periods.append({
            'start': drawdown.index[start_idx],
            'trough': max_dd_idx,
            'end': None,  # Ongoing
            'max_drawdown': abs(period_dd.min()),
            'duration_days': (drawdown.index[-1] - drawdown.index[start_idx]).days,
            'recovery_days': None
        })
    
    # Sort by max drawdown
    drawdown_periods.sort(key=lambda x: -x['max_drawdown'])
    
    return {
        'top_drawdowns': drawdown_periods[:top_n],
        'total_drawdown_periods': len(drawdown_periods),
        'avg_drawdown_duration': np.mean([d['duration_days'] for d in drawdown_periods]) if drawdown_periods else 0,
        'longest_drawdown': max([d['duration_days'] for d in drawdown_periods]) if drawdown_periods else 0,
    }


def compare_strategies(results: Dict[str, BacktestResult]) -> pd.DataFrame:
    """
    Compare multiple backtest results.
    
    Args:
        results: Dict of strategy_name -> BacktestResult
        
    Returns:
        DataFrame comparing all strategies
    """
    data = []
    
    for name, result in results.items():
        data.append({
            'Strategy': name,
            'Total Return': result.total_return,
            'CAGR': result.cagr,
            'Volatility': result.volatility,
            'Sharpe': result.sharpe_ratio,
            'Sortino': result.sortino_ratio,
            'Max DD': result.max_drawdown,
            'Calmar': result.calmar_ratio,
            'Win Rate': result.win_rate,
            'Trades': result.total_trades,
            'Turnover': result.turnover,
        })
    
    df = pd.DataFrame(data)
    df.set_index('Strategy', inplace=True)
    
    # Format percentages
    pct_cols = ['Total Return', 'CAGR', 'Volatility', 'Max DD', 'Win Rate', 'Turnover']
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2%}")
    
    # Format ratios
    ratio_cols = ['Sharpe', 'Sortino', 'Calmar']
    for col in ratio_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2f}")
    
    return df


def generate_full_report(result: BacktestResult) -> BacktestReport:
    """
    Generate complete backtest report.
    
    Args:
        result: BacktestResult
        
    Returns:
        BacktestReport with all analysis
    """
    return BacktestReport(
        result=result,
        summary=generate_performance_summary(result),
        monthly_returns=generate_monthly_returns_table(result),
        annual_returns=generate_annual_returns(result),
        drawdown_analysis=analyze_drawdowns(result),
    )


def format_comparison_table(results: Dict[str, BacktestResult]) -> str:
    """
    Format comparison table as string.
    
    Args:
        results: Dict of strategy_name -> BacktestResult
        
    Returns:
        Formatted comparison table
    """
    df = compare_strategies(results)
    
    lines = [
        "=" * 100,
        "STRATEGY COMPARISON",
        "=" * 100,
        "",
        df.to_string(),
        "",
        "=" * 100,
    ]
    
    # Add winner analysis
    if len(results) > 1:
        lines.append("")
        lines.append("WINNERS BY METRIC:")
        lines.append("-" * 40)
        
        metrics = {
            'Highest Return': 'total_return',
            'Best Sharpe': 'sharpe_ratio',
            'Lowest Volatility': 'volatility',
            'Smallest Drawdown': 'max_drawdown',
        }
        
        for label, attr in metrics.items():
            if attr in ['volatility', 'max_drawdown']:
                winner = min(results.items(), key=lambda x: getattr(x[1], attr))
            else:
                winner = max(results.items(), key=lambda x: getattr(x[1], attr))
            
            value = getattr(winner[1], attr)
            if attr in ['total_return', 'volatility', 'max_drawdown']:
                value_str = f"{value:.2%}"
            else:
                value_str = f"{value:.2f}"
            
            lines.append(f"  {label}: {winner[0]} ({value_str})")
    
    return "\n".join(lines)
