# tests/test_phase7_1_ips_esg.py
"""
Tests for Phase 7.1: IPS Manager and ESG Screener

Run with:
    pytest tests/test_phase7_1_ips_esg.py -v
"""

import pytest
import sys
import os
from datetime import date
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from portfolio_tool.database_setup import (
    get_session, Client, ClientIPS, ESGExclusion, 
    Portfolio, PortfolioHolding, Asset,
    IPSConstraintType, ESGCategory
)
from portfolio_tool.ips_manager import IPSManager, get_portfolio_constraints
from portfolio_tool.esg_screener import (
    ESGScreener, 
    check_security_esg, 
    check_portfolio_esg,
    is_ticker_excluded
)
from agents.decision_schemas import (
    IPSConstraint, 
    ConstraintType, 
    BreachSeverity,
    ComplianceCheck
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def session():
    """Provide a database session."""
    session = get_session()
    yield session
    session.close()


@pytest.fixture
def ips_manager(session):
    """Provide an IPSManager instance."""
    manager = IPSManager(session=session)
    yield manager


@pytest.fixture
def esg_screener(session):
    """Provide an ESGScreener instance."""
    screener = ESGScreener(session=session)
    yield screener


# =============================================================================
# IPS MANAGER TESTS
# =============================================================================

class TestIPSManager:
    """Tests for IPSManager class."""
    
    def test_get_client_by_id(self, ips_manager):
        """Test fetching client by external ID."""
        client = ips_manager.get_client("8821-X")
        
        assert client is not None
        assert client.name == "The Anders Family Trust"
        assert client.client_type == "trust"
        assert client.risk_profile == "moderate"
    
    def test_get_client_not_found(self, ips_manager):
        """Test fetching non-existent client."""
        client = ips_manager.get_client("NONEXISTENT-999")
        assert client is None
    
    def test_list_clients(self, ips_manager):
        """Test listing all clients."""
        clients = ips_manager.list_clients()
        
        assert len(clients) >= 4
        
        client_ids = [c.client_id for c in clients]
        assert "8821-X" in client_ids
        assert "SMITH-401K" in client_ids
    
    def test_get_client_constraints(self, ips_manager):
        """Test fetching constraints for a client."""
        client = ips_manager.get_client("8821-X")
        assert client is not None
        
        constraints = ips_manager.get_client_constraints(client.id)
        
        assert len(constraints) == 6
        
        for c in constraints:
            assert isinstance(c, IPSConstraint)
            assert isinstance(c.type, ConstraintType)
            assert isinstance(c.breach_severity, BreachSeverity)
    
    def test_get_constraints_filtered_by_type(self, ips_manager):
        """Test filtering constraints by type."""
        client = ips_manager.get_client("8821-X")
        
        esg_constraints = ips_manager.get_client_constraints(
            client.id, 
            constraint_type=ConstraintType.ESG
        )
        
        assert len(esg_constraints) == 2
        
        for c in esg_constraints:
            assert c.type == ConstraintType.ESG
    
    def test_has_esg_constraints(self, ips_manager):
        """Test checking if client has ESG constraints."""
        anders = ips_manager.get_client("8821-X")
        assert ips_manager.has_esg_constraints(anders.id) == True
        
        smith = ips_manager.get_client("SMITH-401K")
        assert ips_manager.has_esg_constraints(smith.id) == False
    
    def test_get_esg_categories(self, ips_manager):
        """Test getting ESG categories for a client."""
        anders = ips_manager.get_client("8821-X")
        categories = ips_manager.get_esg_categories(anders.id)
        
        assert "tobacco" in categories
        assert "thermal_coal" in categories
    
    def test_get_default_constraints(self, ips_manager):
        """Test getting default constraints by risk profile."""
        conservative = ips_manager.get_default_constraints("conservative")
        assert len(conservative) == 4
        
        equity_constraint = next(
            c for c in conservative 
            if c.type == ConstraintType.ALLOCATION and c.asset_class == "equity"
        )
        assert equity_constraint.max_weight == 0.40
        
        aggressive = ips_manager.get_default_constraints("aggressive")
        equity_constraint = next(
            c for c in aggressive 
            if c.type == ConstraintType.ALLOCATION and c.asset_class == "equity"
        )
        assert equity_constraint.max_weight == 0.90
    
    def test_constraint_dataclass_conversion(self, ips_manager):
        """Test that DB rows convert correctly to dataclasses."""
        client = ips_manager.get_client("8821-X")
        constraints = ips_manager.get_client_constraints(client.id)
        
        equity = next(
            c for c in constraints 
            if c.type == ConstraintType.ALLOCATION and c.asset_class == "equity"
        )
        
        assert equity.name == "Max Equity Exposure"
        assert equity.max_weight == 0.65
        assert equity.tolerance == 0.05
        assert equity.breach_severity == BreachSeverity.HIGH
    
    def test_constraint_with_exemptions(self, ips_manager):
        """Test constraints with exemptions are loaded correctly."""
        client = ips_manager.get_client("8821-X")
        constraints = ips_manager.get_client_constraints(client.id)
        
        concentration = next(
            c for c in constraints 
            if c.type == ConstraintType.CONCENTRATION
        )
        
        assert concentration.max_weight == 0.05
        assert len(concentration.exemptions) == 2
        assert "asset_subclass:government_bond" in concentration.exemptions


# =============================================================================
# ESG SCREENER TESTS
# =============================================================================

class TestESGScreener:
    """Tests for ESGScreener class."""
    
    def test_get_exclusion_set(self, esg_screener):
        """Test loading exclusion set."""
        exclusions = esg_screener.get_exclusion_set()
        
        assert len(exclusions) > 0
        assert "ticker:BTI" in exclusions
        
        bti = exclusions["ticker:BTI"]
        assert bti["category"] == "tobacco"
        assert "British American Tobacco" in bti["company_name"]
    
    def test_get_exclusion_set_filtered(self, esg_screener):
        """Test filtering exclusion set by category."""
        tobacco_only = esg_screener.get_exclusion_set(categories=["tobacco"])
        
        for key, exc in tobacco_only.items():
            assert exc["category"] == "tobacco"
    
    def test_check_security_excluded(self, esg_screener):
        """Test checking an excluded security."""
        result = esg_screener.check_security(ticker="BTI")
        
        assert result["excluded"] == True
        assert result["category"] == "tobacco"
        assert "tobacco" in result["reason"].lower()
    
    def test_check_security_not_excluded(self, esg_screener):
        """Test checking a non-excluded security."""
        result = esg_screener.check_security(ticker="AAPL")
        
        assert result["excluded"] == False
    
    def test_check_security_by_isin(self, esg_screener):
        """Test checking by ISIN."""
        result = esg_screener.check_security(isin="GB0002875804")
        
        assert result["excluded"] == True
        assert result["category"] == "tobacco"
    
    def test_is_excluded_convenience(self, esg_screener):
        """Test is_excluded convenience method."""
        assert esg_screener.is_excluded(ticker="BTI") == True
        assert esg_screener.is_excluded(ticker="AAPL") == False
        assert esg_screener.is_excluded(ticker="PM") == True
    
    def test_get_excluded_tickers(self, esg_screener):
        """Test getting set of excluded tickers."""
        tickers = esg_screener.get_excluded_tickers()
        
        assert "BTI" in tickers
        assert "PM" in tickers
        assert "MO" in tickers
        assert "LMT" in tickers
    
    def test_get_excluded_tickers_filtered(self, esg_screener):
        """Test getting excluded tickers with category filter."""
        tobacco_tickers = esg_screener.get_excluded_tickers(categories=["tobacco"])
        
        assert "BTI" in tobacco_tickers
        assert "PM" in tobacco_tickers
        assert "LMT" not in tobacco_tickers
    
    def test_check_holdings_list(self, esg_screener):
        """Test checking a list of holdings."""
        holdings = [
            {"ticker": "AAPL", "quantity": 100, "price": 150.0},
            {"ticker": "BTI", "quantity": 50, "price": 35.0},
            {"ticker": "MSFT", "quantity": 75, "price": 400.0},
        ]
        
        breaches = esg_screener.check_holdings_list(holdings)
        
        assert len(breaches) == 1
        assert breaches[0].ticker == "BTI"
        assert breaches[0].status == "breach"
        assert breaches[0].severity == BreachSeverity.CRITICAL
        assert breaches[0].constraint_type == ConstraintType.ESG
    
    def test_breach_has_action(self, esg_screener):
        """Test that breaches include recommended action."""
        holdings = [
            {"ticker": "BTI", "quantity": 100, "price": 35.0},
        ]
        
        breaches = esg_screener.check_holdings_list(holdings)
        
        assert len(breaches) == 1
        assert breaches[0].action is not None
        assert "SELL" in breaches[0].action
        assert "BTI" in breaches[0].action
    
    def test_exclusion_stats(self, esg_screener):
        """Test getting exclusion statistics."""
        stats = esg_screener.get_exclusion_stats()
        
        assert "tobacco" in stats
        assert stats["tobacco"] >= 4


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_check_security_esg_function(self):
        """Test check_security_esg convenience function."""
        result = check_security_esg(ticker="BTI")
        assert result["excluded"] == True
        
        result = check_security_esg(ticker="AAPL")
        assert result["excluded"] == False
    
    def test_is_ticker_excluded_function(self):
        """Test is_ticker_excluded convenience function."""
        assert is_ticker_excluded("BTI") == True
        assert is_ticker_excluded("AAPL") == False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining IPS Manager and ESG Screener."""
    
    def test_client_esg_categories_match_screener(self, ips_manager, esg_screener):
        """Test that client ESG categories can be used with screener."""
        anders = ips_manager.get_client("8821-X")
        categories = ips_manager.get_esg_categories(anders.id)
        
        assert "tobacco" in categories
        
        exclusions = esg_screener.get_exclusion_set(categories=categories)
        
        for exc in exclusions.values():
            assert exc["category"] in categories
    
    def test_workflow_load_constraints_then_screen(self, ips_manager, esg_screener):
        """Test the typical workflow: load constraints, then screen."""
        client = ips_manager.get_client("8821-X")
        assert client is not None
        
        has_esg = ips_manager.has_esg_constraints(client.id)
        assert has_esg == True
        
        categories = ips_manager.get_esg_categories(client.id)
        assert len(categories) > 0
        
        holdings = [
            {"ticker": "AAPL", "quantity": 100, "price": 150.0},
            {"ticker": "BTI", "quantity": 50, "price": 35.0},
            {"ticker": "BTU", "quantity": 30, "price": 20.0},
        ]
        
        breaches = esg_screener.check_holdings_list(holdings, categories=categories)
        
        assert len(breaches) == 2
        tickers_in_breach = [b.ticker for b in breaches]
        assert "BTI" in tickers_in_breach
        assert "BTU" in tickers_in_breach


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])