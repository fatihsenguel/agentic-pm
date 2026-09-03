"""
Macro Agent for Quant Portfolio Manager.

The Macro Agent analyzes the macro environment for TAA decisions:
- Market regime detection (VIX, Yield Curve)
- Risk signal generation

⚠️ IMPORTANT SCOPE:
The Macro Agent provides SIGNALS for TAA parameter adjustment.
It does NOT make trade decisions directly.

ARCHITECTURE (Separation of Concerns):
- MacroAgent = Interface/Orchestrator
- DataManager = Database operations (VIX, Yields persistence)

The Agent DELEGATES work to these components, it does NOT implement
raw scraping, calculations, or DB operations directly.
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from .protocols import PortfolioTask, PortfolioResult, RegimeType

from config import config


# ==================== ENUMS & DATA CLASSES ====================

# WICHTIG: Wir verwenden RegimeType aus protocols.py für Konsistenz
# Alias für Rückwärtskompatibilität
MarketRegime = RegimeType


@dataclass
class MacroSignal:
    """
    Combined macro signal for TAA.
    
    Used to adjust portfolio positioning based on macro environment.
    """
    
    # Market indicators
    vix_level: float
    vix_regime: str  # "low", "normal", "elevated", "crisis"
    
    # Yield curve
    yield_curve_slope: Optional[float] = None
    yield_curve_signal: str = "neutral"
    
    # Combined regime
    regime: MarketRegime = MarketRegime.NEUTRAL
    regime_confidence: float = 0.5
    
    # Recommendation
    risk_stance: str = "neutral"
    equity_adjustment: float = 0.0
    
    # Metadata
    analysis_date: datetime = None
    data_source: str = "database"  # "database", "live", "shared_state"
    
    def __post_init__(self):
        if self.analysis_date is None:
            self.analysis_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent responses."""
        return {
            "vix_level": round(self.vix_level, 2),
            "vix_regime": self.vix_regime,
            "yield_curve_slope": round(self.yield_curve_slope, 4) if self.yield_curve_slope else None,
            "yield_curve_signal": self.yield_curve_signal,
            "regime": self.regime.value,
            "regime_confidence": round(self.regime_confidence, 3),
            "risk_stance": self.risk_stance,
            "equity_adjustment": round(self.equity_adjustment, 4),
            "analysis_date": self.analysis_date.isoformat(),
            "data_source": self.data_source,
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 50,
            "MACRO ENVIRONMENT ANALYSIS",
            "=" * 50,
            "",
            "📊 MARKET INDICATORS:",
            f"   VIX Level: {self.vix_level:.1f} ({self.vix_regime.upper()})",
            f"   Yield Curve: {self.yield_curve_signal}",
            "",
            "🎯 REGIME ASSESSMENT:",
            f"   Current Regime: {self.regime.value.upper()}",
            f"   Confidence: {self.regime_confidence:.0%}",
            "",
            "💼 TAA RECOMMENDATION:",
            f"   Risk Stance: {self.risk_stance.upper()}",
            f"   Equity Adjustment: {self.equity_adjustment:+.0%}",
            "",
            f"📅 Analysis Date: {self.analysis_date.strftime('%Y-%m-%d %H:%M')}",
            f"📦 Data Source: {self.data_source}",
            "=" * 50,
        ]
        return "\n".join(lines)

# ==================== MACRO AGENT ====================

class MacroAgent(BaseAgent):
    """
    Macro Agent for analyzing macro environment.
    
    Capabilities:
    - Fetch and persist macro data (VIX, Treasury Yields)
    - Detect market regime
    - Generate TAA signals
    
    ⚠️ This agent provides SIGNALS, not trade decisions.
    
    ARCHITECTURE:
    - Uses DataManager for database operations
    """
    
    def __init__(self, agent_config: Optional[AgentConfig] = None):
        """Initialize Macro Agent."""
        if agent_config is None:
            agent_config = AgentConfig(
                name="MacroAgent",
                role=AgentRole.MACRO,
                temperature=0.0,
            )
        super().__init__(agent_config)
        
        # Lazy-loaded components (Separation of Concerns)
        self._data_manager = None
    
    # ==================== LAZY-LOADED COMPONENTS ====================
    
    @property
    def data_manager(self):
        """Lazy-load DataManager for database operations."""
        if self._data_manager is None:
            from portfolio_tool.data_manager import get_data_manager
            self._data_manager = get_data_manager()
        return self._data_manager
    
    # ==================== AGENT INTERFACE ====================
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides."""
        return [
            "fetch_macro_data",
            "get_macro_snapshot",
            "assess_market_regime",
            "generate_taa_signal",
            "get_vix_analysis",
            "get_yield_curve_analysis",
        ]
    
    def get_tools(self) -> List[Callable]:
        """Get the list of tools available to this agent."""
        return [
            self.fetch_macro_data_tool,
            self.get_macro_snapshot_tool,
            self.get_vix_analysis_tool,
            self.get_yield_curve_analysis_tool,
            self.assess_regime_tool,
            self.generate_taa_signal_tool,
        ]
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are the Macro Agent for a Quant Portfolio Manager system.

Your role is to analyze the macro environment for Tactical Asset Allocation (TAA).

⚠️ IMPORTANT SCOPE LIMITATION:
You provide SIGNALS that inform TAA parameters.
You do NOT make direct trade decisions.
Your output adjusts thresholds and weights, not specific trades.

CAPABILITIES:
1. Macro Data Management
   - Fetch VIX, Treasury Yields from Yahoo Finance
   - Persist data to database for other agents
   - Query historical macro data

2. Market Regime Detection
   - VIX-based volatility regime
   - Yield curve signals (inversion warning)
   - Combined regime classification

3. TAA Signal Generation
   - Risk stance recommendation
   - Equity weight adjustment suggestion
   - Confidence level

VIX REGIMES:
- Low (<15): Complacent, potentially risk_on
- Normal (15-25): Balanced
- Elevated (25-35): Cautious, risk_off
- Crisis (>35): Defensive positioning

YIELD CURVE:
- Inverted (<0): Recession warning
- Flat (0-0.5): Caution
- Normal (0.5-1.5): Healthy
- Steep (>1.5): Growth expectations

OUTPUT FORMAT:
Always provide structured results with:
- success: boolean
- data: relevant metrics
- metadata: source, timestamp, confidence
"""
    
    # ==================== PROCESS METHOD ====================
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Process macro analysis request.
        
        Auto-fetches missing data from database/API if configured.
        Updates shared_data with macro signals for other agents.
        """
        task = state.current_task
        
        if task is None:
            state.add_message("assistant", "No task provided to Macro Agent")
            return state
        
        self.log(f"Processing macro task: {task.task_id}")
        
        shared = state.shared_data
        
        # ===== STEP 1: Get VIX (from shared_data, DB, or fetch) =====
        vix_data = self._get_vix_data(shared)
        vix_level = vix_data.get("current_vix", 20.0)
        vix_regime = vix_data.get("regime", "normal")
        
        # ===== STEP 2: Get Yield Curve (from shared_data, DB, or fetch) =====
        yield_data = self._get_yield_curve_data(shared)
        yield_curve_slope = yield_data.get("slope_10y_3m")
        yield_curve_signal = yield_data.get("status", "normal")
        
        # ===== STEP 3: Generate Signal =====
        signal = self._generate_signal(
            vix_level=vix_level,
            yield_curve=yield_curve_slope
        )
        
        # ===== STEP 4: Update Shared State =====
        state.shared_data["vix_level"] = vix_level
        state.shared_data["vix_regime"] = vix_regime
        state.shared_data["yield_curve_slope"] = yield_curve_slope
        state.shared_data["yield_curve_signal"] = yield_curve_signal
        state.shared_data["macro_signal"] = signal.to_dict()
        state.shared_data["market_regime"] = signal.regime.value
        
        # ===== STEP 5: Create Result =====
        result = PortfolioResult(
            agent_name=self.name,
            task_id=task.task_id,
            success=True,
            result_type="macro_analysis",
            data=signal.to_dict(),
            message=f"Macro analysis complete. Regime: {signal.regime.value.upper()}, "
                    f"Equity adjustment: {signal.equity_adjustment:+.0%}",
            metadata={
                "vix_source": vix_data.get("source", "unknown"),
                "yield_source": yield_data.get("source", "unknown"),
            }
        )
        
        state.add_sub_result(self.name, result)
        state.add_message("assistant", signal.to_summary())
        
        return state
    
    # ==================== DATA RETRIEVAL HELPERS ====================
    
    def _get_vix_data(self, shared: Dict) -> Dict[str, Any]:
        """
        Get VIX data from shared_data, database, or fetch live.
        
        Priority:
        1. shared_data (if provided by upstream)
        2. Database (most recent)
        3. Live fetch (if auto_fetch enabled)
        """
        # Check shared_data first
        if "vix_level" in shared:
            return {
                "current_vix": shared["vix_level"],
                "regime": self._classify_vix_regime(shared["vix_level"]),
                "source": "shared_state"
            }
        
        # Try database
        try:
            db_result = self.data_manager.get_vix_with_regime()
            if db_result.get("success") and db_result.get("current_vix"):
                return {
                    "current_vix": db_result["current_vix"],
                    "regime": db_result["regime"],
                    "percentile_30d": db_result.get("percentile_30d"),
                    "trend": db_result.get("trend"),
                    "source": "database"
                }
        except Exception as e:
            self.log(f"Database VIX fetch failed: {e}")
        
        # Auto-fetch if enabled
        if config.macro.auto_fetch_if_missing:
            try:
                self.log("Auto-fetching VIX data...")
                update_result = self.data_manager.update_vix(days=config.macro.default_history_days)
                if update_result.success:
                    db_result = self.data_manager.get_vix_with_regime()
                    if db_result.get("success"):
                        return {
                            "current_vix": db_result["current_vix"],
                            "regime": db_result["regime"],
                            "source": "live_fetch"
                        }
            except Exception as e:
                self.log(f"Live VIX fetch failed: {e}")
        
        # Default fallback
        return {
            "current_vix": 20.0,
            "regime": "normal",
            "source": "default"
        }
    
    def _get_yield_curve_data(self, shared: Dict) -> Dict[str, Any]:
        """
        Get yield curve data from shared_data, database, or fetch live.
        """
        # Check shared_data first
        if "yield_curve_slope" in shared:
            slope = shared["yield_curve_slope"]
            return {
                "slope_10y_3m": slope,
                "status": self._classify_yield_curve(slope),
                "source": "shared_state"
            }
        
        # Try database
        try:
            db_result = self.data_manager.get_yield_curve_status()
            if db_result.get("success") and db_result.get("slope_10y_3m") is not None:
                return {
                    "slope_10y_3m": db_result["slope_10y_3m"],
                    "status": db_result.get("status", "normal"),
                    "treasury_10y": db_result.get("treasury_10y"),
                    "treasury_3m": db_result.get("treasury_3m"),
                    "recession_signal": db_result.get("recession_signal", False),
                    "source": "database"
                }
        except Exception as e:
            self.log(f"Database yield curve fetch failed: {e}")
        
        # Auto-fetch if enabled
        if config.macro.auto_fetch_if_missing:
            try:
                self.log("Auto-fetching Treasury yields...")
                update_result = self.data_manager.update_treasury_yields(days=config.macro.default_history_days)
                if update_result.success:
                    db_result = self.data_manager.get_yield_curve_status()
                    if db_result.get("success"):
                        return {
                            "slope_10y_3m": db_result.get("slope_10y_3m"),
                            "status": db_result.get("status", "normal"),
                            "source": "live_fetch"
                        }
            except Exception as e:
                self.log(f"Live yield fetch failed: {e}")
        
        # Default fallback
        return {
            "slope_10y_3m": None,
            "status": "unknown",
            "source": "default"
        }
    
    # ==================== CLASSIFICATION HELPERS ====================
    
    def _classify_vix_regime(self, vix_level: float) -> str:
        """Classify VIX level into regime."""
        if vix_level < config.macro.vix_low:
            return "low"
        elif vix_level < config.macro.vix_elevated:
            return "normal"
        elif vix_level < config.macro.vix_crisis:
            return "elevated"
        else:
            return "crisis"
    
    def _classify_yield_curve(self, slope: Optional[float]) -> str:
        """Classify yield curve slope."""
        if slope is None:
            return "unknown"
        if slope < -0.2:
            return "inverted"
        elif slope < 0.5:
            return "flat"
        elif slope < 1.5:
            return "normal"
        else:
            return "steep"
    
    # ==================== SIGNAL GENERATION ====================
    
    def _generate_signal(
        self,
        vix_level: float,
        yield_curve: Optional[float]
    ) -> MacroSignal:
        """Generate combined macro signal."""
        
        # Classify indicators
        vix_regime = self._classify_vix_regime(vix_level)
        yield_signal = self._classify_yield_curve(yield_curve)
        
        # Determine regime
        regime = self._determine_regime(vix_regime, yield_signal)
        
        # Calculate confidence
        regime_confidence = self._calculate_regime_confidence(vix_regime)
        
        # Determine risk stance and adjustment
        risk_stance, equity_adjustment = self._determine_risk_stance(
            regime, vix_regime
        )
        
        return MacroSignal(
            vix_level=vix_level,
            vix_regime=vix_regime,
            yield_curve_slope=yield_curve,
            yield_curve_signal=yield_signal,
            regime=regime,
            regime_confidence=regime_confidence,
            risk_stance=risk_stance,
            equity_adjustment=equity_adjustment,
        )
    
    def _determine_regime(
        self,
        vix_regime: str,
        yield_signal: str
    ) -> MarketRegime:
        """Determine market regime from indicators."""
        
        # Crisis check
        if vix_regime == "crisis":
            return MarketRegime.CRISIS
        
        # Scoring
        risk_off_signals = 0
        risk_on_signals = 0
        
        # VIX
        if vix_regime == "elevated":
            risk_off_signals += 1
        elif vix_regime == "low":
            risk_on_signals += 1
        
        # Yield curve (strong signal)
        if yield_signal == "inverted":
            risk_off_signals += 2
        elif yield_signal == "steep":
            risk_on_signals += 1
        
        # Determine regime
        if risk_off_signals >= 3:
            return MarketRegime.RISK_OFF
        elif risk_on_signals >= 2 and risk_off_signals == 0:
            return MarketRegime.RISK_ON
        elif risk_on_signals > risk_off_signals:
            return MarketRegime.RECOVERY
        else:
            return MarketRegime.NEUTRAL
    
    def _calculate_regime_confidence(
        self,
        vix_regime: str
    ) -> float:
        """Calculate confidence in regime assessment.
        
        NOTE: derived from VIX alone. The yield curve informs the regime but
        not the confidence in it, so confidence is capped at 0.3. Recorded in
        tests/golden/KNOWN_GAPS.md.
        """
        if vix_regime in ["crisis", "low"]:
            confidence = 0.3
        elif vix_regime == "elevated":
            confidence = 0.2
        else:
            confidence = 0.1
        
        return min(0.95, confidence)
    
    def _determine_risk_stance(
        self,
        regime: MarketRegime,
        vix_regime: str
    ) -> tuple:
        """Determine risk stance and equity adjustment."""
        max_adj = config.macro.max_equity_adjust
        
        if regime == MarketRegime.CRISIS:
            return "defensive", -max_adj
        
        elif regime == MarketRegime.RISK_OFF:
            adj = -max_adj * 0.6
            if vix_regime == "elevated":
                adj -= max_adj * 0.2
            return "risk_off", adj
        
        elif regime == MarketRegime.RISK_ON:
            return "risk_on", max_adj * 0.5
        
        elif regime == MarketRegime.RECOVERY:
            return "cautious_risk_on", max_adj * 0.3
        
        else:
            return "neutral", 0.0
    
    # ==================== TOOL METHODS ====================
    
    def fetch_macro_data_tool(
        self,
        indicators: str = "VIX,TNX_10Y,TYX_30Y,IRX_3M",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch and persist macro data to database.
        
        Args:
            indicators: Comma-separated list (VIX, TNX_10Y, TYX_30Y, IRX_3M, USD_INDEX, GOLD)
            days: Number of days of history
            
        Returns:
            {success, rows_updated, indicators, message}
        """
        try:
            indicator_list = [i.strip() for i in indicators.split(",")]
            
            result = self.data_manager.update_macro_data(
                indicators=indicator_list,
                start_date=date.today() - timedelta(days=days),
                end_date=date.today()
            )
            
            return {
                "success": result.success,
                "operation": "fetch_macro_data",
                "indicators": indicator_list,
                "rows_updated": result.affected_count,
                "message": f"Updated {result.affected_count} records for {len(indicator_list)} indicators",
                "metadata": result.metadata
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_macro_snapshot_tool(self) -> Dict[str, Any]:
        """
        Get current snapshot of all macro indicators from database.
        
        Returns:
            {success, vix, yields, yield_curve}
        """
        try:
            latest = self.data_manager.get_latest_macro_values()
            
            if not latest.get("success"):
                return latest
            
            indicators = latest.get("indicators", {})
            
            result = {
                "success": True,
                "timestamp": latest.get("timestamp"),
                "vix": None,
                "yields": {},
                "yield_curve": None
            }
            
            # VIX with regime
            if "VIX" in indicators:
                vix_val = indicators["VIX"]["value"]
                result["vix"] = {
                    "value": vix_val,
                    "date": indicators["VIX"]["date"],
                    "regime": self._classify_vix_regime(vix_val)
                }
            
            # Treasury yields
            for key in ["TNX_10Y", "TYX_30Y", "IRX_3M"]:
                if key in indicators:
                    result["yields"][key] = indicators[key]
            
            # Yield curve slope
            t10y = indicators.get("TNX_10Y", {}).get("value")
            t3m = indicators.get("IRX_3M", {}).get("value")
            
            if t10y is not None and t3m is not None:
                slope = t10y - t3m
                result["yield_curve"] = {
                    "slope": round(slope, 4),
                    "status": self._classify_yield_curve(slope),
                    "recession_warning": slope < 0
                }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_vix_analysis_tool(self, days: int = 30) -> Dict[str, Any]:
        """
        Get VIX analysis with regime and trend.
        
        Args:
            days: Days for historical analysis
            
        Returns:
            {current_vix, regime, percentile, trend, signal}
        """
        try:
            vix_info = self.data_manager.get_vix_with_regime()
            
            if not vix_info.get("success"):
                return vix_info
            
            # Add investment signal
            regime = vix_info.get("regime", "unknown")
            trend = vix_info.get("trend", "unknown")
            
            if regime == "crisis":
                signal = "DEFENSIVE - High volatility, reduce equity exposure"
            elif regime == "elevated":
                signal = "CAUTION - Volatility elevated" + (", rising" if trend == "rising" else "")
            elif regime == "low":
                signal = "RISK_ON - Low volatility" + (" (watch for complacency)" if trend == "falling" else "")
            else:
                signal = "NEUTRAL - Normal market conditions"
            
            vix_info["signal"] = signal
            return vix_info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_yield_curve_analysis_tool(self) -> Dict[str, Any]:
        """
        Analyze yield curve for recession signals.
        
        Returns:
            {treasury_10y, treasury_3m, slope, status, recession_signal, interpretation}
        """
        try:
            curve_info = self.data_manager.get_yield_curve_status()
            
            if not curve_info.get("success"):
                return curve_info
            
            status = curve_info.get("status", "unknown")
            
            interpretations = {
                "deeply_inverted": "Deeply inverted. Historically precedes recessions by 6-18 months.",
                "inverted": "Inverted. Warning signal for economic slowdown.",
                "flat": "Flat. Market uncertainty about future growth.",
                "steep": "Steep. Strong growth/inflation expectations.",
                "normal": "Normal. Stable growth expectations."
            }
            
            curve_info["interpretation"] = interpretations.get(status, "Unknown status")
            return curve_info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def assess_regime_tool(
        self,
        vix_level: float,
        yield_curve_slope: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assess current market regime from indicators.
        
        Args:
            vix_level: Current VIX level
            yield_curve_slope: 10Y-3M spread
            
        Returns:
            {success, regime, confidence, signals, recommendation}
        """
        try:
            signal = self._generate_signal(
                vix_level=vix_level,
                yield_curve=yield_curve_slope
            )
            
            return {
                "success": True,
                **signal.to_dict(),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_taa_signal_tool(
        self,
        current_equity_weight: float = 0.60,
        use_database: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete TAA signal.
        
        Args:
            current_equity_weight: Current equity allocation (0-1)
            use_database: Use database for VIX/Yields (default True)
            
        Returns:
            {success, current_weight, recommended_weight, action, regime, rationale}
        """
        try:
            # Get VIX
            if use_database:
                vix_data = self._get_vix_data({})
                yield_data = self._get_yield_curve_data({})
            else:
                vix_data = {"current_vix": 20.0, "regime": "normal"}
                yield_data = {"slope_10y_3m": None, "status": "unknown"}
            
            vix_level = vix_data.get("current_vix", 20.0)
            yield_slope = yield_data.get("slope_10y_3m")
            
            # Generate signal
            signal = self._generate_signal(
                vix_level=vix_level,
                yield_curve=yield_slope
            )
            
            # Calculate recommended weight
            recommended = current_equity_weight + signal.equity_adjustment
            recommended = max(0.30, min(0.80, recommended))  # Clamp to 30-80%
            
            change = recommended - current_equity_weight
            
            if change > 0.02:
                action = "INCREASE"
            elif change < -0.02:
                action = "DECREASE"
            else:
                action = "HOLD"
            
            rationale = [
                f"Market regime: {signal.regime.value.upper()}",
                f"VIX at {vix_level:.1f} ({signal.vix_regime})",
            ]
            if yield_slope is not None:
                rationale.append(f"Yield curve: {signal.yield_curve_signal}")
            
            return {
                "success": True,
                "current_equity_weight": current_equity_weight,
                "recommended_equity_weight": round(recommended, 4),
                "change": round(change, 4),
                "action": action,
                "regime": signal.regime.value,
                "regime_confidence": signal.regime_confidence,
                "rationale": rationale,
                "signal_details": signal.to_dict(),
                "summary": signal.to_summary()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== FACTORY FUNCTION ====================

def create_macro_agent(verbose: bool = False) -> MacroAgent:
    """
    Factory function to create configured Macro Agent.
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        Configured MacroAgent
    """
    agent_config = AgentConfig(
        name="MacroAgent",
        role=AgentRole.MACRO,
        verbose=verbose,
    )
    return MacroAgent(agent_config)