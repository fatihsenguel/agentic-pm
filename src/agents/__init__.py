# src/agents/__init__.py
# Purpose: Clean exports for the agents module
# Updated: Phase 6 - Multi-Agent System (Cleaned)
#
# REMOVED in Cleanup:
#   - finance_agent (replaced by specialized agents)
#   - cli.py (replaced by demos/multi_agent_cli.py)

"""
Agents Module for Quant Portfolio Manager.

Multi-Agent Architecture:
    ┌─────────────────────────────────────────┐
    │         RiskManagerAgent                │
    │           (Supervisor)                  │
    └─────────────┬───────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  Data   │ │  Macro  │ │Rebalance│ │Backtest │
│  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Usage:
    from agents import create_data_agent, create_macro_agent
    
    data_agent = create_data_agent(verbose=True)
    result = data_agent.fetch_prices_tool(tickers="SPY,TLT", period="1Y")
"""

# =============================================================================
# CONFIGURATION & LLM SETUP
# =============================================================================

from .config import (
    ACTIVE_LLM_CONFIG,
    AGENT_SETTINGS,
    get_llm,
    # Presets for easy switching
    OPENAI_MINI,
    OPENAI_FULL,
    ANTHROPIC_HAIKU,
    ANTHROPIC_SONNET,
)

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

from .state import AgentState, trim_messages

# =============================================================================
# PROMPTS
# =============================================================================

from .prompts import (
    build_system_prompt,
)

# =============================================================================
# PROTOCOLS - DTOs for Agent Communication
# =============================================================================

from .protocols import (
    # Enums
    TaskType,
    OptimizationMethod,
    RebalanceFrequency,
    RegimeType,
    # Core DTOs
    PortfolioTask,
    PortfolioResult,
    PortfolioConstraints,
    # Supporting DTOs
    TAARule,
    BacktestMetrics,
    RiskDecomposition,
    CovarianceResult,
    RegimeSignal,
    RebalanceAnalysis,
)

# =============================================================================
# BASE AGENT CLASSES
# =============================================================================

from .base_agent import (
    BaseAgent,
    SupervisorAgent,
    AgentConfig,
    AgentRole,
    AgentState as MultiAgentState,  # Renamed to avoid conflict with LangGraph state
    AgentMessage,
)

# =============================================================================
# SPECIALIZED AGENTS
# =============================================================================

# Data Agent - Market data, covariance, returns
from .data_agent import (
    DataAgent,
    create_data_agent,
)

# Macro Agent - VIX, yields, regime detection, TAA signals
from .macro_agent import (
    MacroAgent,
    create_macro_agent,
)

# Rebalance Agent - Drift analysis, trade generation (DETERMINISTIC)
from .rebalance_agent import (
    RebalanceAgent,
    create_rebalance_agent,
)

# Optimization Agent - Mean-variance, risk parity
from .optimization_agent import (
    OptimizationAgent,
    create_optimization_agent,
)

# Backtest Agent - Historical simulation
from .backtest_agent import (
    BacktestAgent,
    create_backtest_agent,
)

# Risk Manager Agent - SUPERVISOR (coordinates all other agents)
from .risk_manager_agent import (
    RiskManagerAgent,
    create_risk_manager,
)

# =============================================================================
# VERSION & EXPORTS
# =============================================================================
__version__ = "0.6.0"  # Phase 6: Production-Ready Multi-Agent System

__all__ = [
    # === Configuration ===
    "ACTIVE_LLM_CONFIG",
    "AGENT_SETTINGS", 
    "get_llm",
    "OPENAI_MINI",
    "OPENAI_FULL",
    "ANTHROPIC_HAIKU",
    "ANTHROPIC_SONNET",
    
    # === State Management ===
    "AgentState",
    "trim_messages",
    
    # === Prompts ===
    "build_system_prompt",
    
    # === Protocols (Enums) ===
    "TaskType",
    "OptimizationMethod",
    "RebalanceFrequency",
    "RegimeType",
    
    # === Protocols (Core DTOs) ===
    "PortfolioTask",
    "PortfolioResult", 
    "PortfolioConstraints",
    
    # === Protocols (Supporting DTOs) ===
    "TAARule",
    "BacktestMetrics",
    "RiskDecomposition",
    "CovarianceResult",
    "RegimeSignal",
    "RebalanceAnalysis",
    
    # === Base Classes ===
    "BaseAgent",
    "SupervisorAgent",
    "AgentConfig",
    "AgentRole",
    "MultiAgentState",
    "AgentMessage",
    
    # === Specialized Agents ===
    # Data Agent
    "DataAgent",
    "create_data_agent",
    
    # Macro Agent
    "MacroAgent",
    "create_macro_agent",
    
    # Rebalance Agent
    "RebalanceAgent", 
    "create_rebalance_agent",
    
    # Optimization Agent
    "OptimizationAgent",
    "create_optimization_agent",
    
    # Backtest Agent
    "BacktestAgent",
    "create_backtest_agent",
    
    # Risk Manager (Supervisor)
    "RiskManagerAgent",
    "create_risk_manager",
]