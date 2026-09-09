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
from .extraction import Extraction, extract, resolve
from .router_prompts import build_router_prompt, build_repair_prompt
from .schemas import (
    RouterDecision, 
    IntentType, 
    ExtractedParameters,
    TERMINAL,
    derive_plan,
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
    use_stronger_model: bool = False
    
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
                from agents.config import ANTHROPIC_SONNET
                from langchain_anthropic import ChatAnthropic
                self._llm = ChatAnthropic(
                    model=ANTHROPIC_SONNET.model,
                    temperature=0.0,
                    max_tokens=1024,
                    api_key=ANTHROPIC_SONNET.api_key,
                )
            else:
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
        portfolio_id: Optional[int] = None,
        pending: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RouterDecision, ValidationResult]:
        """
        Route a user message to the appropriate agent(s).

        `pending` is the record of what the previous turn asked back. The
        message is first resolved against it (agents/extraction.resolve):
        a reply that confirms or names a ticker becomes the original
        question with that ticker, and is routed as if typed, the
        resolution recorded on the decision; any other message is new.

        Extraction runs first (agents/extraction.py): tickers, period,
        volatility cap and hypothetical weight are read from the message
        deterministically, and the model's values for those fields are never
        read - every attempt's JSON has them replaced before validation. If
        the message asks for something the vocabularies cannot express, the
        clarification is returned here and the model is not called. The
        model decides intent, measure and group_by; the plan is derived
        from those, and whether a compliance question asks what the policy
        says is extraction's, the topic then being the user's own words,
        which is what the policy is matched against.
        
        Args:
            user_message: The user's request
            portfolio_id: Optional portfolio ID to analyze
            pending: The previous turn's clarification record, if any
        
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
            
            resolved = None
            resolved_message = resolve(user_message, pending, portfolio_tickers or [])
            if resolved_message is not None:
                resolved = {"reply": user_message, "message": resolved_message}
                user_message = resolved_message

            extraction = extract(
                user_message, portfolio_tickers or [], app_config.data.period_days.keys()
            )
            if extraction.clarification:
                self.stats["clarifications_requested"] += 1
                return self._clarification_from_extraction(extraction), ValidationResult()

            # Build prompt
            prompt = build_router_prompt(
                user_message=user_message,
                include_examples=self.config.include_examples,
                # Tells the router the portfolio exists, not to copy it: nothing
                # downstream reads parameters.tickers when a portfolio is set
                # except the position P&L formatter, where a filled list means
                # "these positions" and an empty one means "every position".
                portfolio_context=(
                    f"The user has an active portfolio (id={portfolio_id}) holding: "
                    f"{', '.join(portfolio_tickers)}. 'My portfolio', 'my holdings', "
                    f"'my position(s)', 'my allocation', 'my risk' and 'my volatility' "
                    f"refer to it. You already have this data - never ask the user to "
                    f"provide their holdings, and never copy these tickers into "
                    f"parameters.tickers: leave tickers empty unless the user names "
                    f"specific symbols in the message."
                ) if portfolio_tickers else None
            )
            
            # Call LLM
            decision, validation = await self._call_llm_with_retry(
                prompt=prompt,
                user_message=user_message,
                extraction=extraction,
            )
            if decision and resolved:
                decision.resolved = resolved
            
            # parameters.tickers is what the user named, and nothing else. A
            # block here used to overwrite it with the portfolio's tickers (or
            # the union, via list(set(...)), which is where the random order
            # came from). Nothing read the overwritten value while a portfolio
            # was set - the data layer loads holdings from the database - until
            # position P&L did, where a filled list means "these positions" and
            # an empty one "every position". The portfolio id is the state's;
            # nothing is copied onto the parameters after the model call.
            
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
                    f"Routed to: {list(decision.execution_order)} "
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
        user_message: str,
        extraction: Extraction,
    ) -> Tuple[Optional[RouterDecision], ValidationResult]:
        """
        Call LLM and retry on parsing failures. Every attempt's parameters
        are overwritten from `extraction` before validation, so a validator
        that rejects a mode under the wrong intent is asking the model to
        change the intent, the one thing it still decides.
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
                raw_json = _with_extraction(raw_json, extraction, user_message)
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
        Additional validation of the router decision: the tickers against
        the database. The agent names and the plan are the schema's and the
        terminal table's - execution_order is typed against AgentName and
        derived from one table - so no check here on it could fire.
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
        
        return validation
    
    def _clarification_from_extraction(self, extraction: Extraction) -> RouterDecision:
        """The message asked for something outside the vocabularies - a typo
        of a holding, a span the period vocabulary lacks, two weights. The
        question is extraction's, deterministic, and no model is consulted:
        a model shown the message would either guess or ask the same."""
        return RouterDecision(
            intent=IntentType.CLARIFICATION_NEEDED,
            confidence=1.0,
            execution_order=[],
            parameters=ExtractedParameters(
                tickers=extraction.tickers,
                period=extraction.period,
                max_volatility=extraction.max_volatility,
                hypothetical_weight=extraction.hypothetical_weight,
            ),
            reasoning=f"Extraction could not resolve the message: {extraction.clarification}"[:1000],
            clarification_question=extraction.clarification,
            pending=extraction.pending,
        )

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
            execution_order=[],
            parameters=ExtractedParameters(),
            reasoning=f"Router failed: {error}",
            clarification_question="Es tut mir leid, ich konnte Ihre Anfrage nicht verstehen. Können Sie bitte genauer beschreiben, was Sie tun möchten?"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = self.stats["total_routes"]
        return {
            **self.stats,
            "success_rate": self.stats["successful_routes"] / total if total > 0 else 0,
            "clarification_rate": self.stats["clarifications_requested"] / total if total > 0 else 0,
        }


def _with_extraction(raw: Dict[str, Any], extraction: Extraction, user_message: str) -> Dict[str, Any]:
    """The model's JSON with the extracted fields and the derived plan
    written over its own.

    Tickers, period, volatility cap and hypothetical weight are the message's,
    read deterministically; whatever the model put there is not read. So is
    the policy topic: extraction decides whether the question asks what the
    policy says, and the topic is then the user's own words, which the
    compliance node matches the owner's topic vocabulary against. The
    model's flag missed into a lookup for questions about a position, and a
    paraphrased value would match a clause the user did not ask about
    (KNOWN_GAPS, runner 3.4 and the prompt shrink, 8 September).
    """
    parameters = dict(raw.get("parameters") or {})
    parameters["tickers"] = list(extraction.tickers)
    parameters["period"] = extraction.period
    parameters["max_volatility"] = extraction.max_volatility
    parameters["hypothetical_weight"] = extraction.hypothetical_weight
    parameters["policy_topic"] = user_message if extraction.policy_lookup else None
    out = {**raw, "parameters": parameters}
    # The record of a clarification and the resolution are the router's own,
    # from extraction; the model writes neither.
    out["pending"] = extraction.pending
    out["resolved"] = None

    # The plan is derived from the intent and those parameters through
    # schemas.TERMINAL and REQUIRES; the model's execution_order is not
    # read, and a task list it sends is ignored with every other extra
    # field. An intent the registry lacks is left for the schema to reject.
    intent = raw.get("intent")
    if intent in TERMINAL:
        plan = derive_plan(intent, parameters)
        out["execution_order"] = plan
    return out


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
