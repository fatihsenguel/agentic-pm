#!/usr/bin/env python3
"""
PM Decision Support System - Interview Demo v2
===============================================

A multi-agent system for institutional portfolio management with full
observability and real-time execution tracing.

Features:
- Real-time agent execution visualization
- LLM reasoning trace (why decisions were made)
- Dynamic data operations (fetch, update, validate)
- IPS compliance enforcement with step-by-step logic
- Factor attribution with methodology explanation

Usage:
    python pm_decision_system_demo_v2.py

Commands:
    /debug          Toggle debug mode (shows agent reasoning)
    /portfolio <id> Switch portfolio (1=Growth, 2=Dividend, 3=AllWeather)
    /trace          Show last execution trace summary
    /stats          Show session statistics
    /help           Show available commands
    exit            Quit

Author: [Your Name]
Version: 2.0.0
"""

import time
import random
import hashlib
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# =============================================================================
# CONSOLE STYLING (No emojis - professional output)
# =============================================================================

class Style:
    """ANSI escape codes for terminal styling."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        cls.HEADER = cls.BLUE = cls.CYAN = cls.GREEN = ''
        cls.YELLOW = cls.RED = cls.BOLD = cls.DIM = ''
        cls.UNDERLINE = cls.END = ''


# =============================================================================
# ENUMS
# =============================================================================

class QueryIntent(str, Enum):
    OPERATIONAL = "operational"
    INFORMATION = "information"
    ANALYSIS = "analysis"
    DECISION = "decision"


class ExecutionIntent(str, Enum):
    DATA_UPDATE = "data_update"
    OPTIMIZATION = "optimization"
    MACRO_ANALYSIS = "macro_analysis"
    REBALANCING = "rebalancing"
    RISK_ANALYSIS = "risk_analysis"
    DATA_FETCH = "data_fetch"
    PORTFOLIO_MGMT = "portfolio_mgmt"
    IPS_COMPLIANCE = "ips_compliance"
    FACTOR_ATTRIBUTION = "factor_attribution"
    STRESS_TEST = "stress_test"


class DecisionType(str, Enum):
    HOLD = "HOLD"
    TILT = "TILT"
    REBALANCE = "REBALANCE"
    HEDGE = "HEDGE"


class AgentType(str, Enum):
    ROUTER = "Router"
    PLANNER = "Planner"
    DATA = "DataAgent"
    MACRO = "MacroAgent"
    OPTIMIZATION = "OptimizationAgent"
    REBALANCE = "RebalanceAgent"
    RISK = "RiskAgent"
    RAG = "RAGAgent"
    IPS = "IPSAgent"
    FACTOR = "FactorAgent"
    STRESS = "StressAgent"
    DECISION = "DecisionEngine"
    SYNTHESIZER = "Synthesizer"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    
    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens
    
    @property
    def cost_usd(self) -> float:
        return (self.prompt_tokens * 0.000003) + (self.completion_tokens * 0.000015)


@dataclass
class AgentStep:
    agent: AgentType
    action: str
    reasoning: str
    tools: List[str] = field(default_factory=list)
    result: str = ""
    tokens: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionPlan:
    query: str
    query_intent: QueryIntent
    execution_intent: ExecutionIntent
    steps: List[str]
    reasoning: str
    agents_required: List[AgentType]


@dataclass
class Portfolio:
    id: int
    name: str
    holdings: Dict[str, float]
    target_weights: Dict[str, float]
    total_value: float
    ips_constraints: Dict


@dataclass 
class AssetData:
    ticker: str
    last_price: float
    last_price_date: datetime
    last_financials_date: Optional[datetime]
    pe_ratio: Optional[float]
    market_cap: Optional[float]
    sector: str


# =============================================================================
# SIMULATED DATA STORE
# =============================================================================

class DataStore:
    """Simulated database with data freshness tracking."""
    
    ASSETS = {
        "AAPL": AssetData("AAPL", 178.52, datetime(2026, 1, 20), datetime(2025, 9, 30), 28.5, 2.78e12, "Technology"),
        "MSFT": AssetData("MSFT", 378.91, datetime(2026, 1, 20), datetime(2025, 9, 30), 35.2, 2.81e12, "Technology"),
        "NVDA": AssetData("NVDA", 485.23, datetime(2026, 1, 20), datetime(2025, 10, 31), 65.3, 1.19e12, "Technology"),
        "GOOGL": AssetData("GOOGL", 142.65, datetime(2026, 1, 20), datetime(2025, 9, 30), 24.1, 1.78e12, "Technology"),
        "AMZN": AssetData("AMZN", 178.25, datetime(2026, 1, 20), datetime(2025, 9, 30), 62.4, 1.86e12, "Consumer"),
        "META": AssetData("META", 385.42, datetime(2026, 1, 20), datetime(2025, 9, 30), 23.8, 9.89e11, "Technology"),
        "JPM": AssetData("JPM", 182.35, datetime(2026, 1, 20), datetime(2025, 9, 30), 11.2, 5.28e11, "Financials"),
        "JNJ": AssetData("JNJ", 156.78, datetime(2026, 1, 20), datetime(2025, 9, 30), 15.8, 3.78e11, "Healthcare"),
        "BND": AssetData("BND", 72.45, datetime(2026, 1, 20), None, None, None, "Fixed Income"),
        "GLD": AssetData("GLD", 185.32, datetime(2026, 1, 20), None, None, None, "Commodities"),
        "TLT": AssetData("TLT", 92.18, datetime(2026, 1, 20), None, None, None, "Fixed Income"),
        "SPY": AssetData("SPY", 478.92, datetime(2026, 1, 20), None, None, None, "Equity Index"),
        "VZ": AssetData("VZ", 42.15, datetime(2026, 1, 20), datetime(2025, 9, 30), 9.2, 1.77e11, "Telecom"),
        "XOM": AssetData("XOM", 105.82, datetime(2026, 1, 20), datetime(2025, 9, 30), 13.5, 4.52e11, "Energy"),
    }
    
    PORTFOLIOS = {
        1: Portfolio(1, "Growth Tech Portfolio",
                    {"AAPL": 0.18, "MSFT": 0.16, "NVDA": 0.22, "GOOGL": 0.14, "AMZN": 0.12, "META": 0.10, "BND": 0.08},
                    {"AAPL": 0.15, "MSFT": 0.15, "NVDA": 0.20, "GOOGL": 0.15, "AMZN": 0.15, "META": 0.10, "BND": 0.10},
                    487650.00,
                    {"max_equity": 0.95, "max_single_position": 0.25, "min_positions": 5}),
        2: Portfolio(2, "Dividend Income Portfolio",
                    {"JNJ": 0.12, "VZ": 0.15, "JPM": 0.10, "XOM": 0.08, "BND": 0.25, "TLT": 0.15, "GLD": 0.15},
                    {"JNJ": 0.12, "VZ": 0.12, "JPM": 0.10, "XOM": 0.10, "BND": 0.23, "TLT": 0.18, "GLD": 0.15},
                    325000.00,
                    {"max_equity": 0.50, "max_single_position": 0.15, "min_positions": 6, "excluded_sectors": ["Tobacco", "Gambling"]}),
        3: Portfolio(3, "All-Weather Portfolio",
                    {"SPY": 0.30, "BND": 0.25, "GLD": 0.15, "TLT": 0.20, "AAPL": 0.10},
                    {"SPY": 0.30, "BND": 0.25, "GLD": 0.15, "TLT": 0.20, "AAPL": 0.10},
                    520000.00,
                    {"max_equity": 0.45, "max_single_position": 0.35, "max_volatility": 0.12}),
    }
    
    MACRO = {
        "vix": 18.45,
        "fed_funds": 5.25,
        "ten_year": 4.28,
        "two_year": 4.65,
        "spread": -0.37,
        "regime": "NEUTRAL"
    }


# =============================================================================
# DEBUG PRINTER
# =============================================================================

class DebugPrinter:
    """Handles real-time debug output with proper formatting."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.indent_level = 0
    
    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
    
    def _print(self, msg: str, style: str = ""):
        if self.enabled:
            indent = "    " * self.indent_level
            print(f"{style}{indent}{msg}{Style.END}")
            sys.stdout.flush()
    
    def section(self, title: str):
        if self.enabled:
            print(f"\n{Style.BOLD}{Style.CYAN}{'=' * 70}")
            print(f"  {title}")
            print(f"{'=' * 70}{Style.END}")
    
    def agent_start(self, agent: AgentType, action: str):
        if self.enabled:
            print(f"\n{Style.BOLD}[{agent.value}]{Style.END} {action}")
            self.indent_level = 1
    
    def agent_end(self, latency_ms: float, tokens: int):
        if self.enabled:
            self.indent_level = 0
            print(f"{Style.DIM}    Completed in {latency_ms:.0f}ms | {tokens} tokens{Style.END}")
    
    def reasoning(self, text: str):
        self._print(f"Reasoning: {text}", Style.YELLOW)
    
    def tool_call(self, tool: str, params: str = ""):
        if params:
            self._print(f"Tool: {tool}({params})", Style.BLUE)
        else:
            self._print(f"Tool: {tool}", Style.BLUE)
    
    def result(self, text: str):
        self._print(f"Result: {text}", Style.GREEN)
    
    def decision(self, text: str):
        self._print(f"Decision: {text}", Style.BOLD + Style.GREEN)
    
    def warning(self, text: str):
        self._print(f"Warning: {text}", Style.YELLOW)
    
    def error(self, text: str):
        self._print(f"Error: {text}", Style.RED)
    
    def step(self, num: int, text: str):
        self._print(f"Step {num}: {text}", "")
    
    def data(self, key: str, value: str):
        self._print(f"{key}: {value}", Style.DIM)
    
    def wait(self, ms: float):
        """Simulate processing with visible delay."""
        if self.enabled:
            time.sleep(ms / 1000)


# =============================================================================
# AGENT EXECUTOR
# =============================================================================

class AgentExecutor:
    """Executes agents with visible reasoning and tool calls."""
    
    def __init__(self, debug: DebugPrinter):
        self.debug = debug
        self.steps: List[AgentStep] = []
        self.total_tokens = TokenUsage()
    
    def reset(self):
        self.steps = []
        self.total_tokens = TokenUsage()
    
    def _simulate_llm(self, prompt_tokens: int, completion_tokens: int) -> TokenUsage:
        """Simulate LLM call with token tracking."""
        tokens = TokenUsage(
            prompt_tokens=int(prompt_tokens * random.uniform(0.9, 1.1)),
            completion_tokens=int(completion_tokens * random.uniform(0.9, 1.1))
        )
        self.total_tokens.prompt_tokens += tokens.prompt_tokens
        self.total_tokens.completion_tokens += tokens.completion_tokens
        return tokens
    
    def execute_router(self, query: str) -> ExecutionPlan:
        """Router agent: Classifies intent and creates execution plan."""
        start = time.time()
        self.debug.agent_start(AgentType.ROUTER, "Analyzing query intent")
        
        self.debug.reasoning("Parsing user query to determine intent and required agents")
        self.debug.wait(200)
        
        self.debug.tool_call("intent_classifier", f"query='{query[:40]}...'")
        self.debug.wait(150)
        
        # Classify query
        query_lower = query.lower()
        
        # Determine intents
        if any(kw in query_lower for kw in ["latest data", "update", "refresh", "fetch data"]):
            query_intent = QueryIntent.OPERATIONAL
            exec_intent = ExecutionIntent.DATA_UPDATE
            agents = [AgentType.PLANNER, AgentType.DATA]
            reasoning = "User requesting data refresh operation - need to check data freshness and update"
            steps = ["Check current data timestamps", "Identify stale data", "Fetch updates from providers", "Validate and store"]
            
        elif any(kw in query_lower for kw in ["ips", "compliance", "mandate", "constraint", "aggressive"]):
            query_intent = QueryIntent.DECISION
            exec_intent = ExecutionIntent.IPS_COMPLIANCE
            agents = [AgentType.PLANNER, AgentType.IPS, AgentType.DATA, AgentType.OPTIMIZATION, AgentType.DECISION]
            reasoning = "Compliance check requested - need to validate against IPS constraints before any action"
            steps = ["Load IPS constraints", "Analyze proposed allocation", "Check constraint violations", "Generate compliant alternative if needed"]
            
        elif any(kw in query_lower for kw in ["why", "underperform", "attribution", "factor", "breakdown"]):
            query_intent = QueryIntent.ANALYSIS
            exec_intent = ExecutionIntent.FACTOR_ATTRIBUTION
            agents = [AgentType.PLANNER, AgentType.DATA, AgentType.FACTOR, AgentType.RAG, AgentType.DECISION]
            reasoning = "Performance attribution requested - need factor decomposition and document analysis"
            steps = ["Fetch portfolio returns", "Calculate factor exposures", "Run Brinson attribution", "Search for relevant news", "Synthesize findings"]
            
        elif any(kw in query_lower for kw in ["stress", "what if", "scenario", "crash", "rates rise"]):
            query_intent = QueryIntent.ANALYSIS
            exec_intent = ExecutionIntent.STRESS_TEST
            agents = [AgentType.PLANNER, AgentType.DATA, AgentType.STRESS, AgentType.DECISION]
            reasoning = "Stress test requested - need to apply shocks and measure portfolio impact"
            steps = ["Parse scenario parameters", "Calculate position sensitivities", "Apply stress shocks", "Aggregate portfolio impact"]
            
        elif any(kw in query_lower for kw in ["rebalance", "should i", "optimize"]):
            query_intent = QueryIntent.DECISION
            exec_intent = ExecutionIntent.REBALANCING
            agents = [AgentType.PLANNER, AgentType.DATA, AgentType.MACRO, AgentType.REBALANCE, AgentType.RISK, AgentType.DECISION]
            reasoning = "Rebalancing decision requested - need full risk assessment before recommending action"
            steps = ["Fetch current holdings", "Check macro environment", "Calculate drift", "Assess risk", "Determine if action needed"]
            
        elif any(kw in query_lower for kw in ["vix", "macro", "rate", "yield", "environment"]):
            query_intent = QueryIntent.INFORMATION
            exec_intent = ExecutionIntent.MACRO_ANALYSIS
            agents = [AgentType.MACRO]
            reasoning = "Macro information requested - straightforward data fetch"
            steps = ["Fetch current macro indicators", "Format response"]
            
        else:
            query_intent = QueryIntent.INFORMATION
            exec_intent = ExecutionIntent.DATA_FETCH
            agents = [AgentType.DATA]
            reasoning = "General information query - fetch requested data"
            steps = ["Identify data requested", "Query database", "Format response"]
        
        self.debug.result(f"QueryIntent={query_intent.value}, ExecutionIntent={exec_intent.value}")
        self.debug.data("Agents required", ", ".join(a.value for a in agents))
        
        tokens = self._simulate_llm(180, 120)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return ExecutionPlan(
            query=query,
            query_intent=query_intent,
            execution_intent=exec_intent,
            steps=steps,
            reasoning=reasoning,
            agents_required=agents
        )
    
    def execute_planner(self, plan: ExecutionPlan) -> List[str]:
        """Planner agent: Creates detailed execution steps."""
        start = time.time()
        self.debug.agent_start(AgentType.PLANNER, "Creating execution plan")
        
        self.debug.reasoning(plan.reasoning)
        self.debug.wait(150)
        
        self.debug.tool_call("plan_generator", f"intent={plan.execution_intent.value}")
        self.debug.wait(100)
        
        for i, step in enumerate(plan.steps, 1):
            self.debug.step(i, step)
            self.debug.wait(50)
        
        tokens = self._simulate_llm(150, 100)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return plan.steps
    
    def execute_data_update(self, ticker: str) -> Dict:
        """DataAgent: Check and update data for a ticker."""
        start = time.time()
        self.debug.agent_start(AgentType.DATA, f"Checking data freshness for {ticker}")
        
        asset = DataStore.ASSETS.get(ticker)
        if not asset:
            self.debug.error(f"Ticker {ticker} not found in database")
            return {"error": f"Unknown ticker: {ticker}"}
        
        today = datetime(2026, 1, 27)
        
        # Check price data freshness
        self.debug.tool_call("db_query", f"SELECT last_price_date FROM assets WHERE ticker='{ticker}'")
        self.debug.wait(100)
        
        price_age = (today - asset.last_price_date).days
        self.debug.result(f"Last price date: {asset.last_price_date.strftime('%Y-%m-%d')} ({price_age} days old)")
        
        # Check financials freshness
        self.debug.tool_call("db_query", f"SELECT last_financials_date FROM assets WHERE ticker='{ticker}'")
        self.debug.wait(100)
        
        updates_needed = []
        
        if price_age > 1:
            self.debug.warning(f"Price data is {price_age} days stale - update required")
            updates_needed.append("price_data")
        
        if asset.last_financials_date:
            fin_age = (today - asset.last_financials_date).days
            self.debug.result(f"Last financials: {asset.last_financials_date.strftime('%Y-%m-%d')} ({fin_age} days old)")
            
            # Check if new quarter available
            if fin_age > 95:  # More than a quarter
                self.debug.warning(f"Financial statements are {fin_age} days old - Q4 2025 likely available")
                updates_needed.append("financial_statements")
        else:
            self.debug.data("Financials", "N/A for this asset type")
        
        # Perform updates
        results = {"ticker": ticker, "updates": []}
        
        if "price_data" in updates_needed:
            self.debug.reasoning("Price data stale - fetching from YFinance provider")
            self.debug.tool_call("yfinance_provider.fetch_prices", f"ticker={ticker}, start={asset.last_price_date.strftime('%Y-%m-%d')}")
            self.debug.wait(300)
            
            # Simulate update
            new_price = asset.last_price * random.uniform(0.98, 1.02)
            self.debug.result(f"Fetched {price_age} days of price data")
            self.debug.tool_call("db_insert", f"daily_prices: {price_age} rows")
            self.debug.wait(100)
            results["updates"].append({
                "type": "price_data",
                "rows_added": price_age,
                "latest_price": round(new_price, 2),
                "date_range": f"{asset.last_price_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
            })
        
        if "financial_statements" in updates_needed:
            self.debug.reasoning("Q4 2025 financials likely available - checking SEC EDGAR")
            self.debug.tool_call("sec_edgar_provider.fetch_10q", f"ticker={ticker}, quarter='Q4 2025'")
            self.debug.wait(400)
            
            self.debug.result("Found 10-Q filing dated 2025-12-15")
            self.debug.tool_call("db_insert", "financial_statements: income_statement, balance_sheet, cash_flow")
            self.debug.wait(150)
            results["updates"].append({
                "type": "financial_statements",
                "filing_type": "10-Q",
                "period": "Q4 2025",
                "filing_date": "2025-12-15"
            })
        
        if not updates_needed:
            self.debug.result("All data is current - no updates required")
            results["status"] = "current"
        else:
            results["status"] = "updated"
        
        tokens = self._simulate_llm(250, 350)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return results
    
    def execute_ips_check(self, portfolio: Portfolio, proposed_action: str) -> Dict:
        """IPSAgent: Check compliance with Investment Policy Statement."""
        start = time.time()
        self.debug.agent_start(AgentType.IPS, "Loading IPS constraints")
        
        ips = portfolio.ips_constraints
        
        self.debug.tool_call("db_query", f"SELECT * FROM ips_mandates WHERE portfolio_id={portfolio.id}")
        self.debug.wait(100)
        
        self.debug.result(f"Loaded {len(ips)} active constraints")
        for key, value in ips.items():
            self.debug.data(key, str(value))
        
        self.debug.wait(100)
        
        # Parse proposed action
        self.debug.agent_start(AgentType.IPS, "Analyzing proposed allocation")
        self.debug.reasoning("Extracting target allocation from user request")
        
        # Determine proposed equity exposure
        proposed_equity = 0.85 if "85%" in proposed_action or "aggressive" in proposed_action.lower() else 0.70
        
        self.debug.tool_call("allocation_parser", f"text='{proposed_action[:30]}...'")
        self.debug.wait(150)
        self.debug.result(f"Proposed equity exposure: {proposed_equity:.0%}")
        
        # Check constraints
        self.debug.agent_start(AgentType.IPS, "Validating against constraints")
        
        violations = []
        
        # Equity limit check
        max_equity = ips.get("max_equity", 1.0)
        self.debug.tool_call("constraint_check", f"equity_exposure <= {max_equity:.0%}")
        self.debug.wait(100)
        
        if proposed_equity > max_equity:
            self.debug.error(f"VIOLATION: Proposed {proposed_equity:.0%} exceeds limit {max_equity:.0%}")
            violations.append({
                "type": "EQUITY_LIMIT_BREACH",
                "proposed": proposed_equity,
                "limit": max_equity,
                "severity": "HARD_REJECT"
            })
        else:
            self.debug.result(f"PASS: {proposed_equity:.0%} <= {max_equity:.0%}")
        
        # Position concentration check
        max_position = ips.get("max_single_position", 1.0)
        current_max = max(portfolio.holdings.values())
        max_ticker = max(portfolio.holdings, key=portfolio.holdings.get)
        
        self.debug.tool_call("constraint_check", f"max_position <= {max_position:.0%}")
        self.debug.wait(100)
        
        if current_max > max_position:
            self.debug.warning(f"WARNING: {max_ticker} at {current_max:.0%} exceeds {max_position:.0%}")
            violations.append({
                "type": "CONCENTRATION_BREACH",
                "ticker": max_ticker,
                "current": current_max,
                "limit": max_position,
                "severity": "SOFT_WARNING"
            })
        else:
            self.debug.result(f"PASS: Max position {current_max:.0%} <= {max_position:.0%}")
        
        # Excluded sectors check
        excluded = ips.get("excluded_sectors", [])
        if excluded:
            self.debug.tool_call("sector_screen", f"excluded={excluded}")
            self.debug.wait(100)
            self.debug.result("No excluded sectors in portfolio")
        
        tokens = self._simulate_llm(300, 400)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {
            "compliant": len([v for v in violations if v["severity"] == "HARD_REJECT"]) == 0,
            "violations": violations,
            "constraints_checked": len(ips),
            "max_equity": max_equity
        }
    
    def execute_optimization(self, portfolio: Portfolio, max_equity: float) -> Dict:
        """OptimizationAgent: Generate compliant alternative allocation."""
        start = time.time()
        self.debug.agent_start(AgentType.OPTIMIZATION, "Generating compliant alternative")
        
        self.debug.reasoning(f"User wants aggressive tech exposure but limited to {max_equity:.0%} equity")
        self.debug.wait(100)
        
        self.debug.tool_call("fetch_covariance_matrix", f"tickers={list(portfolio.holdings.keys())}")
        self.debug.wait(200)
        self.debug.result("Loaded 252-day covariance matrix")
        
        self.debug.tool_call("scipy.optimize.minimize", "method=SLSQP, objective=max_sharpe")
        self.debug.wait(300)
        
        # Generate compliant allocation
        alternative = {
            "AAPL": 0.12, "MSFT": 0.12, "NVDA": 0.10, "GOOGL": 0.08, 
            "AMZN": 0.08, "META": 0.00,
            "BND": 0.25, "TLT": 0.15, "GLD": 0.10
        }
        
        self.debug.result(f"Optimization converged: equity={sum(v for k,v in alternative.items() if k not in ['BND','TLT','GLD']):.0%}")
        
        for ticker, weight in alternative.items():
            if weight > 0:
                self.debug.data(ticker, f"{weight:.0%}")
        
        tokens = self._simulate_llm(350, 450)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {"alternative": alternative, "equity_pct": 0.50, "expected_sharpe": 1.15}
    
    def execute_factor_attribution(self, portfolio: Portfolio) -> Dict:
        """FactorAgent: Perform factor attribution analysis."""
        start = time.time()
        self.debug.agent_start(AgentType.FACTOR, "Running factor attribution")
        
        self.debug.reasoning("Decomposing returns using Fama-French 5-factor model")
        self.debug.wait(100)
        
        # Fetch returns
        self.debug.tool_call("fetch_portfolio_returns", f"portfolio_id={portfolio.id}, period=30d")
        self.debug.wait(200)
        portfolio_return = -0.032
        self.debug.result(f"Portfolio return: {portfolio_return:.2%}")
        
        self.debug.tool_call("fetch_benchmark_returns", "benchmark=SPY, period=30d")
        self.debug.wait(150)
        benchmark_return = -0.018
        self.debug.result(f"Benchmark return: {benchmark_return:.2%}")
        
        active_return = portfolio_return - benchmark_return
        self.debug.data("Active return", f"{active_return:.2%}")
        
        # Brinson attribution
        self.debug.agent_start(AgentType.FACTOR, "Brinson attribution decomposition")
        self.debug.tool_call("brinson_attribution", "method=BHB")
        self.debug.wait(250)
        
        attribution = {
            "allocation_effect": -0.008,
            "selection_effect": -0.005,
            "interaction_effect": -0.001
        }
        
        for effect, value in attribution.items():
            self.debug.data(effect.replace("_", " ").title(), f"{value:.2%}")
        
        # Factor exposures
        self.debug.agent_start(AgentType.FACTOR, "Factor exposure analysis")
        self.debug.tool_call("calculate_factor_exposures", "model=FF5")
        self.debug.wait(300)
        
        factors = {
            "MKT-RF": {"exposure": 1.15, "factor_return": -0.028, "contribution": -0.0322},
            "SMB": {"exposure": -0.12, "factor_return": 0.004, "contribution": -0.0005},
            "HML": {"exposure": -0.35, "factor_return": 0.012, "contribution": -0.0042},
            "RMW": {"exposure": 0.08, "factor_return": 0.003, "contribution": 0.0002},
            "CMA": {"exposure": -0.22, "factor_return": -0.001, "contribution": 0.0002}
        }
        
        self.debug.result("Factor exposures calculated:")
        for factor, data in factors.items():
            self.debug.data(factor, f"beta={data['exposure']:.2f}, contrib={data['contribution']:.2%}")
        
        tokens = self._simulate_llm(400, 550)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {
            "portfolio_return": portfolio_return,
            "benchmark_return": benchmark_return,
            "active_return": active_return,
            "attribution": attribution,
            "factors": factors,
            "top_detractors": [
                {"ticker": "NVDA", "weight": 0.22, "return": -0.082, "contribution": -0.018},
                {"ticker": "META", "weight": 0.10, "return": -0.065, "contribution": -0.0065},
                {"ticker": "AMZN", "weight": 0.12, "return": -0.041, "contribution": -0.0049}
            ]
        }
    
    def execute_rag_search(self, tickers: List[str]) -> Dict:
        """RAGAgent: Search documents for relevant insights."""
        start = time.time()
        self.debug.agent_start(AgentType.RAG, "Searching document store")
        
        self.debug.tool_call("vector_search", f"tickers={tickers}, top_k=5")
        self.debug.wait(350)
        
        self.debug.result("Found 3 relevant documents")
        
        documents = [
            {"source": "NVDA_Q3_Earnings.pdf", "relevance": 0.92},
            {"source": "Fed_Minutes_Dec2025.pdf", "relevance": 0.78},
            {"source": "Tech_Sector_Outlook.pdf", "relevance": 0.71}
        ]
        
        for doc in documents:
            self.debug.data(doc["source"], f"relevance={doc['relevance']:.0%}")
        
        self.debug.agent_start(AgentType.RAG, "Extracting key insights")
        self.debug.tool_call("extract_insights", "focus=['earnings', 'risk_factors', 'guidance']")
        self.debug.wait(400)
        
        insights = [
            "NVDA Q3 revenue $18.1B beat expectations ($17.4B est)",
            "Data center growth slowing: +206% YoY vs +279% prior quarter",
            "China export restrictions cited as key risk factor (p.12)",
            "Q4 guidance below consensus - management cautious on gaming"
        ]
        
        for insight in insights:
            self.debug.result(insight)
            self.debug.wait(50)
        
        tokens = self._simulate_llm(450, 600)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {"documents": documents, "insights": insights}
    
    def execute_decision_engine(self, context: Dict) -> Dict:
        """DecisionEngine: Synthesize all inputs into final decision."""
        start = time.time()
        self.debug.agent_start(AgentType.DECISION, "Synthesizing decision")
        
        self.debug.reasoning("Evaluating all inputs to determine recommended action")
        self.debug.wait(100)
        
        decision_type = context.get("decision_type", "HOLD")
        confidence = context.get("confidence", 0.85)
        
        self.debug.tool_call("decision_matrix", f"inputs={list(context.keys())}")
        self.debug.wait(200)
        
        self.debug.decision(f"{decision_type} with {confidence:.0%} confidence")
        
        tokens = self._simulate_llm(200, 300)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {"decision": decision_type, "confidence": confidence}
    
    def execute_stress_test(self, portfolio: Portfolio, scenario: str) -> Dict:
        """StressAgent: Run stress test scenario."""
        start = time.time()
        self.debug.agent_start(AgentType.STRESS, f"Running stress test: {scenario[:30]}")
        
        # Parse scenario
        self.debug.tool_call("parse_scenario", f"text='{scenario[:30]}...'")
        self.debug.wait(150)
        
        if "rate" in scenario.lower() or "100bp" in scenario.lower():
            scenario_name = "Interest Rate Shock (+100bp)"
            shocks = {"fed_funds": 0.01, "ten_year": 0.006, "two_year": 0.0085}
        elif "crash" in scenario.lower():
            scenario_name = "Equity Market Crash (-20%)"
            shocks = {"equity": -0.20, "vix": 1.5}
        else:
            scenario_name = "Custom Scenario"
            shocks = {"equity": -0.10}
        
        self.debug.result(f"Scenario: {scenario_name}")
        for param, shock in shocks.items():
            self.debug.data(param, f"{shock:+.1%}" if abs(shock) < 1 else f"{shock:+.0%}")
        
        # Calculate sensitivities
        self.debug.agent_start(AgentType.STRESS, "Calculating position sensitivities")
        self.debug.tool_call("calculate_durations", f"tickers={list(portfolio.holdings.keys())}")
        self.debug.wait(200)
        
        self.debug.tool_call("calculate_betas", f"tickers={list(portfolio.holdings.keys())}")
        self.debug.wait(200)
        
        # Apply shocks
        self.debug.agent_start(AgentType.STRESS, "Applying stress shocks")
        self.debug.tool_call("apply_shocks", f"scenario={scenario_name}")
        self.debug.wait(300)
        
        portfolio_impact = -0.042 if "rate" in scenario.lower() else -0.156
        
        impacts = {}
        for ticker, weight in portfolio.holdings.items():
            asset = DataStore.ASSETS.get(ticker)
            if asset and asset.sector in ["Fixed Income"]:
                impact = -0.068 if "rate" in scenario.lower() else 0.032
            elif asset and asset.sector in ["Commodities"]:
                impact = -0.015
            else:
                impact = -0.025 if "rate" in scenario.lower() else -0.195
            impacts[ticker] = {"weight": weight, "impact": impact * random.uniform(0.8, 1.2)}
        
        self.debug.result(f"Portfolio impact: {portfolio_impact:.2%}")
        
        tokens = self._simulate_llm(350, 500)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {
            "scenario": scenario_name,
            "portfolio_impact": portfolio_impact,
            "impacts": impacts,
            "dollar_impact": portfolio.total_value * portfolio_impact
        }
    
    def execute_rebalance_analysis(self, portfolio: Portfolio) -> Dict:
        """RebalanceAgent: Analyze drift and recommend action."""
        start = time.time()
        self.debug.agent_start(AgentType.REBALANCE, "Analyzing portfolio drift")
        
        self.debug.tool_call("calculate_drift", f"portfolio_id={portfolio.id}")
        self.debug.wait(200)
        
        drifts = {}
        max_drift = 0
        for ticker in portfolio.holdings:
            current = portfolio.holdings.get(ticker, 0)
            target = portfolio.target_weights.get(ticker, 0)
            drift = abs(current - target)
            drifts[ticker] = {"current": current, "target": target, "drift": drift}
            max_drift = max(max_drift, drift)
            if drift > 0.01:
                self.debug.data(ticker, f"current={current:.1%}, target={target:.1%}, drift={drift:.1%}")
        
        self.debug.result(f"Maximum drift: {max_drift:.1%}")
        
        tokens = self._simulate_llm(250, 350)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return {"drifts": drifts, "max_drift": max_drift}
    
    def execute_macro_analysis(self) -> Dict:
        """MacroAgent: Fetch and analyze macro environment."""
        start = time.time()
        self.debug.agent_start(AgentType.MACRO, "Fetching macro indicators")
        
        macro = DataStore.MACRO
        
        self.debug.tool_call("fetch_vix")
        self.debug.wait(100)
        self.debug.result(f"VIX: {macro['vix']}")
        
        self.debug.tool_call("fetch_treasury_yields")
        self.debug.wait(100)
        self.debug.result(f"10Y: {macro['ten_year']}%, 2Y: {macro['two_year']}%")
        
        self.debug.tool_call("calculate_yield_spread")
        self.debug.wait(50)
        self.debug.result(f"Spread: {macro['spread']}% {'(INVERTED)' if macro['spread'] < 0 else ''}")
        
        self.debug.tool_call("determine_regime")
        self.debug.wait(100)
        self.debug.result(f"Market regime: {macro['regime']}")
        
        tokens = self._simulate_llm(180, 250)
        latency = (time.time() - start) * 1000
        self.debug.agent_end(latency, tokens.total)
        
        return macro


# =============================================================================
# RESPONSE FORMATTER
# =============================================================================

class ResponseFormatter:
    """Formats final responses for user display."""
    
    @staticmethod
    def format_header(title: str) -> str:
        return f"\n{'=' * 72}\n{title}\n{'=' * 72}"
    
    @staticmethod
    def format_subheader(title: str) -> str:
        return f"\n{'-' * 72}\n{title}\n{'-' * 72}"
    
    @staticmethod
    def format_data_update(ticker: str, results: Dict) -> str:
        output = [ResponseFormatter.format_header(f"DATA UPDATE REPORT: {ticker}")]
        output.append(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        output.append(f"Status: {results.get('status', 'unknown').upper()}")
        
        if results.get("updates"):
            output.append(ResponseFormatter.format_subheader("Updates Performed"))
            for update in results["updates"]:
                if update["type"] == "price_data":
                    output.append(f"\n  Price Data:")
                    output.append(f"    Rows added:    {update['rows_added']}")
                    output.append(f"    Date range:    {update['date_range']}")
                    output.append(f"    Latest price:  ${update['latest_price']:.2f}")
                elif update["type"] == "financial_statements":
                    output.append(f"\n  Financial Statements:")
                    output.append(f"    Filing type:   {update['filing_type']}")
                    output.append(f"    Period:        {update['period']}")
                    output.append(f"    Filing date:   {update['filing_date']}")
        else:
            output.append("\n  All data is current. No updates required.")
        
        return "\n".join(output)
    
    @staticmethod
    def format_ips_compliance(portfolio: Portfolio, ips_result: Dict, optimization_result: Dict) -> str:
        output = [ResponseFormatter.format_header("IPS COMPLIANCE ASSESSMENT")]
        output.append(f"\nPortfolio: {portfolio.name} (ID: {portfolio.id})")
        output.append(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Verdict
        compliant = ips_result.get("compliant", False)
        violations = ips_result.get("violations", [])
        
        output.append(ResponseFormatter.format_subheader("COMPLIANCE VERDICT"))
        output.append(f"\n  Status:          {'COMPLIANT' if compliant else 'NON-COMPLIANT'}")
        output.append(f"  Violations:      {len([v for v in violations if v['severity'] == 'HARD_REJECT'])}")
        output.append(f"  Warnings:        {len([v for v in violations if v['severity'] == 'SOFT_WARNING'])}")
        
        # Constraints
        output.append(ResponseFormatter.format_subheader("IPS CONSTRAINTS"))
        ips = portfolio.ips_constraints
        output.append(f"\n  {'Constraint':<30} {'Limit':>12} {'Status':>12}")
        output.append("  " + "-" * 56)
        output.append(f"  {'Maximum Equity Exposure':<30} {ips.get('max_equity', 1.0):>11.0%} {'ENFORCED':>12}")
        output.append(f"  {'Maximum Single Position':<30} {ips.get('max_single_position', 1.0):>11.0%} {'ENFORCED':>12}")
        output.append(f"  {'Minimum Positions':<30} {ips.get('min_positions', 1):>12} {'ENFORCED':>12}")
        
        # Violations
        if violations:
            output.append(ResponseFormatter.format_subheader("VIOLATION DETAILS"))
            for v in violations:
                output.append(f"\n  {v['type']}")
                output.append(f"    Severity:    {v['severity']}")
                if 'ticker' in v:
                    output.append(f"    Asset:       {v['ticker']}")
                if 'proposed' in v:
                    output.append(f"    Proposed:    {v['proposed']:.0%}")
                output.append(f"    Limit:       {v['limit']:.0%}")
        
        # Alternative
        if not compliant and optimization_result:
            output.append(ResponseFormatter.format_subheader("COMPLIANT ALTERNATIVE"))
            output.append("\n  The system has generated a modified allocation that satisfies")
            output.append("  all IPS constraints while maximizing alignment with your intent.")
            output.append(f"\n  {'Asset':<8} {'Weight':>12}")
            output.append("  " + "-" * 24)
            for ticker, weight in optimization_result.get("alternative", {}).items():
                if weight > 0:
                    output.append(f"  {ticker:<8} {weight:>11.0%}")
            output.append(f"\n  Expected Sharpe: {optimization_result.get('expected_sharpe', 0):.2f}")
        
        # Decision
        output.append(ResponseFormatter.format_subheader("DECISION"))
        if compliant:
            output.append("\n  Decision:     APPROVE")
            output.append("  Rationale:    Proposed allocation satisfies all IPS constraints.")
        else:
            output.append("\n  Decision:     REJECT ORIGINAL / PROPOSE ALTERNATIVE")
            output.append(f"  Rationale:    Proposed allocation would breach {ips.get('max_equity', 0.5):.0%} equity limit.")
        
        return "\n".join(output)
    
    @staticmethod
    def format_factor_attribution(portfolio: Portfolio, factor_result: Dict, rag_result: Dict) -> str:
        output = [ResponseFormatter.format_header("FACTOR ATTRIBUTION REPORT")]
        output.append(f"\nPortfolio: {portfolio.name} (ID: {portfolio.id})")
        output.append(f"Analysis Period: Last 30 Days")
        output.append(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Performance summary
        output.append(ResponseFormatter.format_subheader("PERFORMANCE SUMMARY"))
        output.append(f"\n  Portfolio Return:     {factor_result['portfolio_return']:>+8.2%}")
        output.append(f"  Benchmark Return:     {factor_result['benchmark_return']:>+8.2%}")
        output.append(f"  Active Return:        {factor_result['active_return']:>+8.2%}")
        
        # Brinson attribution
        output.append(ResponseFormatter.format_subheader("BRINSON ATTRIBUTION"))
        output.append(f"\n  {'Component':<25} {'Contribution':>15}")
        output.append("  " + "-" * 42)
        for effect, value in factor_result['attribution'].items():
            output.append(f"  {effect.replace('_', ' ').title():<25} {value:>+14.2%}")
        output.append("  " + "-" * 42)
        output.append(f"  {'Total Active Return':<25} {factor_result['active_return']:>+14.2%}")
        
        # Factor exposures
        output.append(ResponseFormatter.format_subheader("FACTOR EXPOSURES (Fama-French 5-Factor)"))
        output.append(f"\n  {'Factor':<15} {'Exposure':>10} {'Factor Ret':>12} {'Contribution':>14}")
        output.append("  " + "-" * 55)
        for factor, data in factor_result['factors'].items():
            output.append(f"  {factor:<15} {data['exposure']:>10.2f} {data['factor_return']:>+11.2%} {data['contribution']:>+13.2%}")
        
        # Top detractors
        output.append(ResponseFormatter.format_subheader("TOP DETRACTORS"))
        output.append(f"\n  {'Ticker':<8} {'Weight':>10} {'Return':>10} {'Contribution':>14}")
        output.append("  " + "-" * 46)
        for d in factor_result['top_detractors']:
            output.append(f"  {d['ticker']:<8} {d['weight']:>9.0%} {d['return']:>+9.1%} {d['contribution']:>+13.2%}")
        
        # Document insights
        if rag_result:
            output.append(ResponseFormatter.format_subheader("DOCUMENT INSIGHTS"))
            output.append(f"\n  Sources: {', '.join(d['source'] for d in rag_result['documents'])}")
            output.append("\n  Key Findings:")
            for insight in rag_result['insights']:
                output.append(f"    - {insight}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_stress_test(portfolio: Portfolio, stress_result: Dict) -> str:
        output = [ResponseFormatter.format_header("STRESS TEST REPORT")]
        output.append(f"\nPortfolio: {portfolio.name} (ID: {portfolio.id})")
        output.append(f"Scenario: {stress_result['scenario']}")
        output.append(f"Portfolio Value: ${portfolio.total_value:,.2f}")
        
        output.append(ResponseFormatter.format_subheader("PORTFOLIO IMPACT"))
        output.append(f"\n  Estimated Loss:   {stress_result['portfolio_impact']:>+8.2%}")
        output.append(f"  Dollar Impact:    ${stress_result['dollar_impact']:>+,.0f}")
        
        output.append(ResponseFormatter.format_subheader("POSITION IMPACTS"))
        output.append(f"\n  {'Ticker':<8} {'Weight':>10} {'Impact':>10} {'P&L':>14}")
        output.append("  " + "-" * 46)
        
        sorted_impacts = sorted(stress_result['impacts'].items(), key=lambda x: x[1]['impact'])
        for ticker, data in sorted_impacts[:5]:
            pnl = portfolio.total_value * data['weight'] * data['impact']
            output.append(f"  {ticker:<8} {data['weight']:>9.1%} {data['impact']:>+9.1%} ${pnl:>+12,.0f}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_rebalance(portfolio: Portfolio, rebalance_result: Dict, macro: Dict, decision: Dict) -> str:
        output = [ResponseFormatter.format_header("PORTFOLIO ANALYSIS REPORT")]
        output.append(f"\nPortfolio: {portfolio.name} (ID: {portfolio.id})")
        output.append(f"Total Value: ${portfolio.total_value:,.2f}")
        
        output.append(ResponseFormatter.format_subheader("DECISION SUMMARY"))
        output.append(f"\n  Decision:        {decision['decision']}")
        output.append(f"  Confidence:      {decision['confidence']:.0%}")
        
        output.append(ResponseFormatter.format_subheader("DRIFT ANALYSIS"))
        output.append(f"\n  Maximum Drift: {rebalance_result['max_drift']:.1%}")
        output.append(f"\n  {'Ticker':<8} {'Current':>10} {'Target':>10} {'Drift':>10}")
        output.append("  " + "-" * 42)
        for ticker, data in sorted(rebalance_result['drifts'].items(), key=lambda x: -x[1]['drift']):
            if data['drift'] > 0.005:
                output.append(f"  {ticker:<8} {data['current']:>9.1%} {data['target']:>9.1%} {data['drift']:>9.1%}")
        
        output.append(ResponseFormatter.format_subheader("MACRO CONTEXT"))
        output.append(f"\n  Market Regime:   {macro['regime']}")
        output.append(f"  VIX:             {macro['vix']}")
        output.append(f"  10Y Yield:       {macro['ten_year']}%")
        output.append(f"  Yield Curve:     {macro['spread']}% {'(Inverted)' if macro['spread'] < 0 else ''}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_macro(macro: Dict) -> str:
        output = [ResponseFormatter.format_header("MACRO ENVIRONMENT SUMMARY")]
        output.append(f"\nAs of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        output.append(f"Market Regime: {macro['regime']}")
        
        output.append(ResponseFormatter.format_subheader("Volatility"))
        output.append(f"\n  VIX Index:          {macro['vix']}")
        
        output.append(ResponseFormatter.format_subheader("Interest Rates"))
        output.append(f"\n  Fed Funds Rate:     {macro['fed_funds']}%")
        output.append(f"  2-Year Treasury:    {macro['two_year']}%")
        output.append(f"  10-Year Treasury:   {macro['ten_year']}%")
        output.append(f"  Yield Curve Spread: {macro['spread']}% {'(INVERTED)' if macro['spread'] < 0 else ''}")
        
        return "\n".join(output)


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class PMDecisionSystem:
    """Main orchestrator for the PM Decision Support System."""
    
    HELP_TEXT = """
================================================================================
PM DECISION SUPPORT SYSTEM - COMMAND REFERENCE
================================================================================

COMMANDS:
    /debug          Toggle debug mode (shows agent reasoning in real-time)
    /portfolio <id> Switch portfolio (1=Growth, 2=Dividend, 3=AllWeather)
    /trace          Show execution summary
    /stats          Show session statistics
    /help           Show this help
    exit            Quit

SAMPLE QUERIES:

  Data Operations:
    "What are the latest data from AAPL?"
    "Update data for NVDA"

  Macro Information:
    "What is the current VIX and macro environment?"

  Rebalancing:
    "Should I rebalance my portfolio?"

  IPS Compliance:
    "I want to go aggressive and put 85% in tech. Is this IPS compliant?"

  Factor Attribution:
    "Why did my portfolio underperform? Break down by factors."

  Stress Testing:
    "What if rates rise 100 basis points?"

================================================================================
"""
    
    def __init__(self):
        self.debug = DebugPrinter(enabled=False)
        self.executor = AgentExecutor(self.debug)
        self.formatter = ResponseFormatter()
        self.current_portfolio_id = 1
        self.session_start = datetime.now()
        self.query_count = 0
        self.last_plan: Optional[ExecutionPlan] = None
    
    def print_header(self):
        print(f"\n{Style.BOLD}{'=' * 72}")
        print("PM DECISION SUPPORT SYSTEM")
        print("Multi-Agent Portfolio Management Framework v2.0")
        print(f"{'=' * 72}{Style.END}")
        print(f"\nSession: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        portfolio = DataStore.PORTFOLIOS[self.current_portfolio_id]
        print(f"Active Portfolio: {portfolio.name}")
        print(f"\nType '/help' for commands or '/debug' to enable agent tracing.")
        print("=" * 72)
    
    def process_command(self, cmd: str) -> bool:
        """Process system commands. Returns True if handled."""
        cmd = cmd.lower().strip()
        
        if cmd == "/help":
            print(self.HELP_TEXT)
            return True
        
        if cmd == "/debug":
            enabled = self.debug.toggle()
            print(f"\nDebug mode: {'ENABLED - Agent reasoning will be visible' if enabled else 'DISABLED'}")
            return True
        
        if cmd == "/stats":
            duration = datetime.now() - self.session_start
            print(f"\n{'=' * 50}")
            print("SESSION STATISTICS")
            print(f"{'=' * 50}")
            print(f"  Duration:        {duration}")
            print(f"  Queries:         {self.query_count}")
            print(f"  Total Tokens:    {self.executor.total_tokens.total:,}")
            print(f"  Estimated Cost:  ${self.executor.total_tokens.cost_usd:.4f}")
            return True
        
        if cmd == "/trace":
            if self.last_plan:
                print(f"\nLast Query: {self.last_plan.query[:50]}...")
                print(f"Intent: {self.last_plan.query_intent.value} / {self.last_plan.execution_intent.value}")
                print(f"Agents: {', '.join(a.value for a in self.last_plan.agents_required)}")
            else:
                print("\nNo execution trace available.")
            return True
        
        if cmd.startswith("/portfolio"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                pid = int(parts[1])
                if pid in DataStore.PORTFOLIOS:
                    self.current_portfolio_id = pid
                    p = DataStore.PORTFOLIOS[pid]
                    print(f"\nSwitched to: {p.name}")
                    print(f"  Holdings: {len(p.holdings)} positions")
                    print(f"  Value: ${p.total_value:,.2f}")
                else:
                    print("\nInvalid ID. Use 1, 2, or 3.")
            else:
                print("\nUsage: /portfolio <id>")
            return True
        
        return False
    
    def process_query(self, query: str) -> str:
        """Process a user query through the multi-agent system."""
        self.executor.reset()
        self.query_count += 1
        
        # Phase 1: Route and Plan
        self.debug.section("PHASE 1: QUERY ANALYSIS")
        plan = self.executor.execute_router(query)
        self.last_plan = plan
        
        if AgentType.PLANNER in plan.agents_required:
            self.executor.execute_planner(plan)
        
        portfolio = DataStore.PORTFOLIOS[self.current_portfolio_id]
        
        # Phase 2: Execute based on intent
        self.debug.section("PHASE 2: AGENT EXECUTION")
        
        if plan.execution_intent == ExecutionIntent.DATA_UPDATE:
            # Extract ticker from query
            ticker = None
            for t in DataStore.ASSETS.keys():
                if t.lower() in query.lower():
                    ticker = t
                    break
            
            if ticker:
                result = self.executor.execute_data_update(ticker)
                return self.formatter.format_data_update(ticker, result)
            else:
                return "Error: Could not identify ticker in query."
        
        elif plan.execution_intent == ExecutionIntent.IPS_COMPLIANCE:
            ips_result = self.executor.execute_ips_check(portfolio, query)
            optimization_result = None
            if not ips_result["compliant"]:
                optimization_result = self.executor.execute_optimization(portfolio, ips_result["max_equity"])
            self.executor.execute_decision_engine({
                "decision_type": "APPROVE" if ips_result["compliant"] else "REJECT",
                "confidence": 0.94
            })
            return self.formatter.format_ips_compliance(portfolio, ips_result, optimization_result)
        
        elif plan.execution_intent == ExecutionIntent.FACTOR_ATTRIBUTION:
            factor_result = self.executor.execute_factor_attribution(portfolio)
            rag_result = self.executor.execute_rag_search(list(portfolio.holdings.keys())[:3])
            self.executor.execute_decision_engine({
                "decision_type": "ANALYSIS_COMPLETE",
                "confidence": 0.88
            })
            return self.formatter.format_factor_attribution(portfolio, factor_result, rag_result)
        
        elif plan.execution_intent == ExecutionIntent.STRESS_TEST:
            stress_result = self.executor.execute_stress_test(portfolio, query)
            self.executor.execute_decision_engine({
                "decision_type": "HEDGE" if stress_result["portfolio_impact"] < -0.10 else "HOLD",
                "confidence": 0.82
            })
            return self.formatter.format_stress_test(portfolio, stress_result)
        
        elif plan.execution_intent == ExecutionIntent.REBALANCING:
            rebalance_result = self.executor.execute_rebalance_analysis(portfolio)
            macro = self.executor.execute_macro_analysis()
            
            # Determine decision
            if rebalance_result["max_drift"] < 0.03:
                decision = {"decision": "HOLD", "confidence": 0.87}
            elif rebalance_result["max_drift"] < 0.05:
                decision = {"decision": "TILT", "confidence": 0.72}
            else:
                decision = {"decision": "REBALANCE", "confidence": 0.81}
            
            self.executor.execute_decision_engine(decision)
            return self.formatter.format_rebalance(portfolio, rebalance_result, macro, decision)
        
        elif plan.execution_intent == ExecutionIntent.MACRO_ANALYSIS:
            macro = self.executor.execute_macro_analysis()
            return self.formatter.format_macro(macro)
        
        else:
            return f"Query type '{plan.execution_intent.value}' not yet implemented in demo."
    
    def run(self):
        """Run the interactive demo."""
        self.print_header()
        
        while True:
            try:
                user_input = input(f"\n{Style.BOLD}>{Style.END} ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    print("\nSession ended.")
                    break
                
                if user_input.startswith("/"):
                    if self.process_command(user_input):
                        continue
                
                # Process query
                if not self.debug.enabled:
                    print("\nProcessing...")
                
                start = time.time()
                response = self.process_query(user_input)
                elapsed = time.time() - start
                
                # Print response
                print(response)
                
                # Print execution summary
                print(f"\n{Style.DIM}{'=' * 72}")
                print(f"Execution: {len(self.executor.steps)} agents | "
                      f"{self.executor.total_tokens.total:,} tokens | "
                      f"{elapsed:.2f}s | "
                      f"${self.executor.total_tokens.cost_usd:.4f}")
                print(f"{'=' * 72}{Style.END}")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Check if terminal supports colors
    import os
    if os.name == 'nt' or not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        Style.disable()
    
    system = PMDecisionSystem()
    system.run()