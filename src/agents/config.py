# src/agents/config.py
# Purpose: Centralized LLM configuration
# Principle: Single source of truth for model settings, easy to swap providers

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """
    Configuration for LLM provider.
    API key is loaded lazily (only when needed) to avoid import errors.
    """
    provider: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 1024
    _api_key: Optional[str] = field(default=None, repr=False)
    
    @property
    def api_key(self) -> str:
        """Lazy load API key - only fails when actually used."""
        if self._api_key:
            return self._api_key
        
        env_var = f"{self.provider.upper()}_API_KEY"
        key = os.getenv(env_var)
        
        if not key:
            raise ValueError(
                f"Missing API key. Set {env_var} in your .env file.\n"
                f"Example: {env_var}=sk-..."
            )
        return key


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

# Cost-optimized for MVP (YOUR CURRENT CHOICE)
OPENAI_MINI = LLMConfig(
    provider="openai",
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=1024,
)

# Higher capability when needed
OPENAI_FULL = LLMConfig(
    provider="openai",
    model="gpt-4o",
    temperature=0.1,
    max_tokens=2048,
)

# Claude alternatives (for future - won't error on import)
ANTHROPIC_HAIKU = LLMConfig(
    provider="anthropic",
    model="claude-haiku-4-5-20251001",
    temperature=0.1,
    max_tokens=1024,
)

# The stronger model behind the router's use_stronger_model switch, off by
# default. Decision 16 (KNOWN_GAPS) is logged, not taken; this is only the
# id, accepted by the token counter on 9 September, so that flipping the
# switch gives Sonnet and not Haiku with a plausible face.
ANTHROPIC_SONNET = LLMConfig(
    provider="anthropic",
    model="claude-sonnet-5",
    temperature=0.1,
    max_tokens=2048,
)



# =============================================================================
# ACTIVE CONFIGURATION (change this one line to switch models)
# =============================================================================

ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU

# =============================================================================
# AGENT BEHAVIOR SETTINGS
# =============================================================================

@dataclass
class AgentSettings:
    """Runtime settings for agent behavior - tune for cost/quality tradeoff."""
    
    # Context window management
    max_conversation_history: int = 10
    
    # Tool behavior
    max_tool_iterations: int = 5
    
    # Response behavior
    verbose_tool_results: bool = False


AGENT_SETTINGS = AgentSettings()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_llm():
    """
    Factory: Returns configured LLM instance.
    API key is validated here (not at import time).
    """
    config = ACTIVE_LLM_CONFIG
    
    if config.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key,  # Lazy loaded here
        )
    
    elif config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key,  # Lazy loaded here
        )
    
    else:
        raise ValueError(f"Unknown provider: {config.provider}")