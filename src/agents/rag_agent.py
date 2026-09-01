# src/agents/rag_agent.py
"""
RAG Agent - The "Researcher" for Document-Backed Decisions.

Phase: 6.7 - RAG Integration (Phase 3: RAG Agent)

PURPOSE:
Orchestrate document search and insight extraction to feed into Decision Engine:
- Search indexed documents based on query context
- Extract risk factors from filings
- Analyze Fed sentiment
- Provide citations for decision rationale

DESIGN PRINCIPLES:
- Deterministic workflow (no LLM decides what to search)
- Context-aware: Uses portfolio holdings and query to guide search
- Hot Potato: Returns aggregated insights, not raw documents
- Integration-ready: Output matches DocumentInsights schema

ARCHITECTURE:
    User Query: "Should I increase my NVDA position given recent earnings?"
                │
                ▼
        ┌───────────────┐
        │   RAG Agent   │
        │               │
        │ 1. Parse context (ticker=NVDA, topic=earnings)
        │ 2. Search documents (filtered by ticker)
        │ 3. Extract key findings
        │ 4. Identify risk factors
        │ 5. Build DocumentInsights
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Decision Engine │ ← DocumentInsights as input
        └───────────────┘

USAGE:
    from agents.rag_agent import RAGAgent
    
    agent = RAGAgent()
    insights = agent.research(
        query="What did NVIDIA report last quarter?",
        context={"ticker": "NVDA", "portfolio_holdings": [...]}
    )
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RAGAgentConfig:
    """Configuration for RAG Agent."""
    
    # Search settings
    default_top_k: int = 5
    min_relevance_score: float = 0.2
    
    # Context extraction
    extract_tickers_from_query: bool = True
    use_portfolio_context: bool = True
    
    # Fed sentiment
    analyze_fed_for_macro: bool = True
    fed_sentiment_use_llm: bool = True
    
    # Output limits
    max_key_findings: int = 5
    max_risk_factors: int = 3
    max_citations: int = 5


# =============================================================================
# RAG AGENT
# =============================================================================

class RAGAgent:
    """
    The "Researcher" Agent - searches documents and extracts insights.
    
    This agent is called by the LangGraph dispatcher when document context
    is needed for a decision. It returns DocumentInsights that feed into
    the Decision Engine.
    
    Key responsibilities:
    1. Parse query to understand what's being asked
    2. Search relevant documents with appropriate filters
    3. Extract key findings and risk factors
    4. Optionally analyze Fed sentiment for macro context
    5. Return structured insights for Decision Engine
    """
    
    def __init__(self, config: Optional[RAGAgentConfig] = None):
        """
        Initialize RAG Agent.
        
        Args:
            config: Agent configuration (uses defaults if not provided)
        """
        self.config = config or RAGAgentConfig()

    def research(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point - research documents based on query and context.
        
        This method orchestrates the full research workflow:
        1. Extract context (tickers, topics) from query
        2. Search documents with filters
        3. Extract insights from results
        4. Optionally analyze Fed sentiment
        5. Return DocumentInsights-compatible dict
        
        Args:
            query: User's question/request
            context: Optional context dict with:
                - ticker: Specific ticker to focus on
                - portfolio_holdings: List of holdings for context
                - include_fed_sentiment: Whether to analyze Fed
                - doc_types: List of doc types to search
                
        Returns:
            Dict matching DocumentInsights structure
        """
        context = context or {}
        
        logger.info(f"RAG Agent researching: {query[:100]}...")
        
        # Step 1: Extract search context
        search_context = self._extract_search_context(query, context)
        logger.debug(f"Search context: {search_context}")
        
        # Step 2: Search documents
        search_results = self._search_documents(query, search_context)
        
        # Step 3: Extract insights from results
        insights = self._extract_insights(query, search_results, search_context)
        
        # Step 4: Fed sentiment (if relevant)
        if self._should_analyze_fed(query, context):
            fed_result = self._analyze_fed_sentiment()
            if fed_result:
                insights["fed_sentiment"] = fed_result
                # Add Fed context to findings if significant
                if fed_result.get("success") and abs(fed_result.get("score", 0)) > 0.3:
                    stance = "hawkish" if fed_result["score"] > 0 else "dovish"
                    insights["key_findings"].insert(0, 
                        f"Fed stance: {stance} (score: {fed_result['score']:.2f})"
                    )
        
        # Step 5: Build final response
        insights["query"] = query
        insights["generated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"RAG Agent found {len(insights.get('sources', []))} sources, "
                   f"{len(insights.get('key_findings', []))} findings")
        
        return insights
    
    def _extract_search_context(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract search parameters from query and context.
        
        Determines:
        - Which tickers to search for
        - What document types are relevant
        - What topics to focus on
        """
        search_context = {
            "tickers": set(),
            "doc_types": [],
            "topics": [],
            "year": None,
        }
        
        # Explicit ticker from context
        if context.get("ticker"):
            search_context["tickers"].add(context["ticker"].upper())
        
        # Extract tickers from query
        if self.config.extract_tickers_from_query:
            tickers = self._extract_tickers_from_text(query)
            search_context["tickers"].update(tickers)
        
        # Use portfolio holdings for context
        if self.config.use_portfolio_context and context.get("portfolio_holdings"):
            for holding in context["portfolio_holdings"]:
                if isinstance(holding, dict) and holding.get("ticker"):
                    search_context["tickers"].add(holding["ticker"].upper())
        
        # Determine relevant doc types from query
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["earnings", "quarter", "revenue", "profit"]):
            search_context["doc_types"].append("earnings")
            search_context["topics"].append("financial_performance")
        
        if any(kw in query_lower for kw in ["10-k", "10k", "annual", "filing"]):
            search_context["doc_types"].append("10k")
            search_context["topics"].append("annual_report")
        
        if any(kw in query_lower for kw in ["10-q", "10q", "quarterly filing"]):
            search_context["doc_types"].append("10q")
        
        if any(kw in query_lower for kw in ["risk", "concern", "challenge", "threat"]):
            search_context["topics"].append("risk_factors")
        
        if any(kw in query_lower for kw in ["fed", "fomc", "interest rate", "monetary"]):
            search_context["doc_types"].append("fed_minutes")
            search_context["topics"].append("monetary_policy")
        
        # Extract year if mentioned
        year_match = re.search(r'\b(202[0-9])\b', query)
        if year_match:
            search_context["year"] = int(year_match.group(1))
        
        # Convert ticker set to list
        search_context["tickers"] = list(search_context["tickers"])
        
        return search_context
    
    def _extract_tickers_from_text(self, text: str) -> Set[str]:
        """Extract stock tickers from text."""
        # Common ticker patterns
        # Match 1-5 uppercase letters that look like tickers
        potential_tickers = re.findall(r'\b([A-Z]{1,5})\b', text)
        
        # Filter out common words that aren't tickers
        non_tickers = {
            "I", "A", "THE", "AND", "OR", "FOR", "TO", "IN", "ON", "AT",
            "IS", "IT", "BE", "AS", "BY", "OF", "IF", "MY", "AI", "Q1",
            "Q2", "Q3", "Q4", "CEO", "CFO", "IPO", "ETF", "GDP", "FED",
            "SEC", "USA", "USD", "EUR", "YOY", "QOQ", "EPS", "PE", "ROE",
        }
        
        return {t for t in potential_tickers if t not in non_tickers and len(t) >= 2}
    
    def _search_documents(
        self,
        query: str,
        search_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Search documents using RAG tools.
        
        Executes multiple searches if needed:
        - One per ticker (if multiple)
        - General search if no specific tickers
        """
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.rag_tools import search_documents
        
        all_results = []
        seen_content = set()  # Dedup
        
        tickers = search_context.get("tickers", [])
        doc_types = search_context.get("doc_types", [])
        year = search_context.get("year")
        
        # Search per ticker
        if tickers:
            for ticker in tickers[:3]:  # Limit to 3 tickers
                for doc_type in (doc_types or [None]):
                    result = search_documents(
                        query=query,
                        ticker=ticker,
                        doc_type=doc_type,
                        year=year,
                        top_k=self.config.default_top_k,
                        min_score=self.config.min_relevance_score,
                    )
                    
                    if result.get("success"):
                        for r in result.get("results", []):
                            # Dedup by content hash
                            content_hash = hash(r.get("content", "")[:100])
                            if content_hash not in seen_content:
                                seen_content.add(content_hash)
                                all_results.append(r)
        
        # General search (no ticker filter)
        if not tickers or len(all_results) < 3:
            for doc_type in (doc_types or [None]):
                result = search_documents(
                    query=query,
                    doc_type=doc_type,
                    year=year,
                    top_k=self.config.default_top_k,
                    min_score=self.config.min_relevance_score,
                )
                
                if result.get("success"):
                    for r in result.get("results", []):
                        content_hash = hash(r.get("content", "")[:100])
                        if content_hash not in seen_content:
                            seen_content.add(content_hash)
                            all_results.append(r)
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return all_results[:self.config.default_top_k * 2]  # Return top results
    
    def _extract_insights(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        search_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract structured insights from search results.
        
        Builds DocumentInsights-compatible structure.
        """
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import DocumentInsights, create_empty_insights
        
        if not search_results:
            empty = create_empty_insights(query)
            return empty.to_dict()
        
        # Extract unique sources
        sources = list(set(
            r.get("filename") for r in search_results 
            if r.get("filename")
        ))[:5]
        
        # Extract relevant tickers
        relevant_tickers = list(set(
            r.get("ticker") for r in search_results 
            if r.get("ticker")
        ))
        
        # Extract key findings from top results
        key_findings = []
        for r in search_results[:self.config.max_key_findings]:
            content = r.get("content", "")
            # Truncate and clean
            finding = content[:200].strip()
            if len(content) > 200:
                # Try to end at sentence boundary
                last_period = finding.rfind('.')
                if last_period > 100:
                    finding = finding[:last_period + 1]
                else:
                    finding += "..."
            
            if finding and finding not in key_findings:
                key_findings.append(finding)
        
        # Extract risk factors
        risk_factors = self._extract_risk_factors(search_results)
        
        # Build citations
        citations = []
        for r in search_results[:self.config.max_citations]:
            citations.append({
                "text": r.get("content", "")[:150],
                "source": r.get("citation", r.get("filename", "Unknown")),
            })
        
        # Calculate sentiment from content (simple heuristic)
        sentiment = self._estimate_content_sentiment(search_results)
        
        # Calculate average score
        scores = [r.get("score", 0) for r in search_results if r.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "sources": sources,
            "key_findings": key_findings,
            "risk_factors": risk_factors,
            "citations": citations,
            "sentiment": sentiment,
            "relevant_tickers": relevant_tickers,
            "total_chunks_searched": len(search_results),
            "top_k_returned": min(len(search_results), self.config.default_top_k),
            "avg_relevance_score": round(avg_score, 3),
        }
    
    def _extract_risk_factors(
        self,
        search_results: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract risk factors from search results."""
        risk_factors = []
        risk_keywords = [
            "risk", "concern", "uncertainty", "challenge", 
            "restriction", "limitation", "volatility", "decline",
            "loss", "competition", "regulation", "lawsuit",
        ]
        
        for r in search_results:
            content = r.get("content", "").lower()
            
            # Check if this chunk contains risk-related content
            if not any(kw in content for kw in risk_keywords):
                continue
            
            # Extract sentences containing risk keywords
            sentences = r.get("content", "").split('.')
            for sent in sentences:
                sent_lower = sent.lower()
                if any(kw in sent_lower for kw in risk_keywords):
                    risk_text = sent.strip()[:150]
                    if risk_text and len(risk_text) > 20:
                        # Add citation
                        source = r.get("filename", "")
                        page = r.get("page")
                        citation = f" ({source}" + (f", p.{page})" if page else ")")
                        
                        full_risk = risk_text + citation
                        if full_risk not in risk_factors:
                            risk_factors.append(full_risk)
                            
                            if len(risk_factors) >= self.config.max_risk_factors:
                                return risk_factors
        
        return risk_factors
    
    def _estimate_content_sentiment(
        self,
        search_results: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Estimate overall sentiment from document content."""
        if not search_results:
            return None
        
        positive_keywords = [
            "growth", "increase", "strong", "exceed", "beat",
            "positive", "improved", "record", "momentum", "robust",
        ]
        negative_keywords = [
            "decline", "decrease", "weak", "miss", "below",
            "negative", "concern", "risk", "challenge", "loss",
        ]
        
        positive_count = 0
        negative_count = 0
        
        for r in search_results:
            content = r.get("content", "").lower()
            positive_count += sum(1 for kw in positive_keywords if kw in content)
            negative_count += sum(1 for kw in negative_keywords if kw in content)
        
        total = positive_count + negative_count
        if total < 3:
            return None  # Not enough signal
        
        ratio = (positive_count - negative_count) / total
        
        if ratio > 0.3:
            return "bullish"
        elif ratio < -0.3:
            return "bearish"
        else:
            return "neutral"
    
    def _should_analyze_fed(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> bool:
        """Determine if Fed sentiment analysis is relevant."""
        if not self.config.analyze_fed_for_macro:
            return False
        
        if context.get("include_fed_sentiment") is False:
            return False
        
        if context.get("include_fed_sentiment") is True:
            return True
        
        # Check query for Fed-related keywords
        fed_keywords = [
            "fed", "fomc", "interest rate", "monetary policy",
            "rate cut", "rate hike", "powell", "inflation",
            "macro", "economy", "recession",
        ]
        
        query_lower = query.lower()
        return any(kw in query_lower for kw in fed_keywords)
    
    def _analyze_fed_sentiment(self) -> Optional[Dict[str, Any]]:
        """Analyze latest Fed minutes sentiment."""
        try:
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.rag_tools import analyze_fed_minutes
            
            result = analyze_fed_minutes(use_llm=self.config.fed_sentiment_use_llm)
            
            if result.get("success"):
                return result.get("sentiment")
            else:
                logger.warning(f"Fed analysis failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.warning(f"Fed sentiment analysis error: {e}")
            return None

        
    def create_rag_agent(config: Optional[RAGAgentConfig] = None) -> "RAGAgent":
            """
            Factory function to create a RAG Agent.
            
            Matches the pattern of other agents for consistency.
            
            Args:
                config: Optional configuration
                
            Returns:
                Configured RAGAgent instance
            """
            return RAGAgent(config=config)

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def research_documents(
    query: str,
    ticker: Optional[str] = None,
    include_fed: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function for document research.
    
    Args:
        query: Research question
        ticker: Specific ticker to focus on
        include_fed: Whether to analyze Fed sentiment
        
    Returns:
        DocumentInsights-compatible dict
    """
    agent = RAGAgent()
    
    context = {}
    if ticker:
        context["ticker"] = ticker
    if include_fed:
        context["include_fed_sentiment"] = True
    
    return agent.research(query, context)
