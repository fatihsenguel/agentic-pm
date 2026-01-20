# ============================================================
# NEUE DATEI: portfolio_tool/tools/macro_tools.py
# ============================================================
# LangChain @tool Funktionen für Macro-Daten.
#
# DESIGN PRINCIPLES BEACHTET:
# 1. Hot Potato: Tools geben NUR aggregierte Daten zurück
# 2. Separation of Concerns: Tools = Agent Interface ONLY
#    - Keine Business Logic (die ist in DataManager)
#    - Kein direkter DB/Provider Zugriff
# 3. Agent-Ready Responses: Strukturierte Dicts mit success, data, metadata
# 4. Konsistent mit bestehenden tools (data_tools.py, analytics_tools.py)
# ============================================================

from datetime import date, timedelta
from typing import Dict, Any, Optional, List
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ==================== HELPER ====================

def _get_data_manager():
    """
    Holt DataManager Instance.
    Gleicher Pattern wie in data_tools.py.
    """
    from portfolio_tool.data_manager import get_data_manager
    return get_data_manager()


# ==================== DATA FETCHING TOOLS ====================

@tool
def fetch_macro_data(
    indicators: str = "VIX,TNX_10Y,TYX_30Y,IRX_3M",
    days: int = 30
) -> Dict[str, Any]:
    """
    Fetcht und speichert Macro-Indikator-Daten in der Datenbank.
    
    Args:
        indicators: Komma-getrennte Liste. Optionen:
                   VIX, TNX_10Y, TYX_30Y, IRX_3M, USD_INDEX, GOLD
        days: Anzahl Tage Historie (default: 30)
    
    Returns:
        {success, operation, indicators, rows_updated, message}
    
    Example:
        fetch_macro_data("VIX,TNX_10Y", 60)
    """
    try:
        dm = _get_data_manager()
        indicator_list = [i.strip() for i in indicators.split(",")]
        
        result = dm.update_macro_data(
            indicators=indicator_list,
            start_date=date.today() - timedelta(days=days),
            end_date=date.today()
        )
        
        return {
            "success": result.success,
            "operation": "fetch_macro_data",
            "indicators": indicator_list,
            "rows_updated": result.affected_count,
            "message": f"Updated {result.affected_count} records for {len(indicator_list)} indicators"
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_macro_data: {e}")
        return {
            "success": False,
            "operation": "fetch_macro_data",
            "error": str(e)
        }


@tool
def get_macro_snapshot() -> Dict[str, Any]:
    """
    Holt aktuellen Snapshot aller Macro-Indikatoren aus der Datenbank.
    
    Returns:
        {
            success: bool,
            timestamp: str,
            vix: {value, regime},
            yields: {TNX_10Y, TYX_30Y, IRX_3M},
            yield_curve: {slope, status, recession_warning}
        }
    
    Example:
        snapshot = get_macro_snapshot()
        print(f"VIX: {snapshot['vix']['value']}")
    """
    try:
        dm = _get_data_manager()
        latest = dm.get_latest_macro_values()
        
        if not latest.get("success"):
            return latest
        
        indicators = latest.get("indicators", {})
        
        # Format Response (Hot Potato: Agent bekommt fertige Struktur)
        result = {
            "success": True,
            "timestamp": latest.get("timestamp"),
            "vix": None,
            "yields": {},
            "yield_curve": None
        }
        
        # VIX mit Regime
        if "VIX" in indicators:
            vix_val = indicators["VIX"]["value"]
            if vix_val < 15:
                regime = "low"
            elif vix_val < 25:
                regime = "normal"
            elif vix_val < 35:
                regime = "elevated"
            else:
                regime = "crisis"
            
            result["vix"] = {
                "value": vix_val,
                "date": indicators["VIX"]["date"],
                "regime": regime
            }
        
        # Treasury Yields
        for key in ["TNX_10Y", "TYX_30Y", "IRX_3M"]:
            if key in indicators:
                result["yields"][key] = indicators[key]
        
        # Yield Curve Slope
        t10y = indicators.get("TNX_10Y", {}).get("value")
        t3m = indicators.get("IRX_3M", {}).get("value")
        
        if t10y is not None and t3m is not None:
            slope = t10y - t3m
            if slope < -0.2:
                status = "inverted"
            elif slope < 0.5:
                status = "flat"
            elif slope < 1.5:
                status = "normal"
            else:
                status = "steep"
            
            result["yield_curve"] = {
                "slope": round(slope, 4),
                "status": status,
                "recession_warning": slope < 0
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_macro_snapshot: {e}")
        return {"success": False, "error": str(e)}


@tool
def get_vix_analysis(days: int = 30) -> Dict[str, Any]:
    """
    Holt VIX-Analyse mit Regime, Trend und Signal.
    
    Args:
        days: Tage für historische Analyse (default: 30)
    
    Returns:
        {
            current_vix: float,
            regime: "low"|"normal"|"elevated"|"crisis",
            percentile_30d: int,
            trend: "rising"|"falling"|"stable",
            signal: Investment-Empfehlung
        }
    """
    try:
        dm = _get_data_manager()
        vix_info = dm.get_vix_with_regime()
        
        if not vix_info.get("success"):
            return vix_info
        
        # Investment Signal hinzufügen (Hot Potato: fertige Empfehlung)
        regime = vix_info.get("regime", "unknown")
        trend = vix_info.get("trend", "unknown")
        
        if regime == "crisis":
            signal = "DEFENSIVE - High volatility, reduce equity exposure"
        elif regime == "elevated":
            if trend == "rising":
                signal = "CAUTION - Volatility increasing, consider hedging"
            else:
                signal = "WATCHFUL - Elevated but stabilizing"
        elif regime == "low":
            if trend == "falling":
                signal = "COMPLACENT - Very low vol may precede spike"
            else:
                signal = "RISK_ON - Low volatility environment"
        else:
            signal = "NEUTRAL - Normal market conditions"
        
        vix_info["signal"] = signal
        return vix_info
        
    except Exception as e:
        logger.error(f"Error in get_vix_analysis: {e}")
        return {"success": False, "error": str(e)}


@tool
def get_yield_curve_analysis() -> Dict[str, Any]:
    """
    Analysiert Yield Curve für Recession-Signale.
    
    Returns:
        {
            treasury_10y: float,
            treasury_3m: float,
            slope: float,
            status: "inverted"|"flat"|"normal"|"steep",
            recession_signal: bool,
            interpretation: str
        }
    """
    try:
        dm = _get_data_manager()
        curve_info = dm.get_yield_curve_status()
        
        if not curve_info.get("success"):
            return curve_info
        
        # Interpretation hinzufügen (Hot Potato)
        status = curve_info.get("status", "unknown")
        
        interpretations = {
            "deeply_inverted": "Deeply inverted yield curve. Historically precedes recessions by 6-18 months.",
            "inverted": "Yield curve inverted. Warning signal for economic slowdown.",
            "flat": "Flat yield curve indicates market uncertainty about future growth.",
            "steep": "Steep yield curve suggests strong growth expectations.",
            "normal": "Normal yield curve indicating stable growth expectations."
        }
        
        curve_info["interpretation"] = interpretations.get(status, "Unknown status")
        return curve_info
        
    except Exception as e:
        logger.error(f"Error in get_yield_curve_analysis: {e}")
        return {"success": False, "error": str(e)}


# ==================== REGIME DETECTION TOOLS ====================

@tool
def get_market_regime() -> Dict[str, Any]:
    """
    Bestimmt aktuelles Markt-Regime basierend auf VIX und Yield Curve.
    
    Returns:
        {
            regime: "RISK_ON"|"RISK_OFF"|"CRISIS"|"NEUTRAL"|"RECOVERY",
            confidence: float (0-1),
            signals: {vix_regime, yield_curve},
            equity_adjustment: float (-0.15 to +0.15),
            recommendation: str
        }
    """
    try:
        dm = _get_data_manager()
        
        # VIX Info
        vix_info = dm.get_vix_with_regime()
        vix_regime = vix_info.get("regime", "normal") if vix_info.get("success") else "normal"
        vix_value = vix_info.get("current_vix", 20) if vix_info.get("success") else 20
        
        # Yield Curve Info
        yield_info = dm.get_yield_curve_status()
        yield_status = yield_info.get("status", "normal") if yield_info.get("success") else "normal"
        recession_signal = yield_info.get("recession_signal", False) if yield_info.get("success") else False
        
        signals = {
            "vix_regime": vix_regime,
            "vix_value": vix_value,
            "yield_curve": yield_status,
            "recession_signal": recession_signal
        }
        
        # Crisis Check
        if vix_regime == "crisis":
            return {
                "success": True,
                "regime": "CRISIS",
                "confidence": 0.95,
                "signals": signals,
                "equity_adjustment": -0.15,
                "recommendation": "DEFENSIVE positioning. VIX in crisis territory. Reduce equity exposure significantly."
            }
        
        # Scoring
        risk_off_score = 0
        risk_on_score = 0
        
        # VIX Contribution
        if vix_regime == "elevated":
            risk_off_score += 2
        elif vix_regime == "low":
            risk_on_score += 2
        else:
            risk_on_score += 1
        
        # Yield Curve Contribution
        if yield_status in ["inverted", "deeply_inverted"]:
            risk_off_score += 3
        elif yield_status == "flat":
            risk_off_score += 1
        elif yield_status == "steep":
            risk_on_score += 1
        
        # Regime bestimmen
        if risk_off_score >= 4:
            regime = "RISK_OFF"
            confidence = min(0.9, risk_off_score / 5)
            equity_adj = -0.10
            recommendation = "CAUTIOUS positioning. Multiple warning signals suggest reducing equity exposure."
        elif risk_on_score >= 3 and risk_off_score <= 1:
            regime = "RISK_ON"
            confidence = min(0.85, risk_on_score / 4)
            equity_adj = 0.05
            recommendation = "CONSTRUCTIVE positioning. Conditions favor equity exposure."
        elif risk_on_score > risk_off_score:
            regime = "RECOVERY"
            confidence = 0.6
            equity_adj = 0.03
            recommendation = "IMPROVING conditions. Cautiously increasing equity exposure."
        else:
            regime = "NEUTRAL"
            confidence = 0.5
            equity_adj = 0.0
            recommendation = "MIXED signals. Maintain current allocation."
        
        return {
            "success": True,
            "regime": regime,
            "confidence": confidence,
            "signals": signals,
            "equity_adjustment": equity_adj,
            "recommendation": recommendation
        }
        
    except Exception as e:
        logger.error(f"Error in get_market_regime: {e}")
        return {"success": False, "error": str(e)}


@tool
def generate_taa_signal(
    current_equity_weight: float = 0.60
) -> Dict[str, Any]:
    """
    Generiert TAA (Tactical Asset Allocation) Signal.
    
    Args:
        current_equity_weight: Aktuelle Equity Allokation (0.0 bis 1.0)
    
    Returns:
        {
            current_equity_weight: float,
            recommended_equity_weight: float,
            change: float,
            action: "INCREASE"|"DECREASE"|"HOLD",
            regime: str,
            rationale: [str]
        }
    """
    try:
        # Market Regime holen
        regime_result = get_market_regime.invoke({})
        
        if not regime_result.get("success"):
            return regime_result
        
        regime = regime_result["regime"]
        equity_adj = regime_result["equity_adjustment"]
        
        # Recommended Weight berechnen
        recommended = current_equity_weight + equity_adj
        
        # Auf sinnvolle Grenzen beschränken (30% - 80%)
        recommended = max(0.30, min(0.80, recommended))
        
        change = recommended - current_equity_weight
        
        # Action bestimmen
        if change > 0.02:
            action = "INCREASE"
        elif change < -0.02:
            action = "DECREASE"
        else:
            action = "HOLD"
        
        # Rationale
        rationale = [
            f"Market regime is {regime}",
            regime_result["recommendation"]
        ]
        
        if equity_adj != 0:
            rationale.append(f"Regime suggests {equity_adj:+.1%} equity adjustment")
        
        return {
            "success": True,
            "current_equity_weight": current_equity_weight,
            "recommended_equity_weight": round(recommended, 4),
            "change": round(change, 4),
            "action": action,
            "regime": regime,
            "rationale": rationale,
            "signals": regime_result["signals"]
        }
        
    except Exception as e:
        logger.error(f"Error in generate_taa_signal: {e}")
        return {"success": False, "error": str(e)}


# ==================== FED MINUTES TOOLS ====================

@tool
def fetch_fed_minutes(date_spec: str = "latest") -> Dict[str, Any]:
    """
    Lädt Fed Minutes (FOMC Meeting Minutes).
    
    Args:
        date_spec: "latest" oder "YYYY-MM" Format (z.B. "2024-01")
    
    Returns:
        {
            success: bool,
            meeting_date: str,
            content_preview: str (erste 500 Zeichen),
            content_length: int,
            source: str
        }
    """
    try:
        from portfolio_tool.rag.fed_scraper import FedMinutesScraper, DownloadStatus
        
        scraper = FedMinutesScraper()
        
        if date_spec.lower() == "latest":
            doc = scraper.get_latest_minutes()
        else:
            parts = date_spec.split("-")
            if len(parts) != 2:
                return {
                    "success": False,
                    "error": "Invalid date format. Use 'latest' or 'YYYY-MM'"
                }
            year, month = int(parts[0]), int(parts[1])
            doc = scraper.get_minutes_by_date(year, month)
        
        if doc.download_status in [DownloadStatus.SUCCESS, DownloadStatus.CACHED]:
            return {
                "success": True,
                "meeting_date": doc.metadata.meeting_date.isoformat(),
                "title": doc.metadata.title,
                "content_preview": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                "content_length": len(doc.content),
                "source": doc.source_path,
                "status": doc.download_status.value
            }
        else:
            return {
                "success": False,
                "status": doc.download_status.value,
                "error": doc.error_message
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "Fed scraper not installed. Add fed_scraper.py to rag/ folder."
        }
    except Exception as e:
        logger.error(f"Error fetching Fed minutes: {e}")
        return {"success": False, "error": str(e)}


@tool
def list_available_fed_minutes(year: Optional[int] = None) -> Dict[str, Any]:
    """
    Listet verfügbare Fed Minutes auf der Fed Website.
    
    Args:
        year: Filter nach Jahr (optional)
    
    Returns:
        {
            success: bool,
            count: int,
            minutes: [{meeting_date, title, has_html, has_pdf}]
        }
    """
    try:
        from portfolio_tool.rag.fed_scraper import FedMinutesScraper
        
        scraper = FedMinutesScraper()
        minutes = scraper.list_available_minutes(year=year)
        
        return {
            "success": True,
            "count": len(minutes),
            "year": year or "current",
            "minutes": [
                {
                    "meeting_date": m.meeting_date.isoformat(),
                    "title": m.title,
                    "has_html": bool(m.html_url),
                    "has_pdf": bool(m.pdf_url)
                }
                for m in minutes
            ]
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Fed scraper not installed."
        }
    except Exception as e:
        logger.error(f"Error listing Fed minutes: {e}")
        return {"success": False, "error": str(e)}


# ==================== TOOL COLLECTION ====================

def get_macro_tools() -> List:
    """
    Gibt alle Macro Tools für Agent-Registrierung zurück.
    
    Usage:
        from portfolio_tool.tools.macro_tools import get_macro_tools
        
        tools = get_macro_tools()
        agent = create_agent(tools=tools)
    """
    return [
        fetch_macro_data,
        get_macro_snapshot,
        get_vix_analysis,
        get_yield_curve_analysis,
        get_market_regime,
        generate_taa_signal,
        fetch_fed_minutes,
        list_available_fed_minutes,
    ]
