# src/agents/__init__.py
# Purpose: Clean exports for the agents module
# Updated: Phase 6 - Multi-Agent System (Cleaned)
#
# REMOVED in Cleanup:
#   - finance_agent (replaced by specialized agents)
#   - cli.py (replaced by demos/multi_agent_cli.py)

"""
Agents Module for Quant Portfolio Manager.

Usage:
    from agents import create_data_agent
    
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
# SPECIALIZED AGENTS
# =============================================================================

# Data Agent - Market data, covariance, returns
from .data_agent import (
    DataAgent,
    create_data_agent,
)

# Rebalance Agent - Drift analysis, trade generation (DETERMINISTIC)
from .rebalance_agent import (
    RebalanceAgent,
    create_rebalance_agent,
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
    
    # === Specialized Agents ===
    # Data Agent
    "DataAgent",
    "create_data_agent",

    # Rebalance Agent
    "RebalanceAgent", 
    "create_rebalance_agent",
]