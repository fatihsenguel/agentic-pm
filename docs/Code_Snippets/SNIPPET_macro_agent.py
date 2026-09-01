"""
Macro Agent for Quant Portfolio Manager.
Analyzes macro environment (Fed Minutes, VIX, Yield Curve) to provide TAA SIGNALS.
Does NOT execute trades directly.
"""
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
# [Standard imports omitted...]

class MarketRegime(str, Enum):
    RISK_ON = "risk_on"; RISK_OFF = "risk_off"; NEUTRAL = "neutral"
    CRISIS = "crisis"; RECOVERY = "recovery"

@dataclass
class MacroSignal:
    """Combined macro signal for TAA."""
    fed_sentiment: float    # -1 to +1
    fed_confidence: float   # 0 to 1
    vix_level: float
    vix_regime: str         # "low", "normal", "elevated", "crisis"
    yield_curve_slope: Optional[float] = None
    yield_curve_signal: str = "neutral"
    regime: MarketRegime = MarketRegime.NEUTRAL
    regime_confidence: float = 0.5
    risk_stance: str = "neutral"
    equity_adjustment: float = 0.0
    analysis_date: datetime = None # Defaults to now

    def to_dict(self) -> Dict[str, Any]:
        """Returns full dict representation for serialization."""
        pass 

@dataclass
class MacroAgentConfig(AgentConfig):
    vix_low: float = 15.0; vix_elevated: float = 25.0; vix_crisis: float = 35.0
    hawkish_threshold: float = 0.3; dovish_threshold: float = -0.3
    max_equity_adjustment: float = 0.15 

class MacroAgent(BaseAgent):
    """Provides SIGNALS for TAA parameter adjustment."""

    async def process(self, state: AgentState) -> AgentState:
        """
        1. Gets 'vix_level', 'yield_curve_slope', 'fed_document' from shared_data.
        2. If 'fed_document' exists, runs sentiment_analyzer.analyze(doc).
        3. Calls self._generate_signal(...).
        4. Updates state.shared_data with 'macro_signal' and 'regime_signal'.
        """
        # ... [Extraction logic] ...
        
        # Core logic execution
        signal = self._generate_signal(
            fed_sentiment=fed_sentiment,
            fed_confidence=fed_confidence,
            vix_level=vix_level,
            yield_curve=yield_curve
        )
        
        # ... [State update and logging] ...
        return state

    def _generate_signal(self, fed_sentiment: float, fed_confidence: float, 
                         vix_level: float, yield_curve: Optional[float] = None) -> MacroSignal:
        """Core logic to combine indicators."""
        
        # 1. Determine VIX Regime
        if vix_level < self.config.vix_low: vix_regime = "low"
        elif vix_level < self.config.vix_elevated: vix_regime = "normal"
        elif vix_level < self.config.vix_crisis: vix_regime = "elevated"
        else: vix_regime = "crisis"
        
        # 2. Determine Yield Curve Signal
        yield_signal = "neutral"
        if yield_curve is not None:
            if yield_curve < -0.2: yield_signal = "inverted"
            elif yield_curve < 0.5: yield_signal = "flat"
            elif yield_curve > 1.0: yield_signal = "steep"
        
        # 3. Determine Regime
        regime = self._determine_regime(fed_sentiment, vix_regime, yield_signal)
        
        # 4. Calculate Confidence
        regime_confidence = self._calculate_regime_confidence(fed_confidence, vix_regime)
        
        # 5. Determine Stance & Adjustment
        risk_stance, equity_adjustment = self._determine_risk_stance(regime, fed_sentiment, vix_regime)
        
        return MacroSignal(fed_sentiment, fed_confidence, vix_level, vix_regime, 
                           yield_curve, yield_signal, regime, regime_confidence, 
                           risk_stance, equity_adjustment)

    def _determine_regime(self, fed_sentiment: float, vix_regime: str, yield_signal: str) -> MarketRegime:
        """Logic tree for regime classification."""
        if vix_regime == "crisis": return MarketRegime.CRISIS
        
        risk_off_signals = 0; risk_on_signals = 0
        
        # Fed Logic
        if fed_sentiment > self.config.hawkish_threshold: risk_off_signals += 1
        elif fed_sentiment < self.config.dovish_threshold: risk_on_signals += 1
        
        # VIX Logic
        if vix_regime == "elevated": risk_off_signals += 1
        elif vix_regime == "low": risk_on_signals += 1
        
        # Yield Logic
        if yield_signal == "inverted": risk_off_signals += 2  # Strong signal
        elif yield_signal == "steep": risk_on_signals += 1
        
        if risk_off_signals >= 3: return MarketRegime.RISK_OFF
        elif risk_on_signals >= 2 and risk_off_signals == 0: return MarketRegime.RISK_ON
        elif risk_on_signals > risk_off_signals: return MarketRegime.RECOVERY
        else: return MarketRegime.NEUTRAL

    def _calculate_regime_confidence(self, fed_confidence: float, vix_regime: str) -> float:
        confidence = fed_confidence * 0.5
        if vix_regime in ["crisis", "low"]: confidence += 0.3
        elif vix_regime == "elevated": confidence += 0.2
        else: confidence += 0.1
        return min(0.95, confidence)

    def _determine_risk_stance(self, regime: MarketRegime, fed_sentiment: float, vix_regime: str) -> tuple:
        """Calculates equity_adjustment float."""
        max_adj = self.config.max_equity_adjustment
        
        if regime == MarketRegime.CRISIS:
            return "defensive", -max_adj
        
        elif regime == MarketRegime.RISK_OFF:
            adj = -max_adj * 0.6
            if vix_regime == "elevated": adj -= max_adj * 0.2
            return "risk_off", adj
        
        elif regime == MarketRegime.RISK_ON:
            adj = max_adj * 0.5
            if fed_sentiment < -0.3: adj += max_adj * 0.2
            return "risk_on", adj
        
        elif regime == MarketRegime.RECOVERY:
            return "cautious_risk_on", max_adj * 0.3
        
        return "neutral", 0.0

    # ========== TOOLS (Signatures Preserved) ==========

    def analyze_fed_minutes_tool(self, text: str, source: str = "fed_minutes") -> Dict[str, Any]:
        """
        Input: Raw text
        Returns: {score, classification, risk_assessment, key_themes, summary}
        """
        pass

    def assess_regime_tool(self, vix_level: float, fed_sentiment: float = 0.0, 
                           yield_curve_slope: Optional[float] = None) -> Dict[str, Any]:
        """
        Input: Indicators
        Returns: Dict version of MacroSignal (regime, equity_adjustment, etc.)
        """
        pass

    def generate_macro_signal_tool(self, fed_text: Optional[str] = None, vix_level: float = 20.0, 
                                   yield_curve_slope: Optional[float] = None) -> Dict[str, Any]:
        """
        Input: Optional text + indicators
        Returns: Complete MacroSignal with summary
        """
        pass

    def search_fed_minutes_tool(self, query: str, fed_text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Input: Query and text
        Returns: {results: [{rank, score, section, text}]} via Vector Store
        """
        pass