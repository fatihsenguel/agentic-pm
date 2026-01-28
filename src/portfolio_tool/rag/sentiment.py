# src/portfolio_tool/rag/sentiment.py
"""
Fed Minutes Sentiment Analysis - Hybrid Approach.

Phase: 6.7 - RAG Integration (Phase 3: RAG Agent)

PURPOSE:
Analyze Federal Reserve meeting minutes for hawkish/dovish sentiment:
- Rule-based: Fast, free, deterministic keyword scoring
- LLM-based: Accurate, nuanced analysis when rules are uncertain
- Hybrid: Rules first, LLM only when needed

DESIGN PRINCIPLES:
- Deterministic decision tree (no LLM decides when to use LLM)
- Config-driven thresholds (easily adjustable)
- Hot Potato: LLM receives summarized text, not full minutes
- Auditable: Returns method used and signals detected
- Graceful fallback: LLM failure → rule-based with warning

USAGE:
    from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
    
    analyzer = FedSentimentAnalyzer()
    result = analyzer.analyze(fed_minutes_text)
    
    print(result["score"])      # -1 (dovish) to +1 (hawkish)
    print(result["confidence"]) # 0-1
    print(result["method"])     # "rule_based", "llm", or "hybrid"

INTEGRATION:
    Your macro_agent.py calls:
        result = self.sentiment_analyzer.analyze(doc)
    
    This module provides exactly that interface.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SentimentConfig:
    """
    Configuration for sentiment analysis.
    
    Add to your config.py or use standalone.
    All thresholds are easily adjustable.
    """
    # LLM Settings
    llm_enabled: bool = True
    llm_provider: str = "openai"  # "openai" or "anthropic"
    llm_model: str = "gpt-4o-mini"  # Cost-effective, good for classification
    llm_max_tokens: int = 500  # Max tokens for LLM response
    llm_temperature: float = 0.0  # Deterministic responses
    
    # Text Processing
    summary_max_tokens: int = 500  # Summarize fed minutes to this size before LLM
    
    # Hybrid Decision Thresholds
    confidence_threshold: float = 0.6  # Below this → use LLM
    ambiguity_threshold: float = 0.2   # Score within ±this of 0 → use LLM
    
    # Rule-based weights (adjustable)
    hawkish_weight: float = 1.0
    dovish_weight: float = 1.0
    
    # Retry settings
    llm_retry_count: int = 1
    llm_timeout: int = 30


# =============================================================================
# KEYWORD DICTIONARIES
# =============================================================================

# Hawkish signals (Fed tightening, inflation concerns)
HAWKISH_KEYWORDS = {
    # Strong hawkish (weight 2.0)
    "inflation remains elevated": 2.0,
    "inflation is too high": 2.0,
    "price stability": 1.5,
    "raise rates": 2.0,
    "rate increase": 2.0,
    "further tightening": 2.0,
    "restrictive stance": 1.8,
    "reduce balance sheet": 1.5,
    "quantitative tightening": 1.5,
    
    # Moderate hawkish (weight 1.0)
    "labor market remains tight": 1.0,
    "labor market tight": 1.0,
    "strong labor market": 0.8,
    "robust employment": 0.8,
    "wage pressures": 1.0,
    "wage growth": 0.7,
    "core inflation": 0.8,
    "inflation expectations": 0.7,
    "above target": 1.2,
    "2 percent target": 0.5,  # Neutral but often in hawkish context
    "higher for longer": 1.5,
    "maintain rates": 0.5,
    "hold rates": 0.5,
    
    # Mild hawkish (weight 0.5)
    "upside risks": 0.5,
    "inflation risks": 0.6,
    "vigilant": 0.5,
    "data dependent": 0.3,
    "monitoring inflation": 0.4,
}

# Dovish signals (Fed easing, growth concerns)
DOVISH_KEYWORDS = {
    # Strong dovish (weight 2.0)
    "rate cut": 2.0,
    "lower rates": 2.0,
    "reduce rates": 2.0,
    "easing": 1.8,
    "accommodation": 1.5,
    "support growth": 1.5,
    "support the economy": 1.5,
    "recession risk": 2.0,
    "recession concerns": 1.8,
    "economic slowdown": 1.8,
    
    # Moderate dovish (weight 1.0)
    "slowing economy": 1.2,
    "growth concerns": 1.0,
    "labor market cooling": 1.2,
    "labor market softening": 1.2,
    "unemployment rising": 1.5,
    "job losses": 1.5,
    "inflation declining": 1.2,
    "inflation falling": 1.2,
    "disinflation": 1.3,
    "below target": 1.0,
    "downside risks": 1.0,
    "financial conditions tightening": 0.8,
    
    # Mild dovish (weight 0.5)
    "balanced risks": 0.5,
    "patient": 0.6,
    "gradual": 0.5,
    "cautious": 0.5,
    "uncertainty": 0.4,
    "wait and see": 0.6,
}


# =============================================================================
# SENTIMENT RESULT
# =============================================================================

@dataclass
class SentimentResult:
    """Structured sentiment analysis result."""
    success: bool
    score: float  # -1 (dovish) to +1 (hawkish)
    confidence: float  # 0-1
    method: str  # "rule_based", "llm", or "hybrid"
    
    # Details
    hawkish_signals: List[str] = field(default_factory=list)
    dovish_signals: List[str] = field(default_factory=list)
    
    # LLM details (if used)
    llm_used: bool = False
    llm_raw_response: Optional[str] = None
    
    # Error tracking
    error: Optional[str] = None
    warning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (matches macro_agent.py expected format)."""
        return {
            "success": self.success,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "signals": self.hawkish_signals + self.dovish_signals,
            "hawkish_signals": self.hawkish_signals,
            "dovish_signals": self.dovish_signals,
            "llm_used": self.llm_used,
            "error": self.error,
            "warning": self.warning,
        }


# =============================================================================
# RULE-BASED ANALYZER
# =============================================================================

class RuleBasedSentiment:
    """
    Deterministic keyword-based sentiment scoring.
    
    Fast, free, and predictable. Forms the foundation of hybrid approach.
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
    
    def analyze(self, text: str) -> Tuple[float, float, List[str], List[str]]:
        """
        Analyze text using keyword matching.
        
        Args:
            text: Fed minutes text
            
        Returns:
            Tuple of (score, confidence, hawkish_signals, dovish_signals)
        """
        text_lower = text.lower()
        
        # Count hawkish signals
        hawkish_score = 0.0
        hawkish_signals = []
        for phrase, weight in HAWKISH_KEYWORDS.items():
            count = len(re.findall(re.escape(phrase), text_lower))
            if count > 0:
                hawkish_score += weight * count * self.config.hawkish_weight
                hawkish_signals.append(f"{phrase} (×{count})")
        
        # Count dovish signals
        dovish_score = 0.0
        dovish_signals = []
        for phrase, weight in DOVISH_KEYWORDS.items():
            count = len(re.findall(re.escape(phrase), text_lower))
            if count > 0:
                dovish_score += weight * count * self.config.dovish_weight
                dovish_signals.append(f"{phrase} (×{count})")
        
        # Calculate net score (-1 to +1)
        total_signals = hawkish_score + dovish_score
        if total_signals == 0:
            score = 0.0
            confidence = 0.3  # Low confidence when no signals found
        else:
            # Net score: positive = hawkish, negative = dovish
            raw_score = (hawkish_score - dovish_score) / total_signals
            score = max(-1.0, min(1.0, raw_score))  # Clamp to [-1, 1]
            
            # Confidence based on signal strength
            signal_strength = min(total_signals / 10.0, 1.0)  # Normalize
            balance = 1.0 - abs(hawkish_score - dovish_score) / (total_signals + 0.01)
            confidence = signal_strength * (1.0 - balance * 0.5)  # Reduce confidence if balanced
            confidence = max(0.3, min(0.95, confidence))  # Clamp to [0.3, 0.95]
        
        return score, confidence, hawkish_signals, dovish_signals


# =============================================================================
# LLM ANALYZER
# =============================================================================

class LLMSentiment:
    """
    LLM-based sentiment analysis using GPT.
    
    More accurate but costs tokens. Used when rule-based is uncertain.
    """
    
    SYSTEM_PROMPT = """You are a Federal Reserve policy analyst. Analyze the following Fed minutes excerpt for monetary policy sentiment.

Rate the sentiment on a scale from -1.0 to +1.0:
- -1.0 = Strongly dovish (likely to cut rates, support growth)
- 0.0 = Neutral (balanced, no clear direction)
- +1.0 = Strongly hawkish (likely to raise rates, fight inflation)

Also rate your confidence from 0.0 to 1.0.

Respond ONLY with valid JSON in this exact format:
{"score": 0.0, "confidence": 0.0, "reasoning": "brief explanation"}"""

    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self._client = None
    
    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()  # Uses OPENAI_API_KEY
                logger.info("OpenAI client initialized for sentiment analysis")
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client
    
    def analyze(self, text: str) -> Tuple[float, float, str]:
        """
        Analyze text using LLM.
        
        Args:
            text: Fed minutes text (should be pre-summarized)
            
        Returns:
            Tuple of (score, confidence, raw_response)
            
        Raises:
            Exception on API error (caller should handle)
        """
        # Truncate if too long (shouldn't happen if pre-summarized)
        if len(text) > self.config.summary_max_tokens * 4:
            text = text[:self.config.summary_max_tokens * 4] + "..."
        
        response = self.client.chat.completions.create(
            model=self.config.llm_model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this Fed minutes excerpt:\n\n{text}"}
            ],
            max_tokens=self.config.llm_max_tokens,
            temperature=self.config.llm_temperature,
            timeout=self.config.llm_timeout,
        )
        
        raw_response = response.choices[0].message.content
        
        # Parse JSON response
        import json
        try:
            # Handle markdown code blocks
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            
            result = json.loads(cleaned)
            score = float(result.get("score", 0.0))
            confidence = float(result.get("confidence", 0.7))
            
            # Validate ranges
            score = max(-1.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))
            
            return score, confidence, raw_response
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {raw_response}")
            # Return neutral with low confidence on parse error
            return 0.0, 0.4, raw_response


# =============================================================================
# HYBRID ANALYZER (MAIN CLASS)
# =============================================================================

class FedSentimentAnalyzer:
    """
    Hybrid Fed Minutes sentiment analyzer.
    
    Combines rule-based and LLM approaches:
    1. Always run rule-based (fast, free)
    2. If confidence low OR score ambiguous → use LLM
    3. Blend results with weighted average
    
    This is the main class your macro_agent.py should use.
    
    Usage:
        analyzer = FedSentimentAnalyzer()
        result = analyzer.analyze(fed_minutes_text)
        
        # result is a dict with: success, score, confidence, method, signals
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        """
        Initialize hybrid analyzer.
        
        Args:
            config: SentimentConfig (uses defaults if not provided)
        """
        self.config = config or SentimentConfig()
        self._rule_analyzer = RuleBasedSentiment(self.config)
        self._llm_analyzer = None  # Lazy load
    
    @property
    def llm_analyzer(self) -> LLMSentiment:
        """Lazy-load LLM analyzer."""
        if self._llm_analyzer is None:
            self._llm_analyzer = LLMSentiment(self.config)
        return self._llm_analyzer
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze Fed minutes for sentiment.
        
        This is the main entry point, matching macro_agent.py's expected interface.
        
        Args:
            text: Fed minutes text (full or excerpt)
            
        Returns:
            Dict with: success, score, confidence, method, signals, etc.
        """
        if not text or not text.strip():
            return SentimentResult(
                success=False,
                score=0.0,
                confidence=0.0,
                method="none",
                error="Empty text provided"
            ).to_dict()
        
        # Step 1: Always run rule-based analysis
        rule_score, rule_confidence, hawkish_signals, dovish_signals = \
            self._rule_analyzer.analyze(text)
        
        logger.debug(f"Rule-based: score={rule_score:.2f}, confidence={rule_confidence:.2f}")
        
        # Step 2: Decide if LLM is needed (DETERMINISTIC decision)
        needs_llm = self._needs_llm_refinement(rule_score, rule_confidence)
        
        # Step 3: Run LLM if needed and enabled
        llm_used = False
        llm_raw_response = None
        warning = None
        final_score = rule_score
        final_confidence = rule_confidence
        method = "rule_based"
        
        if needs_llm and self.config.llm_enabled:
            try:
                # Summarize text for LLM (Hot Potato principle)
                summary = self._summarize_for_llm(text)
                
                # Run LLM analysis
                llm_score, llm_confidence, llm_raw_response = \
                    self.llm_analyzer.analyze(summary)
                
                llm_used = True
                logger.debug(f"LLM: score={llm_score:.2f}, confidence={llm_confidence:.2f}")
                
                # Step 4: Blend results
                final_score, final_confidence = self._blend_results(
                    rule_score, rule_confidence,
                    llm_score, llm_confidence
                )
                method = "hybrid"
                
            except Exception as e:
                # Fallback to rule-based with warning
                warning = f"LLM analysis failed: {str(e)}. Using rule-based only."
                logger.warning(warning)
                method = "rule_based"
        
        elif needs_llm and not self.config.llm_enabled:
            warning = "LLM refinement recommended but disabled. Using rule-based only."
            logger.info(warning)
        
        # Build result
        result = SentimentResult(
            success=True,
            score=final_score,
            confidence=final_confidence,
            method=method,
            hawkish_signals=hawkish_signals[:5],  # Top 5
            dovish_signals=dovish_signals[:5],
            llm_used=llm_used,
            llm_raw_response=llm_raw_response,
            warning=warning,
        )
        
        return result.to_dict()
    
    def _needs_llm_refinement(self, score: float, confidence: float) -> bool:
        """
        Determine if LLM refinement is needed.
        
        DETERMINISTIC decision based on config thresholds.
        No LLM is used to make this decision.
        """
        # Low confidence from rules
        if confidence < self.config.confidence_threshold:
            logger.debug(f"LLM needed: confidence {confidence:.2f} < {self.config.confidence_threshold}")
            return True
        
        # Ambiguous score (near neutral)
        if abs(score) < self.config.ambiguity_threshold:
            logger.debug(f"LLM needed: score {score:.2f} within ambiguity threshold {self.config.ambiguity_threshold}")
            return True
        
        return False
    
    def _summarize_for_llm(self, text: str) -> str:
        """
        Summarize text before sending to LLM.
        
        Hot Potato principle: Don't send full minutes (~10k tokens).
        Extract key sections and limit length.
        """
        # Key sections to prioritize
        key_phrases = [
            "committee decided",
            "participants noted",
            "inflation",
            "employment",
            "economic activity",
            "policy",
            "rate",
            "outlook",
        ]
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        # Score paragraphs by relevance
        scored = []
        for para in paragraphs:
            para = para.strip()
            if len(para) < 50:
                continue
            
            score = sum(1 for phrase in key_phrases if phrase in para.lower())
            scored.append((score, para))
        
        # Sort by relevance and take top paragraphs
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Build summary within token limit (~4 chars per token)
        max_chars = self.config.summary_max_tokens * 4
        summary_parts = []
        current_length = 0
        
        for score, para in scored:
            if current_length + len(para) > max_chars:
                break
            summary_parts.append(para)
            current_length += len(para)
        
        if not summary_parts:
            # Fallback: just take first N characters
            return text[:max_chars]
        
        return "\n\n".join(summary_parts)
    
    def _blend_results(
        self,
        rule_score: float,
        rule_confidence: float,
        llm_score: float,
        llm_confidence: float,
    ) -> Tuple[float, float]:
        """
        Blend rule-based and LLM results.
        
        Weighted average where weights are confidence scores.
        """
        total_confidence = rule_confidence + llm_confidence
        
        if total_confidence == 0:
            return 0.0, 0.5
        
        # Weighted average of scores
        blended_score = (
            rule_score * rule_confidence + llm_score * llm_confidence
        ) / total_confidence
        
        # Take max confidence (if either is confident, we're confident)
        blended_confidence = max(rule_confidence, llm_confidence)
        
        # Boost confidence if they agree
        if (rule_score > 0 and llm_score > 0) or (rule_score < 0 and llm_score < 0):
            blended_confidence = min(blended_confidence * 1.1, 0.95)
        
        return blended_score, blended_confidence
    
    # Convenience method for compatibility
    def get_sentiment(self, text: str) -> Dict[str, Any]:
        """Alias for analyze() for compatibility."""
        return self.analyze(text)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_fed_sentiment(
    text: str,
    use_llm: bool = True,
    config: Optional[SentimentConfig] = None,
) -> Dict[str, Any]:
    """
    Convenience function for one-off sentiment analysis.
    
    Args:
        text: Fed minutes text
        use_llm: Whether to enable LLM (default True)
        config: Optional config override
        
    Returns:
        Sentiment result dict
    """
    if config is None:
        config = SentimentConfig(llm_enabled=use_llm)
    else:
        config.llm_enabled = use_llm
    
    analyzer = FedSentimentAnalyzer(config)
    return analyzer.analyze(text)


def get_rule_based_sentiment(text: str) -> Dict[str, Any]:
    """
    Get rule-based sentiment only (no LLM).
    
    Fast and free, useful for batch processing.
    """
    config = SentimentConfig(llm_enabled=False)
    analyzer = FedSentimentAnalyzer(config)
    return analyzer.analyze(text)
