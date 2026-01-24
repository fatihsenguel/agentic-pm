# src/agents/smart_router.py
# Purpose: LLM-based intent detection and agent routing
# Principle: Replace dumb if/else with intelligent routing
# Phase: 6.1 - Smart Router (LLM-Based Intent Detection)

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .config import get_llm, LLMConfig, OPENAI_FULL, ACTIVE_LLM_CONFIG
from .router_prompts import build_router_prompt, build_repair_prompt
from .schemas import (
    RouterDecision, 
    IntentType, 
    AgentName, 
    AgentTask,
    ExtractedParameters,
    safe_parse_router_response
)
from .validators import (
    validate_tickers,
    validate_optimization_request,
    suggest_ticker,
    ValidationResult
)

import logging
logger = logging.getLogger(__name__)
from config import config as app_config

# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

@dataclass
class RouterConfig:
    """Configuration for the Smart Router."""
    # Use stronger model for routing decisions (GPT-4o instead of GPT-4o-mini)
    use_stronger_model: bool = True
    
    # Max retries for parsing failures
    max_retries: int = 2
    
    # Include few-shot examples (costs tokens but improves accuracy)
    include_examples: bool = True
    
    # Minimum confidence to proceed without clarification
    min_confidence: float = 0.5
    
    # Enable ticker validation
    validate_tickers: bool = True
    
    # Enable observability tracing
    enable_tracing: bool = True


# =============================================================================
# SMART ROUTER CLASS
# =============================================================================

class SmartRouter:
    """
    LLM-based intent detection and agent routing.
    
    Replaces the simple if/else keyword matching with intelligent
    natural language understanding.
    
    Features:
    - Multi-agent chain detection
    - Parameter extraction (tickers, constraints)
    - Confidence scoring
    - Validation with retry
    - Observability integration
    """
    
    def __init__(self, config: Optional[RouterConfig] = None):
        """
        Initialize the Smart Router.
        
        Args:
            config: Router configuration (uses defaults if not provided)
        """
        self.config = config or RouterConfig()
        self._llm = None
        self._tracer = None
        self._token_counter = None
        
        # Track routing statistics
        self.stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "clarifications_requested": 0,
            "retries_needed": 0,
            "validation_errors": 0,
        }
    
    @property
    def llm(self):
        """Lazy load LLM to avoid import-time API key validation."""
        if self._llm is None:
            if self.config.use_stronger_model:
                # Use GPT-4o for routing (more accurate)
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=OPENAI_FULL.model,
                    temperature=0.0,  # Deterministic for routing
                    max_tokens=1024,
                    api_key=OPENAI_FULL.api_key,
                )
            else:
                # Use default model from config
                self._llm = get_llm()
        return self._llm
    
    @property
    def tracer(self):
        """Lazy load tracer."""
        if self._tracer is None and app_config.features.observability_enabled and self.config.enable_tracing:
            try:
                from observability import get_tracer
                self._tracer = get_tracer()
            except ImportError:
                self._tracer = None
        return self._tracer
    
    @property
    def token_counter(self):
        """Lazy load token counter."""
        if self._token_counter is None and app_config.features.observability_enabled and self.config.enable_tracing:
            try:
                from observability import get_token_counter
                self._token_counter = get_token_counter()
            except ImportError:
                self._token_counter = None
        return self._token_counter
    
    async def route(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
        available_agents: Optional[List[str]] = None,
        portfolio_id: Optional[int] = None  # ⭐ NEW
    ) -> Tuple[RouterDecision, ValidationResult]:
        """
        Route a user message to the appropriate agent(s).
        
        Args:
            user_message: The user's request
            conversation_history: Previous conversation messages
            available_agents: List of currently available agents
            portfolio_id: Optional portfolio ID to analyze (overrides tickers from LLM)
        
        Returns:
            Tuple of (RouterDecision, ValidationResult)
        """
        self.stats["total_routes"] += 1
        
        # Start tracing if available
        request_ctx = None
        agent_ctx = None
        if self.tracer:
            request_ctx = self.tracer.trace_request(user_input=user_message[:100])
            request_ctx.__enter__()
            agent_ctx = request_ctx.trace_agent("SmartRouter")
            agent_ctx.__enter__()
            agent_ctx.log_thinking(f"Routing: {user_message[:100]}...")
        
        try:
            # ⭐ NEW: Load portfolio tickers if portfolio_id provided
            portfolio_tickers = None
            if portfolio_id:
                try:
                    from portfolio_tool.portfolio_manager import PortfolioManager
                    pm = PortfolioManager()
                    portfolio_tickers = pm.get_portfolio_tickers(portfolio_id)
                    if portfolio_tickers:
                        logger.info(f"Loaded {len(portfolio_tickers)} tickers from portfolio {portfolio_id}: {portfolio_tickers}")
                    else:
                        logger.warning(f"Portfolio {portfolio_id} has no holdings")
                except Exception as e:
                    logger.error(f"Failed to load portfolio {portfolio_id}: {e}")
                    # Continue without portfolio - LLM will extract tickers from message
            
            # Build prompt
            prompt = build_router_prompt(
                user_message=user_message,
                conversation_history=conversation_history,
                include_examples=self.config.include_examples,
                available_agents=available_agents
            )
            
            # Call LLM
            decision, validation = await self._call_llm_with_retry(
                prompt=prompt,
                user_message=user_message
            )
            
            # ⭐ RECOMMENDED: Smart ticker merging
            if portfolio_tickers and decision:
                llm_tickers = decision.parameters.tickers or []
                
                if llm_tickers:
                    # User mentioned specific tickers - combine with portfolio
                    combined = list(set(llm_tickers + portfolio_tickers))
                    decision.parameters.tickers = combined
                    logger.info(f"Mixed query: Combined {llm_tickers} + portfolio {portfolio_id} → {combined}")
                else:
                    # Pure portfolio query - use only portfolio tickers
                    decision.parameters.tickers = portfolio_tickers
                    logger.info(f"Portfolio query: Using portfolio {portfolio_id} tickers: {portfolio_tickers}")
                
                decision.parameters.portfolio_id = portfolio_id
            
            # Additional validation if enabled
            if self.config.validate_tickers and decision:
                validation = self._validate_decision(decision, validation)
            
            # Track success
            if decision and decision.intent != IntentType.CLARIFICATION_NEEDED:
                self.stats["successful_routes"] += 1
            elif decision and decision.intent == IntentType.CLARIFICATION_NEEDED:
                self.stats["clarifications_requested"] += 1
            
            # Log to tracer
            if agent_ctx and decision:
                agent_ctx.log_thinking(
                    f"Routed to: {[a.agent for a in decision.agents_needed]} "
                    f"(confidence: {decision.confidence:.2f})"
                )
            
            return decision, validation
            
        except Exception as e:
            self.stats["validation_errors"] += 1
            # Return a fallback decision
            fallback = self._create_fallback_decision(user_message, str(e))
            return fallback, ValidationResult()
            
        finally:
            if agent_ctx:
                agent_ctx.__exit__(None, None, None)
            if request_ctx:
                request_ctx.__exit__(None, None, None)
    
    async def _call_llm_with_retry(
        self,
        prompt: str,
        user_message: str
    ) -> Tuple[Optional[RouterDecision], ValidationResult]:
        """
        Call LLM and retry on parsing failures.
        """
        last_error = None
        validation = ValidationResult()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Call LLM
                if attempt == 0:
                    response = await self.llm.ainvoke(prompt)
                else:
                    # Retry with repair prompt
                    self.stats["retries_needed"] += 1
                    repair_prompt = build_repair_prompt(user_message, last_error)
                    response = await self.llm.ainvoke(repair_prompt)
                
                # Track tokens if counter available
                if self.token_counter:
                    # Estimate tokens (actual counting would need tiktoken)
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response.content.split()) * 1.3
                    self.token_counter.add_usage(
                        agent_name="SmartRouter",
                        input_tokens=int(input_tokens),
                        output_tokens=int(output_tokens)
                    )
                
                # Parse response
                raw_json = self._extract_json(response.content)
                decision, error = safe_parse_router_response(raw_json)
                
                if decision:
                    return decision, validation
                else:
                    last_error = error
                    validation.add_error(f"Attempt {attempt + 1}: {error}")
                    
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {str(e)}"
                validation.add_error(last_error)
            except Exception as e:
                last_error = str(e)
                validation.add_error(last_error)
        
        # All retries failed
        return None, validation
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Handles:
        - Pure JSON response
        - JSON in markdown code blocks
        - JSON with surrounding text
        """
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from code block
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        match = re.search(code_block_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        raise json.JSONDecodeError("No valid JSON found in response", text, 0)
    
    def _validate_decision(
        self,
        decision: RouterDecision,
        validation: ValidationResult
    ) -> ValidationResult:
        """
        Additional validation of the router decision.
        """
        # Validate tickers if any were extracted
        if decision.parameters.tickers:
            valid, unknown, invalid = validate_tickers(decision.parameters.tickers)
            
            for ticker in invalid:
                validation.add_error(f"Invalid ticker: {ticker}")
                suggestion = suggest_ticker(ticker)
                validation.add_suggestion(ticker, suggestion)
            
            for ticker in unknown:
                validation.add_warning(f"Unknown ticker (not in database): {ticker}")
        
        # Validate agents exist
        valid_agents = {a.value for a in AgentName}
        for task in decision.agents_needed:
            if task.agent not in valid_agents:
                validation.add_error(f"Unknown agent: {task.agent}")
        
        # Validate execution order makes sense
        if len(decision.execution_order) != len(decision.agents_needed):
            validation.add_warning("execution_order length doesn't match agents_needed")
        
        return validation
    
    def _create_fallback_decision(
        self,
        user_message: str,
        error: str
    ) -> RouterDecision:
        """
        Create a fallback decision when routing fails.
        """
        return RouterDecision(
            intent=IntentType.CLARIFICATION_NEEDED,
            confidence=0.0,
            agents_needed=[],
            execution_order=[],
            parameters=ExtractedParameters(),
            is_multi_step=False,
            requires_confirmation=False,
            reasoning=f"Router failed: {error}",
            clarification_question="Es tut mir leid, ich konnte Ihre Anfrage nicht verstehen. Können Sie bitte genauer beschreiben, was Sie tun möchten?"
        )
    
    def route_sync(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
        available_agents: Optional[List[str]] = None
    ) -> Tuple[RouterDecision, ValidationResult]:
        """
        Synchronous version of route() for non-async contexts.
        """
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.route(user_message, conversation_history, available_agents)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = self.stats["total_routes"]
        return {
            **self.stats,
            "success_rate": self.stats["successful_routes"] / total if total > 0 else 0,
            "clarification_rate": self.stats["clarifications_requested"] / total if total > 0 else 0,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_router_instance: Optional[SmartRouter] = None


def get_router(config: Optional[RouterConfig] = None) -> SmartRouter:
    """
    Get or create the Smart Router singleton.
    
    Args:
        config: Optional configuration (only used on first call)
    
    Returns:
        SmartRouter instance
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = SmartRouter(config)
    
    return _router_instance


def create_router(config: Optional[RouterConfig] = None) -> SmartRouter:
    """
    Create a new Smart Router instance (not singleton).
    
    Use this when you need isolated instances (e.g., testing).
    """
    return SmartRouter(config)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def route_message(
    user_message: str,
    conversation_history: Optional[List[dict]] = None
) -> RouterDecision:
    """
    Quick routing function for simple use cases.
    
    Returns only the decision (ignores validation).
    """
    router = get_router()
    decision, _ = await router.route(user_message, conversation_history)
    return decision


def detect_intent_simple(user_message: str) -> Dict[str, Any]:
    """
    Simple synchronous intent detection.
    
    Returns dict for backwards compatibility with old interface.
    """
    router = get_router()
    decision, validation = router.route_sync(user_message)
    
    return {
        "type": decision.intent.value,
        "agents_needed": [task.agent for task in decision.agents_needed],
        "parameters": {
            "tickers": decision.parameters.tickers,
            "period": decision.parameters.period,
            "max_volatility": decision.parameters.max_volatility,
        },
        "confidence": decision.confidence,
        "is_multi_step": decision.is_multi_step,
        "reasoning": decision.reasoning,
        "validation_errors": validation.errors,
        "validation_warnings": validation.warnings,
    }