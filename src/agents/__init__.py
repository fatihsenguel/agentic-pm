# src/agents/__init__.py
# Purpose: Clean exports for the agents module
# Updated: Phase 5.4 - Added Optimization Agent

# =============================================================================
# EXISTING EXPORTS (Phase 1-3: Single Agent)
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

from .state import AgentState, trim_messages

from .prompts import (
    FINANCE_AGENT_SYSTEM_PROMPT,
    build_system_prompt,
)

from .finance_agent import (
    create_finance_agent,
    chat,
    run_single_query,
)


# =============================================================================
# PHASE 5.1 EXPORTS (Multi-Agent Foundation)
# =============================================================================

# Protocols - DTOs for agent communication
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

# Base Agent classes
from .base_agent import (
    BaseAgent,
    SupervisorAgent,
    AgentConfig,
    AgentRole,
    AgentState as MultiAgentState,  # Renamed to avoid conflict with LangGraph state
    AgentMessage,
)

# Data Agent
from .data_agent import (
    DataAgent,
    DataAgentConfig,
    create_data_agent,
)

# Risk Manager (Supervisor)
from .risk_manager_agent import (
    RiskManagerAgent,
    RiskManagerConfig,
    create_risk_manager,
)

# =============================================================================
# PHASE 5.2 EXPORTS (Optimization)
# =============================================================================

from .optimization_agent import (
    OptimizationAgent,
    OptimizationAgentConfig,
    create_optimization_agent,
)

# =============================================================================
# PHASE 5.3 EXPORTS (BACKTESTS)
# =============================================================================

# Phase 5.3: Backtest Agent
from .backtest_agent import (
    BacktestAgent,
    BacktestAgentConfig,
    create_backtest_agent,
)

# =============================================================================
# PHASE 5.3 EXPORTS (RAG)
# =============================================================================

# Phase 5.4: Macro Agent
from .macro_agent import (
    MacroAgent,
    MacroAgentConfig,
    create_macro_agent,
)

from .rebalance_agent import RebalanceAgent, create_rebalance_agent

# =============================================================================
# VERSION & EXPORTS
# =============================================================================
__version__ = "0.5.4"  # Updated for Phase 5.4

__all__ = [
    # === Phase 1-3: Single Agent ===
    # Config
    "ACTIVE_LLM_CONFIG",
    "AGENT_SETTINGS", 
    "get_llm",
    # Agent
    "create_finance_agent",
    "chat",
    "run_single_query",
    # State (LangGraph)
    "AgentState",
    "trim_messages",
    
    # === Phase 5.1: Multi-Agent Foundation ===
    # Enums
    "TaskType",
    "OptimizationMethod",
    "RebalanceFrequency",
    "RegimeType",
    # Core DTOs
    "PortfolioTask",
    "PortfolioResult", 
    "PortfolioConstraints",
    # Supporting DTOs
    "TAARule",
    "BacktestMetrics",
    "RiskDecomposition",
    "CovarianceResult",
    "RegimeSignal",
    "RebalanceAnalysis",
    # Base classes
    "BaseAgent",
    "SupervisorAgent",
    "AgentConfig",
    "AgentRole",
    "MultiAgentState",
    "AgentMessage",
    # Data Agent
    "DataAgent",
    "create_data_agent",
    # Risk Manager
    "RiskManagerAgent",
    "create_risk_manager",
    
    # === Phase 5.2: Optimization ===
    "OptimizationAgent",
    "create_optimization_agent",
    
    # === Phase 5.3: Backtest ===
    "BacktestAgent",
    "create_backtest_agent",

    # === Phase 5.4: RAG ===
    "MacroAgent",
    "create_macro_agent",

   # == 5.5 ==
   "RebalanceAgent", 
   "create_rebalance_agent"
]