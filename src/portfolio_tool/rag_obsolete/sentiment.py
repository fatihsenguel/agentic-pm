"""
Fed Sentiment Analysis for RAG Pipeline.

Extracts sentiment and key themes from Fed Minutes:
- Hawkish/Dovish scoring (-1 to +1)
- Key theme extraction
- Risk assessment (risk_on/risk_off/neutral)

This is rule-based sentiment analysis optimized for Fed language.
For more sophisticated analysis, an LLM can be used.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re

from .document_loader import Document
from .chunker import Chunk


class SentimentScore(str, Enum):
    """Categorical sentiment classification."""
    VERY_HAWKISH = "very_hawkish"
    HAWKISH = "hawkish"
    NEUTRAL = "neutral"
    DOVISH = "dovish"
    VERY_DOVISH = "very_dovish"


@dataclass
class SentimentResult:
    """
    Result from Fed sentiment analysis.
    
    Contains:
    - Numeric score: -1 (very dovish) to +1 (very hawkish)
    - Categorical classification
    - Key themes extracted
    - Risk assessment for TAA
    """
    
    # Core sentiment
    score: float  # -1.0 to +1.0
    classification: SentimentScore
    confidence: float  # 0.0 to 1.0
    
    # Themes
    key_themes: List[str]
    hawkish_signals: List[str]
    dovish_signals: List[str]
    
    # Risk assessment
    risk_assessment: str  # "risk_on", "risk_off", "neutral"
    
    # Analysis details
    analyzed_sections: List[str]
    word_count_analyzed: int
    
    # Source
    source: str = ""
    date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": f"{self.score:+.2f}",
            "classification": self.classification.value,
            "confidence": f"{self.confidence:.1%}",
            "risk_assessment": self.risk_assessment,
            "key_themes": self.key_themes,
            "hawkish_signals": self.hawkish_signals[:5],  # Top 5
            "dovish_signals": self.dovish_signals[:5],
            "sections_analyzed": len(self.analyzed_sections),
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "Fed Sentiment Analysis",
            "=" * 40,
            f"Score: {self.score:+.2f} ({self.classification.value})",
            f"Confidence: {self.confidence:.1%}",
            f"Risk Assessment: {self.risk_assessment.upper()}",
            "",
            "Key Themes:",
        ]
        
        for theme in self.key_themes[:5]:
            lines.append(f"  • {theme}")
        
        if self.hawkish_signals:
            lines.append("")
            lines.append("Hawkish Signals:")
            for signal in self.hawkish_signals[:3]:
                lines.append(f"  ↑ {signal}")
        
        if self.dovish_signals:
            lines.append("")
            lines.append("Dovish Signals:")
            for signal in self.dovish_signals[:3]:
                lines.append(f"  ↓ {signal}")
        
        return "\n".join(lines)


class FedSentimentAnalyzer:
    """
    Sentiment analyzer optimized for Fed Minutes.
    
    Uses a rule-based approach with weighted keywords and phrases.
    
    Example:
        analyzer = FedSentimentAnalyzer()
        result = analyzer.analyze(document)
        print(f"Sentiment: {result.score:+.2f}")
    """
    
    # Hawkish indicators (positive = tighter policy)
    HAWKISH_TERMS = {
        # Strong hawkish
        "inflation remains elevated": 3.0,
        "inflation is too high": 3.0,
        "price stability": 2.0,
        "further tightening": 2.5,
        "additional rate increases": 2.5,
        "restrictive stance": 2.0,
        "upside risks to inflation": 2.0,
        
        # Moderate hawkish
        "robust labor market": 1.5,
        "strong employment": 1.5,
        "tight labor market": 1.5,
        "wage pressures": 1.5,
        "above target": 1.5,
        "elevated inflation": 1.5,
        "persistent inflation": 1.5,
        
        # Mild hawkish
        "inflation expectations": 1.0,
        "price pressures": 1.0,
        "higher for longer": 1.5,
        "data dependent": 0.5,
        "gradual": 0.5,
    }
    
    # Dovish indicators (negative = looser policy)
    DOVISH_TERMS = {
        # Strong dovish
        "rate cuts": -3.0,
        "easing cycle": -3.0,
        "significant slowdown": -2.5,
        "recession risks": -2.5,
        "financial stress": -2.5,
        
        # Moderate dovish
        "cooling inflation": -2.0,
        "inflation declining": -2.0,
        "labor market softening": -1.5,
        "slowing growth": -1.5,
        "downside risks": -1.5,
        "below trend": -1.5,
        "disinflation": -2.0,
        
        # Mild dovish
        "balanced risks": -0.5,
        "patient": -1.0,
        "flexible": -0.5,
        "data dependent": -0.5,  # Can be both
        "gradual normalization": -1.0,
        "soft landing": -1.0,
    }
    
    # Key themes to extract
    THEME_PATTERNS = {
        "inflation": r"inflat\w+",
        "employment": r"employ\w+|labor market|job\w*",
        "growth": r"economic growth|gdp|expansion|recession",
        "rates": r"interest rate|federal funds|policy rate",
        "financial_conditions": r"financial conditions|credit|lending",
        "global": r"global|international|geopolitical",
        "housing": r"housing|real estate|mortgage",
        "consumer": r"consumer|spending|consumption",
        "banking": r"bank\w+|credit|financial system",
    }
    
    def __init__(self, verbose: bool = False):
        """Initialize analyzer."""
        self.verbose = verbose
    
    def analyze(self, document: Document) -> SentimentResult:
        """
        Analyze Fed Minutes document for sentiment.
        
        Args:
            document: Document to analyze
            
        Returns:
            SentimentResult with sentiment score and themes
        """
        text = document.content.lower()
        
        # Find hawkish and dovish signals
        hawkish_matches = self._find_matches(text, self.HAWKISH_TERMS)
        dovish_matches = self._find_matches(text, self.DOVISH_TERMS)
        
        # Calculate scores
        hawkish_score = sum(score for _, score in hawkish_matches)
        dovish_score = sum(score for _, score in dovish_matches)  # Already negative
        
        # Net score
        raw_score = hawkish_score + dovish_score
        
        # Normalize to -1 to +1
        max_possible = max(abs(hawkish_score), abs(dovish_score), 1)
        normalized_score = max(-1.0, min(1.0, raw_score / (max_possible * 2)))
        
        # Classification
        classification = self._classify_score(normalized_score)
        
        # Confidence based on number of signals
        total_signals = len(hawkish_matches) + len(dovish_matches)
        confidence = min(1.0, total_signals / 20)  # Max confidence at 20+ signals
        
        # Extract themes
        themes = self._extract_themes(text)
        
        # Risk assessment
        risk = self._assess_risk(normalized_score, themes)
        
        # Extract sections analyzed
        sections = self._identify_sections(document.content)
        
        return SentimentResult(
            score=normalized_score,
            classification=classification,
            confidence=confidence,
            key_themes=themes,
            hawkish_signals=[term for term, _ in hawkish_matches],
            dovish_signals=[term for term, _ in dovish_matches],
            risk_assessment=risk,
            analyzed_sections=sections,
            word_count_analyzed=len(text.split()),
            source=document.source,
            date=document.date.isoformat() if document.date else None,
        )
    
    def analyze_chunks(self, chunks: List[Chunk]) -> Dict[str, SentimentResult]:
        """
        Analyze sentiment by section.
        
        Returns dict of section -> SentimentResult.
        """
        # Group chunks by section
        sections: Dict[str, List[Chunk]] = {}
        
        for chunk in chunks:
            section = chunk.section or "general"
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk)
        
        results = {}
        
        for section, section_chunks in sections.items():
            # Combine text
            combined_text = "\n\n".join(c.text for c in section_chunks)
            doc = Document(content=combined_text, source=f"section:{section}")
            
            results[section] = self.analyze(doc)
        
        return results
    
    def _find_matches(
        self, 
        text: str, 
        terms: Dict[str, float]
    ) -> List[Tuple[str, float]]:
        """Find matching terms in text."""
        matches = []
        
        for term, score in terms.items():
            # Count occurrences
            count = text.count(term.lower())
            if count > 0:
                # Diminishing returns for repeated terms
                effective_count = 1 + 0.5 * (count - 1)
                matches.append((term, score * effective_count))
        
        return sorted(matches, key=lambda x: -abs(x[1]))
    
    def _classify_score(self, score: float) -> SentimentScore:
        """Classify numeric score into category."""
        if score >= 0.5:
            return SentimentScore.VERY_HAWKISH
        elif score >= 0.2:
            return SentimentScore.HAWKISH
        elif score <= -0.5:
            return SentimentScore.VERY_DOVISH
        elif score <= -0.2:
            return SentimentScore.DOVISH
        else:
            return SentimentScore.NEUTRAL
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text."""
        themes = []
        
        for theme, pattern in self.THEME_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if len(matches) >= 3:  # Theme is significant if mentioned 3+ times
                themes.append(theme)
        
        return themes
    
    def _assess_risk(self, score: float, themes: List[str]) -> str:
        """
        Assess risk stance for TAA.
        
        Returns: "risk_on", "risk_off", or "neutral"
        """
        # Very hawkish = risk_off (expecting tighter policy)
        # Very dovish = risk_on (expecting easier policy)
        
        if score >= 0.3:
            return "risk_off"
        elif score <= -0.3:
            return "risk_on"
        else:
            return "neutral"
    
    def _identify_sections(self, text: str) -> List[str]:
        """Identify which Fed Minutes sections are present."""
        sections = []
        
        section_names = [
            "Financial Markets",
            "Economic Situation",
            "Financial Situation",
            "Economic Outlook",
            "Participants' Views",
            "Policy Action",
        ]
        
        for section in section_names:
            if section.lower() in text.lower():
                sections.append(section)
        
        return sections


# Convenience functions

def analyze_fed_sentiment(document: Document) -> SentimentResult:
    """Analyze Fed sentiment from document."""
    analyzer = FedSentimentAnalyzer()
    return analyzer.analyze(document)


def extract_key_themes(text: str) -> List[str]:
    """Extract key themes from text."""
    analyzer = FedSentimentAnalyzer()
    doc = Document(content=text, source="text")
    result = analyzer.analyze(doc)
    return result.key_themes


def get_risk_signal(sentiment_score: float) -> str:
    """
    Convert sentiment score to risk signal.
    
    Args:
        sentiment_score: -1.0 to +1.0
        
    Returns:
        "risk_on", "risk_off", or "neutral"
    """
    if sentiment_score >= 0.3:
        return "risk_off"
    elif sentiment_score <= -0.3:
        return "risk_on"
    else:
        return "neutral"
