# src/agents/router_prompts.py
# Purpose: System prompts for the Smart Router
# Principle: Minimal tokens, maximum clarity. The router must be fast and accurate.
# Phase: 6.1 - Smart Router (LLM-Based Intent Detection)

from typing import Optional

from .schemas import INTENTS

# =============================================================================
# ROUTER SYSTEM PROMPT
# =============================================================================

# The system prompt is assembled at import from literal pieces with the
# intent list and the schema's intent line rendered from schemas.INTENTS in
# between. Plain concatenation rather than .format(), because the prompt is
# full of JSON braces. An intent line is "- value: description", the schema
# line the values joined by "|".
#
# What the model decides, and all the prompt asks for: the intent; for a
# question about an existing portfolio's own figures, which measure and
# which breakdown; a clarification question; confidence; a short reasoning.
# Tickers, periods, percentages and the compliance mode are extracted from
# the message before the model sees it, and the plan is derived from the
# intent and those parameters (agents/extraction.py, schemas.TERMINAL), so
# the prompt names no agent, asks for no plan, no extracted field and no
# mode. docs/DIRECTION.md: the router reduced to the one decision an LLM
# should make.

_PROMPT_BEFORE_INTENTS = """You are the Intent Router for a Quant Portfolio Management system.

YOUR ROLE:
Classify the user's request: its intent, and for a question about an existing portfolio's own figures, which figure and which breakdown were asked for. You DO NOT execute tasks, plan agents, or extract tickers, periods or percentages - those are read from the message before you see it.

INTENT TYPES:
"""

_PROMPT_AFTER_INTENTS = """

OUTPUT FORMAT:
You MUST respond with valid JSON matching this schema:
{
  "intent": \""""

_PROMPT_AFTER_INTENT_LINE = """\",
  "confidence": 0.0-1.0,
  "parameters": {
    "measure": null,
    "group_by": null,
    "status": null
  },
  "reasoning": "Brief explanation of your routing decision",
  "clarification_question": null
}

PARAMETER RULES:
- Measure: set ONLY for a question about an existing portfolio's own figures. "allocation" for how the portfolio is divided up, which positions sit in a bucket, or how large a position is; "position_pnl" for how a position or the holdings have performed, gained, lost or done since purchase; "portfolio_volatility" for the volatility of the portfolio as a whole. Otherwise null.
- Group by: with measure "allocation", "asset_class", "sector" or "position" when the user names one; null when they do not. Always null for any other measure.
- Status: with intent compliance, "breach" when the user asks which positions, clauses or limits are over, breached, violated or outside - a list of what is over; null when they ask whether the portfolio or one named position complies, what the policy says, or about a proposed weight. Always null for any other intent.

CONFIDENCE GUIDELINES:
- 0.9+: Clear, unambiguous request with all info provided
- 0.7-0.9: Reasonable inference needed, but intent is clear
- 0.5-0.7: Some ambiguity, may need assumptions
- <0.5: Significant ambiguity, consider asking for clarification

EXAMPLES:

User: "Optimiere mein Portfolio mit SPY, TLT, GLD bei maximal 12% Volatilität"
→ intent: "optimization"

User: "Wie ist die aktuelle Marktlage?"
→ intent: "macro_analysis", confidence: 0.95

User: "Backteste die Strategie über 5 Jahre"
→ intent: "backtest"

User: "What is my volatility over the past twelve months?"
→ intent: "risk_analysis", measure: "portfolio_volatility", confidence: 0.95

User: "What is the risk of my portfolio?"
→ intent: "risk_analysis", measure: null, confidence: 0.9

User: "What is my current allocation by asset class?"
→ intent: "data_fetch", measure: "allocation", group_by: "asset_class", confidence: 0.9

User: "How has my JPM position performed since I bought it?"
→ intent: "data_fetch", measure: "position_pnl", confidence: 0.9

User: "How are my positions doing?" (active portfolio)
→ intent: "data_fetch", measure: "position_pnl", confidence: 0.85

User: "Is NEE up or down?" (active portfolio holding NEE)
→ intent: "data_fetch", measure: "position_pnl", confidence: 0.85
   Reasoning: NEE is a holding, so this asks about the position's gain or loss, not about the stock - not a bare price fetch and not out_of_scope.

User: "Portfolio"
→ intent: "clarification_needed", clarification_question: "Was möchten Sie mit Ihrem Portfolio tun? Optimieren, analysieren, oder rebalancen?"

User: "Lohnt es sich, jetzt in Siemens einzusteigen?"
→ intent: "out_of_scope", confidence: 0.95
   Reasoning: Asks whether to own a security; the system makes no such judgement.

User: "Darf ich 20% in eine einzelne Aktie stecken?" (active portfolio)
→ intent: "compliance", confidence: 0.9
   Reasoning: A proposed weight in one position is checked against the policy's limits; no portfolio figure is needed.

User: "What does my policy say about borrowing against the account?"
→ intent: "compliance", confidence: 0.9

CRITICAL RULES:
1. If unsure, set confidence low and/or ask for clarification
2. Keep reasoning brief (1-2 sentences)
3. Measure "allocation" ONLY when the user asks how an existing portfolio
   is divided up - its allocation, breakdown or composition by asset class,
   sector or region, or which positions sit in one of those buckets - and
   "position_pnl" when they ask how a position or the holdings have
   performed since purchase. An unnamed "my position" or "my positions"
   with an active portfolio means every position: set the measure rather
   than asking which one.
   Measure "portfolio_volatility", with intent risk_analysis, when the user
   asks for the volatility of their portfolio as a whole. Do NOT set a
   measure for other risk questions - VaR, drawdown, concentration, or a
   general "what is my risk": those keep intent risk_analysis with measure
   null. "My portfolio" appearing in a question is not by itself a reason
   to set one.
4. A compliance question has exactly one of three readings. Whether the
   existing portfolio complies, breaks a rule, is within its limits, or a
   position is too big: the portfolio check. A proposed weight in one
   position: no portfolio is measured. That reading needs a weight stated
   in the message; with none, a question about complying, limits, or what
   must change is the portfolio check, not a clarification. What the policy
   says about a topic: the lookup. All three are intent compliance; which
   one is read from the message.
"""


def _render_intents() -> str:
    return "\n".join(f"- {value}: {description}" for value, description in INTENTS.items())


def _render_intent_line() -> str:
    return "|".join(INTENTS)


ROUTER_SYSTEM_PROMPT = (
    _PROMPT_BEFORE_INTENTS
    + _render_intents()
    + _PROMPT_AFTER_INTENTS
    + _render_intent_line()
    + _PROMPT_AFTER_INTENT_LINE
)

# =============================================================================
# FEW-SHOT EXAMPLES (for better accuracy)
# =============================================================================

ROUTER_FEW_SHOT_EXAMPLES = [
    {
        "user": "Erstelle ein risiko-optimiertes Portfolio mit SPY, TLT, GLD, VWO",
        "response": {
            "intent": "optimization",
            "confidence": 0.9,
            "parameters": {"measure": None, "group_by": None},
            "reasoning": "User wants a portfolio optimised over four ETFs.",
        }
    },
    {
        "user": "Was sagt der VIX gerade? Ist Risk-On oder Risk-Off?",
        "response": {
            "intent": "macro_analysis",
            "confidence": 0.95,
            "parameters": {"measure": None, "group_by": None},
            "reasoning": "Clear request for macro analysis - VIX and regime assessment.",
        }
    },
    {
        "user": "Mein Portfolio ist SPY 45%, TLT 25%, GLD 20%, VWO 10%. Soll 40/30/15/15 sein. Soll ich rebalancen?",
        "response": {
            "intent": "rebalancing",
            "confidence": 0.95,
            "parameters": {"measure": None, "group_by": None},
            "reasoning": "User provided current and target weights and asks whether to rebalance.",
        }
    }
]


# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_router_prompt(
    user_message: str,
    include_examples: bool = True,
    portfolio_context: Optional[str] = None
) -> str:
    """
    Build the complete router prompt.

    The model is shown no history and no roster: memory is an extraction
    rule over the record of what was asked (agents/extraction.resolve),
    and the plan is derived, so the model names no agent.
    
    Args:
        user_message: The current user request
        include_examples: Whether to include few-shot examples
        portfolio_context: One paragraph saying the portfolio exists, or None
    
    Returns:
        Complete prompt string
    """
    parts = [ROUTER_SYSTEM_PROMPT]
    
    # Add few-shot examples if requested
    if include_examples:
        parts.append("\nEXAMPLES:")
        for i, example in enumerate(ROUTER_FEW_SHOT_EXAMPLES[:3], 1):  # Limit to 3 for token efficiency
            parts.append(f"\nExample {i}:")
            parts.append(f"User: \"{example['user']}\"")
            parts.append(f"Response: {example['response']}")
    
    # Add portfolio context if provided
    if portfolio_context:
        parts.append("\nPORTFOLIO CONTEXT:")
        parts.append(portfolio_context)

    # Add the current request
    parts.append(f"\nCURRENT REQUEST:")
    parts.append(f"User: \"{user_message}\"")
    parts.append("\nRespond with valid JSON only:")
    
    return "\n".join(parts)


# =============================================================================
# RESPONSE REPAIR PROMPT
# =============================================================================

_REPAIR_BEFORE_INTENT_LINE = """The previous response was invalid JSON or didn't match the required schema.

ERROR: {error}

Please fix and return ONLY valid JSON matching this schema:
{{
  "intent": \""""

_REPAIR_AFTER_INTENT_LINE = """\",
  "confidence": 0.0-1.0,
  "parameters": {{"measure": null, "group_by": null, "status": null}},
  "reasoning": "...",
  "clarification_question": null
}}

Original request was: "{user_message}"
"""

REPAIR_PROMPT = _REPAIR_BEFORE_INTENT_LINE + _render_intent_line() + _REPAIR_AFTER_INTENT_LINE


def build_repair_prompt(user_message: str, error: str) -> str:
    """Build a repair prompt when the first response fails validation."""
    return REPAIR_PROMPT.format(error=error, user_message=user_message)
