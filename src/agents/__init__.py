# src/agents/__init__.py
# Purpose: Clean exports for the agents module
# Updated: Phase 5.1 - Added multi-agent system components

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
# NEW EXPORTS (Phase 5+: Multi-Agent System)
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

# Specialized Agents
from .data_agent import (
    DataAgent,
    DataAgentConfig,
    create_data_agent,
)

from .risk_manager_agent import (
    RiskManagerAgent,
    RiskManagerConfig,
    create_risk_manager,
)


# =============================================================================
# VERSION & EXPORTS
# =============================================================================

__version__ = "0.5.0"  # Updated for Phase 5

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
    
    # === Phase 5+: Multi-Agent System ===
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
    "MultiAgentState",  # Note: Renamed from AgentState to avoid conflict
    "AgentMessage",
    # Agents
    "DataAgent",
    "create_data_agent",
    "RiskManagerAgent",
    "create_risk_manager",
]