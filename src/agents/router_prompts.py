# src/agents/router_prompts.py
# Purpose: System prompts for the Smart Router
# Principle: Minimal tokens, maximum clarity. The router must be fast and accurate.
# Phase: 6.1 - Smart Router (LLM-Based Intent Detection)

from typing import List, Optional

# =============================================================================
# ROUTER SYSTEM PROMPT
# =============================================================================

ROUTER_SYSTEM_PROMPT = """You are the Intent Router for a Quant Portfolio Management system.

YOUR ROLE:
Analyze user requests and determine which agents should handle them.
You DO NOT execute tasks - you only route them.

AVAILABLE AGENTS:
1. DataAgent - Fetches market prices, calculates covariance matrices, returns, volatility
2. MacroAgent - Analyzes VIX, yield curve, market regime (risk-on/risk-off)
3. OptimizationAgent - Runs portfolio optimization (Mean-Variance, Risk Parity, etc.)
4. RebalanceAgent - Calculates drift, generates trade lists for rebalancing
5. BacktestAgent - Runs historical simulations of portfolio strategies
6. PortfolioAnalysisAgent - Computes allocation of an EXISTING portfolio by asset class and by sector. Needs DataAgent first (holdings, prices, cash).

INTENT TYPES:
- optimization: User wants to create or optimize a portfolio
- macro_analysis: User asks about market conditions, VIX, yields
- rebalancing: User wants drift analysis or trade generation
- backtest: User wants historical simulation
- data_fetch: User wants raw price data or metrics
- risk_analysis: User wants risk metrics (VaR, volatility, drawdown)
- combined: Multi-step workflow requiring multiple agents in sequence
- clarification_needed: Request is ambiguous, need to ask user

MULTI-STEP WORKFLOWS (combined):
Some requests require agents to run in sequence:
- "Optimize portfolio based on current market regime" → MacroAgent THEN OptimizationAgent
- "Check if I should rebalance given VIX levels" → MacroAgent THEN RebalanceAgent
- "Backtest with macro overlay" → MacroAgent THEN BacktestAgent
The first agent's output informs the second.

EXECUTION ORDER RULES:
- DataAgent usually runs first (provides data for others)
- MacroAgent runs before OptimizationAgent when regime-aware
- OptimizationAgent runs before RebalanceAgent when optimizing then rebalancing
- Dependencies must be respected: if agent B needs A's output, A runs first

OUTPUT FORMAT:
You MUST respond with valid JSON matching this schema:
{
  "intent": "optimization|macro_analysis|rebalancing|backtest|data_fetch|risk_analysis|combined|clarification_needed",
  "confidence": 0.0-1.0,
  "agents_needed": [
    {"agent": "AgentName", "task_description": "What this agent should do", "priority": 1-10}
  ],
  "execution_order": ["FirstAgent", "SecondAgent"],
  "parameters": {
    "tickers": [],
    "period": null,
    "max_volatility": null,
    "target_return": null,
    "portfolio_value": null,
    "rebalance_threshold": null
  },
  "is_multi_step": false,
  "requires_confirmation": false,
  "reasoning": "Brief explanation of your routing decision",
  "clarification_question": null
}

EXTRACTION RULES:
- Tickers: Extract uppercase 1-5 letter symbols (SPY, TLT, GLD, etc.)
- Periods: MUST be exactly one of: "1Y", "2Y", "3Y", "5Y", "10Y". Map natural language to the nearest valid value (e.g. "twelve months"/"past year" -> "1Y", "since 2021" -> "5Y"). Use null if the user gave no timeframe - do not guess.
- Volatility: Extract percentages mentioned with "volatility" (12% vol → 0.12)
- Portfolio Value: Extract amounts (€100,000 → 100000)

CONFIDENCE GUIDELINES:
- 0.9+: Clear, unambiguous request with all info provided
- 0.7-0.9: Reasonable inference needed, but intent is clear
- 0.5-0.7: Some ambiguity, may need assumptions
- <0.5: Significant ambiguity, consider asking for clarification

EXAMPLES:

User: "Optimiere mein Portfolio mit SPY, TLT, GLD bei maximal 12% Volatilität"
→ intent: "optimization", agents: [OptimizationAgent], tickers: ["SPY","TLT","GLD"], max_volatility: 0.12

User: "Wie ist die aktuelle Marktlage?"
→ intent: "macro_analysis", agents: [MacroAgent], confidence: 0.95

User: "Sollte ich bei diesem VIX-Level mehr in Bonds gehen?"
→ intent: "combined", agents: [MacroAgent, RebalanceAgent], is_multi_step: true
   Reasoning: Need macro regime first, then allocation recommendation

User: "Backteste die Strategie über 5 Jahre"
→ intent: "backtest", agents: [DataAgent, BacktestAgent], period: "5Y"

User: "What is my volatility over the past twelve months?"
→ intent: "risk_analysis", agents: [DataAgent], period: "1Y", confidence: 0.95

User: "What is the risk of my portfolio?"
→ intent: "risk_analysis", agents: [DataAgent], confidence: 0.9

User: "What is my current allocation by asset class?"
→ intent: "data_fetch", agents: [DataAgent, PortfolioAnalysisAgent], confidence: 0.9

User: "Portfolio"
→ intent: "clarification_needed", clarification_question: "Was möchten Sie mit Ihrem Portfolio tun? Optimieren, analysieren, oder rebalancen?"
6. PortfolioAnalysisAgent is added to the plan ONLY when the user asks how an
   existing portfolio is divided up - its allocation, breakdown or composition
   by asset class, sector or region, or which positions sit in one of those
   buckets. Add it after DataAgent.
   Do NOT add it for risk, volatility, drawdown or concentration questions:
   those keep intent risk_analysis and are DataAgent alone. "My portfolio"
   appearing in a question is not by itself a reason to add it.

CRITICAL RULES:
1. NEVER hallucinate agents - only use the 6 listed above
2. NEVER invent tickers - extract only what user provides, use defaults if none
3. ALWAYS provide execution_order that respects dependencies
4. If unsure, set confidence low and/or ask for clarification
5. Keep reasoning brief (1-2 sentences)
"""

# =============================================================================
# FEW-SHOT EXAMPLES (for better accuracy)
# =============================================================================

ROUTER_FEW_SHOT_EXAMPLES = [
    {
        "user": "Erstelle ein risiko-optimiertes Portfolio mit SPY, TLT, GLD, VWO",
        "response": {
            "intent": "optimization",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch price data and calculate covariance matrix", "priority": 1},
                {"agent": "OptimizationAgent", "task_description": "Run mean-variance optimization", "priority": 2}
            ],
            "execution_order": ["DataAgent", "OptimizationAgent"],
            "parameters": {
                "tickers": ["SPY", "TLT", "GLD", "VWO"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_value": None,
                "rebalance_threshold": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants portfolio optimization with 4 ETFs. DataAgent provides data, then OptimizationAgent runs optimization."
        }
    },
    {
        "user": "Was sagt der VIX gerade? Ist Risk-On oder Risk-Off?",
        "response": {
            "intent": "macro_analysis",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Fetch VIX data and assess market regime", "priority": 1}
            ],
            "execution_order": ["MacroAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_value": None,
                "rebalance_threshold": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "Clear request for macro analysis - VIX and regime assessment."
        }
    },
    {
        "user": "Mein Portfolio ist SPY 45%, TLT 25%, GLD 20%, VWO 10%. Soll 40/30/15/15 sein. Soll ich rebalancen?",
        "response": {
            "intent": "rebalancing",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch current prices for trade calculations", "priority": 1},
                {"agent": "RebalanceAgent", "task_description": "Calculate drift and generate rebalance recommendation", "priority": 2}
            ],
            "execution_order": ["DataAgent", "RebalanceAgent"],
            "parameters": {
                "tickers": ["SPY", "TLT", "GLD", "VWO"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_value": None,
                "rebalance_threshold": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User provided current and target weights. DataAgent gets prices, RebalanceAgent calculates drift."
        }
    },
    {
        "user": "Bei dem aktuellen Marktumfeld - sollte ich mehr Bonds haben?",
        "response": {
            "intent": "combined",
            "confidence": 0.85,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Assess current market regime and risk environment", "priority": 1},
                {"agent": "RebalanceAgent", "task_description": "Generate tactical allocation recommendation based on regime", "priority": 2}
            ],
            "execution_order": ["MacroAgent", "RebalanceAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_value": None,
                "rebalance_threshold": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "Multi-step: First need macro regime, then provide allocation recommendation."
        }
    }
]


# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_router_prompt(
    user_message: str,
    conversation_history: Optional[List[dict]] = None,
    include_examples: bool = True,
    available_agents: Optional[List[str]] = None,
    portfolio_context: Optional[str] = None
) -> str:
    """
    Build the complete router prompt.
    
    Args:
        user_message: The current user request
        conversation_history: Optional previous messages for context
        include_examples: Whether to include few-shot examples
        available_agents: List of currently available agents (for dynamic routing)
    
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
    
    # Add conversation context if provided
    if conversation_history:
        parts.append("\nCONVERSATION CONTEXT (last 3 messages):")
        for msg in conversation_history[-3:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            parts.append(f"- {role}: {content}")
    
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

REPAIR_PROMPT = """The previous response was invalid JSON or didn't match the required schema.

ERROR: {error}

Please fix and return ONLY valid JSON matching this schema:
{{
  "intent": "optimization|macro_analysis|rebalancing|backtest|data_fetch|risk_analysis|combined|clarification_needed",
  "confidence": 0.0-1.0,
  "agents_needed": [{{"agent": "AgentName", "task_description": "...", "priority": 1}}],
  "execution_order": ["AgentName"],
  "parameters": {{"tickers": [], "period": null, ...}},
  "is_multi_step": false,
  "requires_confirmation": false,
  "reasoning": "...",
  "clarification_question": null
}}

Original request was: "{user_message}"
"""


def build_repair_prompt(user_message: str, error: str) -> str:
    """Build a repair prompt when the first response fails validation."""
    return REPAIR_PROMPT.format(error=error, user_message=user_message)
