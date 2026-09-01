#!/usr/bin/env python3
"""
Seed Sample Clients and IPS Constraints

Phase: 7.0 - Compliance Schema Foundation

This script creates demo clients with realistic IPS constraints.
The "Anders Family Trust" is the example from the BlackRock demo.

Usage:
    python scripts/seed_sample_clients.py
    
    # Or from Python:
    from scripts.seed_sample_clients import seed_sample_clients
    seed_sample_clients()
"""

import sys
import os
from datetime import date

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Add Project Root (so 'import src...' works)
sys.path.insert(0, PROJECT_ROOT)

# 2. ADD THIS LINE: Add 'src' directory specifically (so 'import portfolio_tool...' works)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import (
    get_session, Client, ClientIPS, IPSConstraintType, Portfolio
)


# =============================================================================
# SAMPLE CLIENT DATA
# =============================================================================

SAMPLE_CLIENTS = [
    # -------------------------------------------------------------------------
    # THE GOLDEN DEMO: Anders Family Trust
    # This matches the BlackRock example from the roadmap
    # -------------------------------------------------------------------------
    {
        "client_id": "8821-X",
        "name": "The Anders Family Trust",
        "client_type": "trust",
        "risk_profile": "moderate",
        "tax_status": "taxable",
        "jurisdiction": "US",
        "constraints": [
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Max Equity Exposure",
                "asset_class": "equity",
                "max_weight": 0.65,
                "tolerance": 0.05,  # Can drift to 70% before breach
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Min Fixed Income",
                "asset_class": "fixed_income",
                "min_weight": 0.20,
                "target_weight": 0.30,
                "tolerance": 0.05,
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.LIQUIDITY,
                "name": "Min Cash Allocation",
                "asset_class": "cash",
                "min_weight": 0.05,
                "tolerance": 0.02,
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.CONCENTRATION,
                "name": "Single Issuer Limit",
                "max_weight": 0.05,
                "tolerance": 0.01,
                "exemptions": ["asset_subclass:government_bond", "asset_subclass:money_market"],
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.ESG,
                "name": "No Tobacco Producers",
                "rule_json": {"category": "tobacco", "zero_tolerance": True},
                "breach_severity": "critical",
            },
            {
                "type": IPSConstraintType.ESG,
                "name": "No Thermal Coal",
                "rule_json": {"category": "thermal_coal", "revenue_threshold": 0.10},
                "breach_severity": "critical",
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # CONSERVATIVE CLIENT: Retirement Account
    # -------------------------------------------------------------------------
    {
        "client_id": "SMITH-401K",
        "name": "Smith Family 401(k)",
        "client_type": "individual",
        "risk_profile": "conservative",
        "tax_status": "tax_deferred",
        "jurisdiction": "US",
        "constraints": [
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Max Equity Exposure",
                "asset_class": "equity",
                "max_weight": 0.40,
                "tolerance": 0.05,
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Min Fixed Income",
                "asset_class": "fixed_income",
                "min_weight": 0.40,
                "tolerance": 0.05,
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.LIQUIDITY,
                "name": "Min Cash Buffer",
                "asset_class": "cash",
                "min_weight": 0.10,
                "tolerance": 0.02,
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.CONCENTRATION,
                "name": "Single Issuer Limit",
                "max_weight": 0.05,
                "tolerance": 0.01,
                "exemptions": ["asset_subclass:government_bond"],
                "breach_severity": "high",
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # AGGRESSIVE CLIENT: Endowment
    # -------------------------------------------------------------------------
    {
        "client_id": "UNIV-ENDOW-01",
        "name": "University Endowment Fund",
        "client_type": "endowment",
        "risk_profile": "aggressive",
        "tax_status": "tax_exempt",
        "jurisdiction": "US",
        "constraints": [
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Max Equity Exposure",
                "asset_class": "equity",
                "max_weight": 0.80,
                "tolerance": 0.05,
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Min Alternatives",
                "asset_class": "alternatives",
                "min_weight": 0.10,
                "tolerance": 0.05,
                "breach_severity": "low",
            },
            {
                "type": IPSConstraintType.LIQUIDITY,
                "name": "Min Liquidity",
                "asset_class": "cash",
                "min_weight": 0.02,
                "tolerance": 0.01,
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.CONCENTRATION,
                "name": "Single Issuer Limit",
                "max_weight": 0.08,
                "tolerance": 0.02,
                "exemptions": ["asset_subclass:government_bond"],
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.SECTOR,
                "name": "Tech Sector Cap",
                "sector": "technology",
                "max_weight": 0.35,
                "tolerance": 0.05,
                "breach_severity": "medium",
            },
            {
                "type": IPSConstraintType.ESG,
                "name": "No Tobacco",
                "rule_json": {"category": "tobacco", "zero_tolerance": True},
                "breach_severity": "critical",
            },
            {
                "type": IPSConstraintType.ESG,
                "name": "No Private Prisons",
                "rule_json": {"category": "private_prisons", "zero_tolerance": True},
                "breach_severity": "critical",
            },
            {
                "type": IPSConstraintType.ESG,
                "name": "No Controversial Weapons",
                "rule_json": {"category": "controversial_weapons", "zero_tolerance": True},
                "breach_severity": "critical",
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # CORPORATE CLIENT: Pension Fund
    # -------------------------------------------------------------------------
    {
        "client_id": "ACME-PENSION",
        "name": "ACME Corp Defined Benefit Pension",
        "client_type": "pension",
        "risk_profile": "moderately_conservative",
        "tax_status": "tax_exempt",
        "jurisdiction": "US",
        "constraints": [
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Max Equity Exposure",
                "asset_class": "equity",
                "max_weight": 0.50,
                "target_weight": 0.40,
                "tolerance": 0.05,
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.ALLOCATION,
                "name": "Min Fixed Income (LDI)",
                "asset_class": "fixed_income",
                "min_weight": 0.45,
                "target_weight": 0.55,
                "tolerance": 0.05,
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.LIQUIDITY,
                "name": "Benefit Payment Reserve",
                "asset_class": "cash",
                "min_weight": 0.03,
                "tolerance": 0.01,
                "breach_severity": "critical",  # Must meet benefit payments
            },
            {
                "type": IPSConstraintType.CONCENTRATION,
                "name": "Single Issuer Limit",
                "max_weight": 0.05,
                "tolerance": 0.01,
                "exemptions": ["asset_subclass:government_bond"],
                "breach_severity": "high",
            },
            {
                "type": IPSConstraintType.DURATION,
                "name": "Duration Target",
                "rule_json": {"min_duration": 8, "max_duration": 12, "target": 10},
                "breach_severity": "medium",
            },
        ]
    },
]


def seed_sample_clients(clear_existing: bool = False, link_portfolio_id: int = None) -> dict:
    """
    Seed sample clients and their IPS constraints.
    
    Args:
        clear_existing: If True, delete all existing clients first
        link_portfolio_id: If provided, link this portfolio to Anders Family Trust
    
    Returns:
        Dict with counts: {"clients": N, "constraints": N}
    """
    session = get_session()
    results = {"clients": 0, "constraints": 0, "skipped": 0}
    
    try:
        if clear_existing:
            # Delete constraints first (cascade should handle, but be explicit)
            session.query(ClientIPS).delete()
            deleted = session.query(Client).delete()
            print(f"Cleared {deleted} existing clients and their constraints")
            session.commit()
        
        for client_data in SAMPLE_CLIENTS:
            # Check if client already exists
            existing = session.query(Client).filter(
                Client.client_id == client_data["client_id"]
            ).first()
            
            if existing:
                results["skipped"] += 1
                print(f"  Skipping existing client: {client_data['client_id']}")
                continue
            
            # Create client
            client = Client(
                client_id=client_data["client_id"],
                name=client_data["name"],
                client_type=client_data["client_type"],
                risk_profile=client_data["risk_profile"],
                tax_status=client_data.get("tax_status"),
                jurisdiction=client_data.get("jurisdiction"),
                is_active=True
            )
            session.add(client)
            session.flush()  # Get the ID
            
            results["clients"] += 1
            print(f"✓ Created client: {client.client_id} - {client.name}")
            
            # Create constraints
            for constraint_data in client_data.get("constraints", []):
                constraint = ClientIPS(
                    client_id=client.id,
                    constraint_type=constraint_data["type"],
                    constraint_name=constraint_data["name"],
                    asset_class=constraint_data.get("asset_class"),
                    sector=constraint_data.get("sector"),
                    min_weight=constraint_data.get("min_weight"),
                    max_weight=constraint_data.get("max_weight"),
                    target_weight=constraint_data.get("target_weight"),
                    tolerance=constraint_data.get("tolerance", 0.05),
                    rule_json=constraint_data.get("rule_json"),
                    exemptions=constraint_data.get("exemptions"),
                    breach_severity=constraint_data.get("breach_severity", "high"),
                    effective_date=date.today(),
                    is_active=True
                )
                session.add(constraint)
                results["constraints"] += 1
            
            print(f"  └─ Added {len(client_data.get('constraints', []))} constraints")
            
            # Link portfolio to Anders Family Trust if requested
            if link_portfolio_id and client_data["client_id"] == "8821-X":
                portfolio = session.query(Portfolio).get(link_portfolio_id)
                if portfolio:
                    portfolio.client_id = client.id
                    print(f"  └─ Linked to portfolio: {portfolio.name}")
        
        session.commit()
        print(f"\n✓ Seeding complete: {results['clients']} clients, {results['constraints']} constraints")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding clients: {e}")
        raise
    
    finally:
        session.close()
    
    return results


def list_clients() -> None:
    """Print all clients and their constraints."""
    session = get_session()
    
    try:
        clients = session.query(Client).filter(
            Client.is_active == True
        ).order_by(Client.name).all()
        
        print(f"\n{'='*70}")
        print(f"CLIENTS ({len(clients)} active)")
        print(f"{'='*70}")
        
        for client in clients:
            constraints = session.query(ClientIPS).filter(
                ClientIPS.client_id == client.id,
                ClientIPS.is_active == True
            ).all()
            
            # Check if linked to any portfolios
            portfolios = session.query(Portfolio).filter(
                Portfolio.client_id == client.id
            ).all()
            
            print(f"\n{client.client_id}: {client.name}")
            print(f"  Type: {client.client_type} | Risk: {client.risk_profile} | Tax: {client.tax_status or 'N/A'}")
            print(f"  Portfolios: {', '.join(p.name for p in portfolios) or 'None linked'}")
            print(f"  Constraints ({len(constraints)}):")
            
            for c in constraints:
                limit = ""
                if c.max_weight:
                    limit = f"max {c.max_weight:.0%}"
                elif c.min_weight:
                    limit = f"min {c.min_weight:.0%}"
                
                target = c.asset_class or c.sector or "portfolio"
                print(f"    • {c.constraint_name}: {target} {limit} [{c.breach_severity}]")
        
        print(f"\n{'='*70}\n")
        
    finally:
        session.close()


def link_portfolio_to_client(portfolio_id: int, client_id: str) -> bool:
    """Link an existing portfolio to a client."""
    session = get_session()
    
    try:
        client = session.query(Client).filter(Client.client_id == client_id).first()
        if not client:
            print(f"✗ Client not found: {client_id}")
            return False
        
        portfolio = session.query(Portfolio).get(portfolio_id)
        if not portfolio:
            print(f"✗ Portfolio not found: {portfolio_id}")
            return False
        
        portfolio.client_id = client.id
        session.commit()
        
        print(f"✓ Linked portfolio '{portfolio.name}' to client '{client.name}'")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error linking portfolio: {e}")
        return False
    
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed sample clients and IPS constraints")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    parser.add_argument("--list", action="store_true", help="List existing clients")
    parser.add_argument("--link", type=int, metavar="PORTFOLIO_ID", 
                       help="Link this portfolio ID to Anders Family Trust")
    args = parser.parse_args()
    
    if args.list:
        list_clients()
    elif args.link:
        link_portfolio_to_client(args.link, "8821-X")
    else:
        seed_sample_clients(clear_existing=args.clear)
        list_clients()
