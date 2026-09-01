# tests/test_phase7_2_compliance_agent.py
"""
Tests for Phase 7.2: Compliance Agent

Run with:
    pytest tests/test_phase7_2_compliance_agent.py -v
"""

import pytest
import sys
import os
from datetime import date, datetime
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from portfolio_tool.database_setup import (
    get_session, Client, Portfolio, PortfolioHolding, Asset, DailyPrice
)
from portfolio_tool.ips_manager import IPSManager
from agents.compliance_agent import (
    ComplianceAgent, 
    run_compliance_check,
    check_portfolio_compliance
)
from agents.decision_schemas import (
    ComplianceStatus,
    ComplianceReport,
    ComplianceCheck,
    ConstraintType,
    BreachSeverity,
    RemediationTrade
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
def compliance_agent():
    """Provide a ComplianceAgent instance."""
    agent = ComplianceAgent()
    yield agent
    agent.close()


@pytest.fixture
def test_portfolio(session):
    """Create a test portfolio with holdings."""
    # Create portfolio
    portfolio = Portfolio(
        name="Test Compliance Portfolio",
        currency="USD",
        cash_balance=50000.0  # $50k cash
    )
    session.add(portfolio)
    session.flush()
    
    # Link to Anders Family Trust
    anders = session.query(Client).filter(Client.client_id == "8821-X").first()
    if anders:
        portfolio.client_id = anders.id
    
    # Create test assets if they don't exist
    test_assets = [
        {"ticker": "AAPL", "name": "Apple Inc", "asset_class": "equity", "sector": "technology"},
        {"ticker": "MSFT", "name": "Microsoft Corp", "asset_class": "equity", "sector": "technology"},
        {"ticker": "BND", "name": "Vanguard Bond ETF", "asset_class": "fixed_income"},
        {"ticker": "BTI", "name": "British American Tobacco", "asset_class": "equity"},  # ESG violation
    ]
    
    assets = {}
    for asset_data in test_assets:
        asset = session.query(Asset).filter(Asset.ticker == asset_data["ticker"]).first()
        if not asset:
            asset = Asset(**asset_data)
            session.add(asset)
            session.flush()
        assets[asset_data["ticker"]] = asset
        
        # Add price data
        existing_price = session.query(DailyPrice).filter(
            DailyPrice.asset_id == asset.id
        ).first()
        if not existing_price:
            price = DailyPrice(
                asset_id=asset.id,
                date=date.today(),
                open=100.0,
                high=105.0,
                low=95.0,
                close=100.0,
                volume=1000000
            )
            session.add(price)
    
    # Add holdings (total ~$1M)
    holdings_data = [
        {"ticker": "AAPL", "quantity": 2000, "price": 150.0},  # $300k (30%)
        {"ticker": "MSFT", "quantity": 1000, "price": 400.0},  # $400k (40%)
        {"ticker": "BND", "quantity": 2000, "price": 75.0},    # $150k (15%)
        {"ticker": "BTI", "quantity": 1000, "price": 35.0},    # $35k (3.5%) - ESG violation
    ]
    
    for h in holdings_data:
        asset = assets[h["ticker"]]
        
        # Update price
        price = session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id).first()
        if price:
            price.close = h["price"]
        
        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=h["quantity"],
            average_price=h["price"]
        )
        session.add(holding)
    
    session.commit()
    
    yield portfolio
    
    # Cleanup
    session.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_id == portfolio.id
    ).delete()
    session.query(Portfolio).filter(Portfolio.id == portfolio.id).delete()
    session.commit()


@pytest.fixture
def concentrated_portfolio(session):
    """Create a portfolio with concentration violations."""
    portfolio = Portfolio(
        name="Concentrated Portfolio",
        currency="USD",
        cash_balance=10000.0
    )
    session.add(portfolio)
    session.flush()
    
    # Link to Anders
    anders = session.query(Client).filter(Client.client_id == "8821-X").first()
    if anders:
        portfolio.client_id = anders.id
    
    # Get or create NVDA
    nvda = session.query(Asset).filter(Asset.ticker == "NVDA").first()
    if not nvda:
        nvda = Asset(ticker="NVDA", name="NVIDIA Corp", asset_class="equity", sector="technology")
        session.add(nvda)
        session.flush()
    
    # Add NVDA price
    price = session.query(DailyPrice).filter(DailyPrice.asset_id == nvda.id).first()
    if not price:
        price = DailyPrice(
            asset_id=nvda.id,
            date=date.today(),
            open=800.0, high=810.0, low=790.0, close=800.0, volume=5000000
        )
        session.add(price)
    else:
        price.close = 800.0
    
    # Add concentrated holding (>5% of portfolio)
    # Portfolio: $10k cash + $90k NVDA = $100k total
    # NVDA = 90% of portfolio (way over 5% limit)
    holding = PortfolioHolding(
        portfolio_id=portfolio.id,
        asset_id=nvda.id,
        quantity=112.5,  # 112.5 * $800 = $90,000
        average_price=800.0
    )
    session.add(holding)
    session.commit()
    
    yield portfolio
    
    # Cleanup
    session.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_id == portfolio.id
    ).delete()
    session.query(Portfolio).filter(Portfolio.id == portfolio.id).delete()
    session.commit()


# =============================================================================
# BASIC TESTS
# =============================================================================

class TestComplianceAgentBasics:
    """Basic tests for ComplianceAgent."""
    
    def test_agent_initialization(self, compliance_agent):
        """Test agent initializes correctly."""
        assert compliance_agent is not None
        assert compliance_agent.config is not None
    
    def test_run_id_generation(self, compliance_agent):
        """Test that run IDs are unique."""
        id1 = compliance_agent._generate_run_id()
        id2 = compliance_agent._generate_run_id()
        
        assert id1.startswith("COMP-")
        assert id2.startswith("COMP-")
        assert id1 != id2  # Should be unique
    
    def test_compliance_check_returns_report(self, compliance_agent, test_portfolio):
        """Test that compliance check returns a report."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        assert isinstance(report, ComplianceReport)
        assert report.portfolio_id == test_portfolio.id
        assert report.compliance_run_id.startswith("COMP-")
    
    def test_report_has_required_fields(self, compliance_agent, test_portfolio):
        """Test report contains all required fields."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        assert report.portfolio_name is not None
        assert report.as_of_date is not None
        assert report.status in ComplianceStatus
        assert report.total_aum > 0
        assert report.num_positions > 0
        assert isinstance(report.allocation, dict)


# =============================================================================
# ALLOCATION TESTS
# =============================================================================

class TestAllocationChecks:
    """Tests for allocation constraint checking."""
    
    def test_detects_equity_allocation(self, compliance_agent, test_portfolio):
        """Test that equity allocation is calculated."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        # Our test portfolio has equity holdings
        assert "equity" in report.allocation
        assert report.allocation["equity"] > 0
    
    def test_allocation_sums_to_one(self, compliance_agent, test_portfolio):
        """Test that allocation weights sum to ~1.0."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        total = sum(report.allocation.values())
        assert 0.99 <= total <= 1.01  # Allow small rounding error


# =============================================================================
# ESG TESTS
# =============================================================================

class TestESGChecks:
    """Tests for ESG screening."""
    
    def test_detects_esg_violation(self, compliance_agent, test_portfolio):
        """Test that ESG violations are detected."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        # BTI should trigger ESG breach
        esg_breaches = [
            b for b in report.breaches 
            if b.constraint_type == ConstraintType.ESG
        ]
        
        assert len(esg_breaches) >= 1
        
        bti_breach = next((b for b in esg_breaches if b.ticker == "BTI"), None)
        assert bti_breach is not None
        assert bti_breach.severity == BreachSeverity.CRITICAL
    
    def test_esg_breach_has_sell_action(self, compliance_agent, test_portfolio):
        """Test that ESG breaches recommend selling."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        esg_breaches = [
            b for b in report.breaches 
            if b.constraint_type == ConstraintType.ESG
        ]
        
        for breach in esg_breaches:
            assert "SELL" in breach.action.upper()


# =============================================================================
# CONCENTRATION TESTS
# =============================================================================

class TestConcentrationChecks:
    """Tests for concentration constraint checking."""
    
    def test_detects_concentration_violation(self, compliance_agent, concentrated_portfolio):
        """Test that concentration violations are detected."""
        report = compliance_agent.run_compliance_check(concentrated_portfolio.id)
        
        concentration_breaches = [
            b for b in report.breaches 
            if b.constraint_type == ConstraintType.CONCENTRATION
        ]
        
        # NVDA at 90% should exceed 5% limit
        assert len(concentration_breaches) >= 1
        
        nvda_breach = next((b for b in concentration_breaches if b.ticker == "NVDA"), None)
        assert nvda_breach is not None
        assert nvda_breach.current_value > nvda_breach.limit_value
    
    def test_concentration_breach_has_trim_action(self, compliance_agent, concentrated_portfolio):
        """Test that concentration breaches recommend trimming."""
        report = compliance_agent.run_compliance_check(concentrated_portfolio.id)
        
        concentration_breaches = [
            b for b in report.breaches 
            if b.constraint_type == ConstraintType.CONCENTRATION
        ]
        
        for breach in concentration_breaches:
            assert "TRIM" in breach.action.upper() or "REDUCE" in breach.action.upper()


# =============================================================================
# STATUS DETERMINATION TESTS
# =============================================================================

class TestStatusDetermination:
    """Tests for compliance status determination."""
    
    def test_critical_breach_means_non_compliant(self, compliance_agent, test_portfolio):
        """Test that critical breaches result in non-compliant status."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        # BTI ESG violation is critical
        has_critical = any(
            b.severity == BreachSeverity.CRITICAL 
            for b in report.breaches
        )
        
        if has_critical:
            assert report.status == ComplianceStatus.NON_COMPLIANT


# =============================================================================
# REMEDIATION TRADE TESTS
# =============================================================================

class TestRemediationTrades:
    """Tests for remediation trade generation."""
    
    def test_generates_remediation_trades(self, compliance_agent, test_portfolio):
        """Test that remediation trades are generated for breaches."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        if report.breaches:
            assert len(report.remediation_trades) > 0
    
    def test_esg_trade_is_full_sell(self, compliance_agent, test_portfolio):
        """Test that ESG violations generate full sell orders."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        esg_trades = [
            t for t in report.remediation_trades 
            if t.breach_type == "esg"
        ]
        
        for trade in esg_trades:
            assert trade.action == "SELL"
            assert trade.shares is not None  # Full position
    
    def test_trades_have_priority(self, compliance_agent, test_portfolio):
        """Test that trades are prioritized."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        if len(report.remediation_trades) > 1:
            priorities = [t.priority for t in report.remediation_trades]
            assert priorities == sorted(priorities)  # Should be in order


# =============================================================================
# REPORT FORMATTING TESTS
# =============================================================================

class TestReportFormatting:
    """Tests for report formatting methods."""
    
    def test_format_summary(self, compliance_agent, test_portfolio):
        """Test summary formatting."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        summary = report.format_summary()
        
        assert "COMPLIANCE REPORT" in summary
        assert report.portfolio_name in summary
        assert report.compliance_run_id in summary
    
    def test_format_breaches_table(self, compliance_agent, test_portfolio):
        """Test breaches table formatting."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        
        if report.breaches:
            table = report.format_breaches_table()
            assert "BREACHES" in table
        else:
            table = report.format_breaches_table()
            assert "No breaches" in table
    
    def test_format_full_report(self, compliance_agent, test_portfolio):
        """Test full report formatting."""
        report = compliance_agent.run_compliance_check(test_portfolio.id)
        full = report.format_full_report()
        
        assert len(full) > 100  # Should be substantial
        assert "COMPLIANCE REPORT" in full


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_run_compliance_check_function(self, test_portfolio):
        """Test run_compliance_check convenience function."""
        report = run_compliance_check(test_portfolio.id)
        
        assert isinstance(report, ComplianceReport)
        assert report.portfolio_id == test_portfolio.id
    
    def test_check_portfolio_compliance_function(self, test_portfolio):
        """Test check_portfolio_compliance convenience function."""
        result = check_portfolio_compliance(test_portfolio.id)
        
        assert "status" in result
        assert "num_breaches" in result
        assert "breaches" in result
        assert isinstance(result["breaches"], list)


# =============================================================================
# CLIENT OVERRIDE TESTS
# =============================================================================

class TestClientOverride:
    """Tests for client ID override functionality."""
    
    def test_can_override_client(self, compliance_agent, session):
        """Test that client can be overridden."""
        # Create a standalone portfolio (no client link)
        portfolio = Portfolio(
            name="Standalone Portfolio",
            currency="USD",
            cash_balance=100000.0
        )
        session.add(portfolio)
        session.commit()
        
        try:
            # Run with Anders client override
            report = compliance_agent.run_compliance_check(
                portfolio.id,
                client_id="8821-X"
            )
            
            assert report.client_id == "8821-X"
            assert report.client_name == "The Anders Family Trust"
        finally:
            session.query(Portfolio).filter(Portfolio.id == portfolio.id).delete()
            session.commit()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
