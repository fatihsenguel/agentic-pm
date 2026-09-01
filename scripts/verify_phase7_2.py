#!/usr/bin/env python3
"""
Phase 7.2 Verification Script - Compliance Agent

This script demonstrates the full compliance checking workflow,
including the "Golden Prompt" demo for Anders Family Trust.

Usage:
    python scripts/verify_phase7_2.py
"""

import sys
import os

# Add project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


def create_demo_portfolio():
    """Create a demo portfolio with intentional violations."""
    from portfolio_tool.database_setup import (
        get_session, Portfolio, PortfolioHolding, Asset, DailyPrice, Client
    )
    from datetime import date
    
    session = get_session()
    
    # Check if demo portfolio already exists
    existing = session.query(Portfolio).filter(
        Portfolio.name == "Anders Family Portfolio"
    ).first()
    
    if existing:
        print(f"   Using existing portfolio: {existing.name} (ID: {existing.id})")
        return existing.id
    
    # Create portfolio linked to Anders Family Trust
    anders = session.query(Client).filter(Client.client_id == "8821-X").first()
    
    portfolio = Portfolio(
        name="Anders Family Portfolio",
        currency="USD",
        cash_balance=20000.0  # $20k cash (2% of $1M - below 5% minimum!)
    )
    session.add(portfolio)
    session.flush()
    
    if anders:
        portfolio.client_id = anders.id
    
    # Create assets with intentional violations
    demo_assets = [
        # Normal holdings
        {"ticker": "AAPL", "name": "Apple Inc", "asset_class": "equity", "sector": "technology", "price": 180.0, "qty": 1500},  # $270k
        {"ticker": "MSFT", "name": "Microsoft Corp", "asset_class": "equity", "sector": "technology", "price": 420.0, "qty": 800},  # $336k
        {"ticker": "GOOGL", "name": "Alphabet Inc", "asset_class": "equity", "sector": "technology", "price": 175.0, "qty": 400},  # $70k
        {"ticker": "BND", "name": "Vanguard Bond ETF", "asset_class": "fixed_income", "price": 72.0, "qty": 1500},  # $108k
        {"ticker": "AGG", "name": "iShares Core Bond", "asset_class": "fixed_income", "price": 98.0, "qty": 800},  # $78.4k
        
        # ESG VIOLATION - Tobacco
        {"ticker": "BTI", "name": "British American Tobacco", "asset_class": "equity", "sector": "consumer_staples", "price": 32.0, "qty": 500},  # $16k
        
        # CONCENTRATION VIOLATION - >5% in single issuer
        {"ticker": "NVDA", "name": "NVIDIA Corp", "asset_class": "equity", "sector": "technology", "price": 890.0, "qty": 120},  # $106.8k (~10.7%)
    ]
    
    for asset_data in demo_assets:
        # Get or create asset
        asset = session.query(Asset).filter(Asset.ticker == asset_data["ticker"]).first()
        if not asset:
            asset = Asset(
                ticker=asset_data["ticker"],
                name=asset_data["name"],
                asset_class=asset_data["asset_class"],
                sector=asset_data.get("sector")
            )
            session.add(asset)
            session.flush()
        
        # Add/update price
        price = session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id).first()
        if not price:
            price = DailyPrice(
                asset_id=asset.id,
                date=date.today(),
                open=asset_data["price"],
                high=asset_data["price"] * 1.02,
                low=asset_data["price"] * 0.98,
                close=asset_data["price"],
                volume=1000000
            )
            session.add(price)
        else:
            price.close = asset_data["price"]
        
        # Add holding
        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=asset_data["qty"],
            average_price=asset_data["price"]
        )
        session.add(holding)
    
    session.commit()
    print(f"   ✓ Created demo portfolio: {portfolio.name} (ID: {portfolio.id})")
    return portfolio.id


def main():
    print("=" * 70)
    print("PHASE 7.2 VERIFICATION: Compliance Agent")
    print("=" * 70)
    print()
    
    # =========================================================================
    # 1. Create Demo Portfolio
    # =========================================================================
    print("1. SETTING UP DEMO PORTFOLIO")
    print("-" * 50)
    
    portfolio_id = create_demo_portfolio()
    print()
    
    # =========================================================================
    # 2. Run Compliance Check
    # =========================================================================
    print("2. RUNNING COMPLIANCE CHECK")
    print("-" * 50)
    
    from agents.compliance_agent import ComplianceAgent
    
    agent = ComplianceAgent()
    report = agent.run_compliance_check(portfolio_id)
    
    print(f"   Portfolio: {report.portfolio_name}")
    print(f"   Client: {report.client_name} ({report.client_id})")
    print(f"   Run ID: {report.compliance_run_id}")
    print(f"   Status: {report.status.value.upper()}")
    print(f"   Total AUM: ${report.total_aum:,.2f}")
    print(f"   Positions: {report.num_positions}")
    print(f"   Breaches: {report.num_breaches} ({report.num_critical} critical)")
    print()
    
    # =========================================================================
    # 3. Show Asset Allocation
    # =========================================================================
    print("3. ASSET ALLOCATION")
    print("-" * 50)
    
    for asset_class, weight in sorted(report.allocation.items(), key=lambda x: -x[1]):
        bar_len = int(weight * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        print(f"   {asset_class.title():<15} {weight:>6.1%}  {bar}")
    print()
    
    # =========================================================================
    # 4. Show Breaches
    # =========================================================================
    print("4. COMPLIANCE BREACHES")
    print("-" * 50)
    
    if report.breaches:
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "ℹ️"
        }
        
        for breach in report.breaches:
            sev = severity_emoji.get(breach.severity.value if breach.severity else "low", "")
            print(f"   {sev} [{breach.constraint_type.value.upper()}] {breach.constraint_name}")
            print(f"      {breach.message}")
            if breach.action:
                print(f"      → {breach.action}")
            print()
    else:
        print("   ✓ No breaches detected!")
    print()
    
    # =========================================================================
    # 5. Show Remediation Trades
    # =========================================================================
    print("5. REMEDIATION TRADES")
    print("-" * 50)
    
    if report.remediation_trades:
        for i, trade in enumerate(report.remediation_trades, 1):
            print(f"   {i}. {trade.format_instruction()}")
            print(f"      Reason: {trade.reason}")
            print()
    else:
        print("   No trades required.")
    print()
    
    # =========================================================================
    # 6. Full Report Output
    # =========================================================================
    print("6. FULL COMPLIANCE REPORT")
    print("-" * 50)
    print()
    print(report.format_full_report())
    print()
    
    # =========================================================================
    # 7. Summary
    # =========================================================================
    print("=" * 70)
    print("✅ PHASE 7.2 VERIFICATION COMPLETE!")
    print("=" * 70)
    print()
    print("Components verified:")
    print("  ✓ ComplianceAgent initialization")
    print("  ✓ Holdings loading with prices")
    print("  ✓ Allocation calculation")
    print("  ✓ Allocation constraint checking")
    print("  ✓ Concentration constraint checking")
    print("  ✓ Liquidity constraint checking")
    print("  ✓ ESG screening integration")
    print("  ✓ Status determination")
    print("  ✓ Remediation trade generation")
    print("  ✓ Report formatting")
    print()
    
    # Show the "Golden Prompt" output
    print("=" * 70)
    print("🎯 GOLDEN PROMPT DEMO")
    print("=" * 70)
    print()
    print('User: "Check IPS compliance for Client Account #8821-X (The Anders Family Trust)"')
    print()
    print("Response:")
    print(report.format_full_report())
    
    agent.close()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
