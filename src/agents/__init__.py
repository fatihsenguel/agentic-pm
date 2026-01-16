# src/agents/__init__.py
# Purpose: Clean exports for the agents module

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

# Version
__version__ = "0.2.0"

# Quick access
__all__ = [
    # Config
    "ACTIVE_LLM_CONFIG",
    "AGENT_SETTINGS", 
    "get_llm",
    # Agent
    "create_finance_agent",
    "chat",
    "run_single_query",
    # State
    "AgentState",
]
