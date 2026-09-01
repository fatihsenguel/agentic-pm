#!/usr/bin/env python3
"""
Seed ESG Exclusion Data

Phase: 7.0 - Compliance Schema Foundation

This script populates the esg_exclusions table with realistic demo data.
In production, this data would come from ESG providers like MSCI, 
Sustainalytics, or ISS.

Usage:
    python scripts/seed_esg_exclusions.py
    
    # Or from Python:
    from scripts.seed_esg_exclusions import seed_esg_exclusions
    seed_esg_exclusions()
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
    get_session, ESGExclusion, ESGCategory
)


# =============================================================================
# ESG EXCLUSION DATA
# =============================================================================
# This is realistic sample data for demo purposes.
# Sources would typically be: MSCI ESG Manager, Sustainalytics, ISS ESG

ESG_EXCLUSIONS = [
    # -------------------------------------------------------------------------
    # TOBACCO (Major Producers)
    # -------------------------------------------------------------------------
    {
        "isin": "GB0002875804",
        "ticker": "BTI",
        "company_name": "British American Tobacco PLC",
        "category": ESGCategory.TOBACCO,
        "subcategory": "tobacco_producer",
        "reason": "Major tobacco manufacturer - cigarettes represent >95% of revenue",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US7181721090",
        "ticker": "PM",
        "company_name": "Philip Morris International Inc",
        "category": ESGCategory.TOBACCO,
        "subcategory": "tobacco_producer",
        "reason": "Major tobacco manufacturer - international cigarette sales",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US0298991011",
        "ticker": "MO",
        "company_name": "Altria Group Inc",
        "category": ESGCategory.TOBACCO,
        "subcategory": "tobacco_producer",
        "reason": "Major tobacco manufacturer - Marlboro brand owner",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "JP3726800000",
        "ticker": "JAPAY",
        "company_name": "Japan Tobacco Inc",
        "category": ESGCategory.TOBACCO,
        "subcategory": "tobacco_producer",
        "reason": "Major tobacco manufacturer - global cigarette producer",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US4461501045",
        "ticker": "TPB",
        "company_name": "Turning Point Brands Inc",
        "category": ESGCategory.TOBACCO,
        "subcategory": "tobacco_producer",
        "reason": "Smokeless tobacco and smoking accessories manufacturer",
        "source": "Sustainalytics",
    },
    
    # -------------------------------------------------------------------------
    # THERMAL COAL (Mining & Power)
    # -------------------------------------------------------------------------
    {
        "isin": "US6708371033",
        "ticker": "BTU",
        "company_name": "Peabody Energy Corporation",
        "category": ESGCategory.THERMAL_COAL,
        "subcategory": "thermal_coal_mining",
        "reason": "Largest private-sector coal company - >90% revenue from thermal coal",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US12626K2033",
        "ticker": "CNX",
        "company_name": "CNX Resources Corporation",
        "category": ESGCategory.THERMAL_COAL,
        "subcategory": "coal_production",
        "reason": "Natural gas and coal production company",
        "source": "Sustainalytics",
        "revenue_threshold": 0.30,  # Only if >30% revenue
    },
    {
        "isin": "US0026881099",
        "ticker": "ARLP",
        "company_name": "Alliance Resource Partners LP",
        "category": ESGCategory.THERMAL_COAL,
        "subcategory": "thermal_coal_mining",
        "reason": "Coal producer and marketer in eastern United States",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US0036541003",
        "ticker": "ARCH",
        "company_name": "Arch Resources Inc",
        "category": ESGCategory.THERMAL_COAL,
        "subcategory": "thermal_coal_mining",
        "reason": "Major US coal producer - metallurgical and thermal coal",
        "source": "MSCI ESG Manager",
    },
    
    # -------------------------------------------------------------------------
    # CONTROVERSIAL WEAPONS
    # -------------------------------------------------------------------------
    {
        "isin": "US5398301094",
        "ticker": "LMT",
        "company_name": "Lockheed Martin Corporation",
        "category": ESGCategory.CONTROVERSIAL_WEAPONS,
        "subcategory": "nuclear_weapons_systems",
        "reason": "Involved in nuclear weapons delivery systems (Trident II missiles)",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US6974351057",
        "ticker": "RTX",
        "company_name": "RTX Corporation",
        "category": ESGCategory.CONTROVERSIAL_WEAPONS,
        "subcategory": "cluster_munitions",
        "reason": "Historical involvement in cluster munitions components",
        "source": "Sustainalytics",
    },
    {
        "isin": "US6153691059",
        "ticker": "NOC",
        "company_name": "Northrop Grumman Corporation",
        "category": ESGCategory.CONTROVERSIAL_WEAPONS,
        "subcategory": "nuclear_weapons_systems",
        "reason": "Nuclear weapons systems contractor (B-21 bomber)",
        "source": "MSCI ESG Manager",
    },
    {
        "isin": "US0970231058",
        "ticker": "BA",
        "company_name": "Boeing Company",
        "category": ESGCategory.CONTROVERSIAL_WEAPONS,
        "subcategory": "nuclear_weapons_delivery",
        "reason": "Nuclear weapons delivery systems (Minuteman III)",
        "source": "MSCI ESG Manager",
    },
    
    # -------------------------------------------------------------------------
    # GAMBLING (Casinos & Online)
    # -------------------------------------------------------------------------
    {
        "isin": "US5178341070",
        "ticker": "LVS",
        "company_name": "Las Vegas Sands Corp",
        "category": ESGCategory.GAMBLING,
        "subcategory": "casino_operator",
        "reason": "Major integrated resort and casino operator",
        "source": "internal",
    },
    {
        "isin": "US9618381017",
        "ticker": "WYNN",
        "company_name": "Wynn Resorts Limited",
        "category": ESGCategory.GAMBLING,
        "subcategory": "casino_operator",
        "reason": "Luxury casino resort operator",
        "source": "internal",
    },
    {
        "isin": "US5765881083",
        "ticker": "MGM",
        "company_name": "MGM Resorts International",
        "category": ESGCategory.GAMBLING,
        "subcategory": "casino_operator",
        "reason": "Major casino and hospitality company",
        "source": "internal",
    },
    {
        "isin": "IE00BK9ZQ967",
        "ticker": "FLTR",
        "company_name": "Flutter Entertainment PLC",
        "category": ESGCategory.GAMBLING,
        "subcategory": "online_gambling",
        "reason": "Online sports betting and gaming company (FanDuel, PokerStars)",
        "source": "internal",
    },
    {
        "isin": "US26614N1028",
        "ticker": "DKNG",
        "company_name": "DraftKings Inc",
        "category": ESGCategory.GAMBLING,
        "subcategory": "online_gambling",
        "reason": "Digital sports entertainment and gaming company",
        "source": "internal",
    },
    
    # -------------------------------------------------------------------------
    # PRIVATE PRISONS
    # -------------------------------------------------------------------------
    {
        "isin": "US22025Y4070",
        "ticker": "CXW",
        "company_name": "CoreCivic Inc",
        "category": ESGCategory.PRIVATE_PRISONS,
        "subcategory": "prison_operator",
        "reason": "Largest private prison operator in the United States",
        "source": "Sustainalytics",
    },
    {
        "isin": "US3647601083",
        "ticker": "GEO",
        "company_name": "The GEO Group Inc",
        "category": ESGCategory.PRIVATE_PRISONS,
        "subcategory": "prison_operator",
        "reason": "Private prison and detention facility operator",
        "source": "Sustainalytics",
    },
    
    # -------------------------------------------------------------------------
    # ADULT ENTERTAINMENT
    # -------------------------------------------------------------------------
    {
        "isin": "US7170811035",
        "ticker": "RICK",
        "company_name": "RCI Hospitality Holdings Inc",
        "category": ESGCategory.ADULT_ENTERTAINMENT,
        "subcategory": "adult_clubs",
        "reason": "Operator of adult nightclubs and restaurants",
        "source": "internal",
    },
    
    # -------------------------------------------------------------------------
    # WEAPONS (Conventional - for strict ESG policies)
    # -------------------------------------------------------------------------
    {
        "isin": "US8085131055",
        "ticker": "SWBI",
        "company_name": "Smith & Wesson Brands Inc",
        "category": ESGCategory.WEAPONS,
        "subcategory": "firearms_manufacturer",
        "reason": "Civilian firearms manufacturer",
        "source": "internal",
    },
    {
        "isin": "US85207U1051",
        "ticker": "RGR",
        "company_name": "Sturm Ruger & Company Inc",
        "category": ESGCategory.WEAPONS,
        "subcategory": "firearms_manufacturer",
        "reason": "Civilian firearms manufacturer",
        "source": "internal",
    },
]


def seed_esg_exclusions(clear_existing: bool = False) -> dict:
    """
    Seed the ESG exclusions table with demo data.
    
    Args:
        clear_existing: If True, delete all existing exclusions first
    
    Returns:
        Dict with counts: {"inserted": N, "skipped": N, "errors": N}
    """
    session = get_session()
    results = {"inserted": 0, "skipped": 0, "errors": 0}
    
    try:
        if clear_existing:
            deleted = session.query(ESGExclusion).delete()
            print(f"Cleared {deleted} existing ESG exclusions")
            session.commit()
        
        for exc_data in ESG_EXCLUSIONS:
            # Check if already exists (by ISIN or ticker)
            existing = None
            if exc_data.get("isin"):
                existing = session.query(ESGExclusion).filter(
                    ESGExclusion.isin == exc_data["isin"]
                ).first()
            if not existing and exc_data.get("ticker"):
                existing = session.query(ESGExclusion).filter(
                    ESGExclusion.ticker == exc_data["ticker"]
                ).first()
            
            if existing:
                results["skipped"] += 1
                continue
            
            # Create new exclusion
            exclusion = ESGExclusion(
                isin=exc_data.get("isin"),
                ticker=exc_data.get("ticker"),
                company_name=exc_data["company_name"],
                category=exc_data["category"],
                subcategory=exc_data.get("subcategory"),
                reason=exc_data["reason"],
                source=exc_data.get("source", "manual"),
                effective_date=exc_data.get("effective_date", date.today()),
                revenue_threshold=exc_data.get("revenue_threshold"),
                is_active=True
            )
            
            session.add(exclusion)
            results["inserted"] += 1
        
        session.commit()
        print(f"✓ ESG Exclusions seeded: {results['inserted']} inserted, {results['skipped']} skipped")
        
    except Exception as e:
        session.rollback()
        results["errors"] += 1
        print(f"✗ Error seeding ESG exclusions: {e}")
        raise
    
    finally:
        session.close()
    
    return results


def list_esg_exclusions() -> None:
    """Print all ESG exclusions in the database."""
    session = get_session()
    
    try:
        exclusions = session.query(ESGExclusion).filter(
            ESGExclusion.is_active == True
        ).order_by(ESGExclusion.category).all()
        
        print(f"\n{'='*70}")
        print(f"ESG EXCLUSIONS ({len(exclusions)} active)")
        print(f"{'='*70}")
        
        current_category = None
        for exc in exclusions:
            if exc.category != current_category:
                current_category = exc.category
                print(f"\n{current_category.value.upper().replace('_', ' ')}")
                print("-" * 50)
            
            print(f"  {exc.ticker or 'N/A':<8} {exc.company_name[:40]:<42} [{exc.source}]")
        
        print(f"\n{'='*70}\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed ESG exclusion data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    parser.add_argument("--list", action="store_true", help="List existing exclusions")
    args = parser.parse_args()
    
    if args.list:
        list_esg_exclusions()
    else:
        seed_esg_exclusions(clear_existing=args.clear)
        list_esg_exclusions()
