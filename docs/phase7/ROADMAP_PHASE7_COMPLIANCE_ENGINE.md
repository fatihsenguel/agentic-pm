# 🏛️ ROADMAP: Phase 7 — Compliance Engine
## Agentic Finance: BlackRock/Aladdin-Style IPS Compliance

**Version:** 1.0.0  
**Date:** January 28, 2026  
**Goal:** Replicate the BlackRock/Aladdin compliance workflow 1:1  
**Estimated Duration:** 20-25 working days  

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Target Behavior](#2-target-behavior)
3. [Current State Analysis](#3-current-state-analysis)
4. [Architecture Overview](#4-architecture-overview)
5. [Phase 7.0: Schema Foundation](#5-phase-70-schema-foundation)
6. [Phase 7.1: IPS Constraint System](#6-phase-71-ips-constraint-system)
7. [Phase 7.2: ESG Screening Module](#7-phase-72-esg-screening-module)
8. [Phase 7.3: Compliance Agent](#8-phase-73-compliance-agent)
9. [Phase 7.4: Router & Graph Integration](#9-phase-74-router--graph-integration)
10. [Phase 7.5: Decision Engine Integration](#10-phase-75-decision-engine-integration)
11. [Phase 7.6: IPS Document Extraction](#11-phase-76-ips-document-extraction-rag)
12. [Phase 7.7: Compliance Reporting](#12-phase-77-compliance-reporting--output)
13. [Phase 7.8: Hardening & Polish](#13-phase-78-hardening--polish)
14. [Test Strategy](#14-test-strategy)
15. [Interview Demo Prompts](#15-interview-demo-prompts)
16. [File Manifest](#16-file-manifest)

---

## 1. Executive Summary

### What We're Building

A **Compliance Agent** that mirrors institutional workflows:

```
User: "Check IPS compliance for Client Account #8821-X (The Anders Family Trust)"

System:
1. Fetch live holdings (with ISIN, sector, currency)
2. Load client's IPS constraints from document/database
3. Compare current allocation vs. target ranges
4. Run ESG negative screening
5. Calculate concentration risk with exemptions
6. Generate severity-tiered compliance memo
```

### Key Deliverables

| Deliverable | Description |
|-------------|-------------|
| **Client & IPS Tables** | Multi-client support with per-client constraints |
| **ESG Screening** | Negative screening against exclusion lists |
| **Compliance Agent** | Orchestrates all compliance checks |
| **Severity Tiers** | 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM classification |
| **IPS Extraction** | Auto-parse constraints from uploaded PDFs |
| **Compliance Memo** | PM-style output matching BlackRock format |

---

## 2. Target Behavior

### The "Golden Prompt" — What Success Looks Like

```
User: Check IPS compliance for Client Account #8821-X (The Anders Family Trust). 
      Flag any breaches immediately.
```

### Expected System Trace

```
[10:42:01.052] [SYSTEM]  Initializing Multi-Agent Swarm...
[10:42:01.210] [ORCHESTRATOR] 🟢 RECEIVED PROMPT. Client: #8821-X.
[10:42:01.215] [ORCHESTRATOR] ⚙️ DECOMPOSING TASK:
    1. Fetch live portfolio holdings
    2. Load client IPS constraints
    3. Compare allocation vs. target ranges
    4. Run ESG negative screening
    5. Calculate concentration risk
    6. Generate Compliance Report

[10:42:01.450] [DATA_AGENT] 🔍 FETCHING HOLDINGS...
    > Retrieved 42 positions. Total AUM: $14,250,400.

[10:42:01.800] [COMPLIANCE_AGENT] 🧠 PARSING IPS CONSTRAINTS:
    > CONSTRAINT 1: "Max Equity: 65% (+/- 5% drift)"
    > CONSTRAINT 2: "Single Issuer < 5% (excl. Treasuries)"
    > CONSTRAINT 3: "Min Cash: 5%"
    > CONSTRAINT 4: "ESG: No Tobacco/Coal"

[10:42:02.350] [COMPLIANCE_AGENT] 📉 CHECKING EXPOSURES:
    > Equity: 70.0% → [WARNING: AT UPPER LIMIT]
    > Cash: 2.0% → [FAIL: BELOW MINIMUM]

[10:42:02.500] [COMPLIANCE_AGENT] 🕵️ ESG SCREENING:
    > British American Tobacco (GB0002875804) → HARD BREACH

[10:42:02.750] [RISK_AGENT] ⚡ CONCENTRATION CHECK:
    > NVDA at 6.2% → BREACH (limit: 5.0%)

[10:42:03.200] [REPORTER] 📝 GENERATING COMPLIANCE MEMO...
```

### Expected Output

```
═══════════════════════════════════════════════════════════════
                     COMPLIANCE REPORT
═══════════════════════════════════════════════════════════════
CLIENT: The Anders Family Trust (#8821-X)
DATE: 2026-01-28 | 10:42 AM CET
STATUS: 🔴 NON-COMPLIANT / ACTION REQUIRED

───────────────────────────────────────────────────────────────
1. EXECUTIVE SUMMARY
───────────────────────────────────────────────────────────────
The portfolio is currently in breach of 3 specific IPS mandates.
Immediate rebalancing is recommended.

───────────────────────────────────────────────────────────────
2. DETAILED BREACHES
───────────────────────────────────────────────────────────────
┌──────────┬─────────────┬──────────────────────┬─────────┬───────┬────────────────┐
│ Severity │ Category    │ Constraint           │ Current │ Limit │ Action         │
├──────────┼─────────────┼──────────────────────┼─────────┼───────┼────────────────┤
│ 🔴 CRIT  │ ESG         │ No Tobacco Producers │ 0.8%    │ 0%    │ SELL IMMEDIATE │
│ 🟠 HIGH  │ Concentr.   │ Single Issuer Limit  │ 6.2%    │ 5.0%  │ TRIM 1.2%      │
│ 🟡 MED   │ Liquidity   │ Min Cash Allocation  │ 2.0%    │ 5.0%  │ RAISE CASH     │
└──────────┴─────────────┴──────────────────────┴─────────┴───────┴────────────────┘

───────────────────────────────────────────────────────────────
3. ASSET ALLOCATION DRIFT
───────────────────────────────────────────────────────────────
• Equity:       70.0% (Upper Limit: 70%) → ⚠️ Watch List
• Fixed Income: 28.0% (Target: 30%)      → ✓ Within Range
• Cash:          2.0% (Min: 5%)          → ❌ Breach

───────────────────────────────────────────────────────────────
4. RECOMMENDED ACTIONS
───────────────────────────────────────────────────────────────
1. SELL entire position in British American Tobacco (~$114k)
2. TRIM NVIDIA Corp by ~$170k to bring weight to 5%
3. ALLOCATE proceeds to USD Sweep Vehicle (restore Cash >5%)

Trace ID: #8821-COMPLIANCE-20260128-104203
═══════════════════════════════════════════════════════════════
```

---

## 3. Current State Analysis

### What Exists (Your System)

| Component | Status | Location |
|-----------|--------|----------|
| `Asset` model | ✅ Has sector, currency | `database_setup.py:28` |
| `Portfolio` model | ✅ Exists | `database_setup.py:401` |
| `PortfolioHolding` | ✅ Exists | `database_setup.py:426` |
| `DecisionLog` | ✅ Has risk_status, key_risks | `database_setup.py:457` |
| `RiskAssessment` schema | ✅ Has breaches list | `decision_schemas.py:44` |
| `PMDecisionSummary` | ✅ Has document_citations | `decision_schemas.py:97` |
| `ExecutionIntent` enum | ✅ Extensible | `schemas.py:35` |
| `AgentName` enum | ✅ Extensible | `schemas.py:64` |
| RAG Pipeline | ✅ Can search documents | `rag/` module |

### What's Missing (Gap Analysis)

| Component | Gap | Impact |
|-----------|-----|--------|
| `Client` table | ❌ No multi-client support | Can't associate IPS per client |
| `ClientIPS` table | ❌ No structured constraints | Can't enforce rules |
| `ESGExclusion` table | ❌ No exclusion lists | Can't screen holdings |
| `ComplianceBreach` table | ❌ No breach audit log | No compliance history |
| `ISIN` field on Asset | ⚠️ Missing | Can't cross-reference ESG databases |
| `asset_subclass` field | ⚠️ Missing | Can't apply exemptions (e.g., "excl. Treasuries") |
| Compliance Agent | ❌ Does not exist | Core gap |
| IPS Parser | ❌ Does not exist | Can't extract constraints from docs |
| Severity classification | ❌ Not in RiskAssessment | No tiered breaches |

---

## 4. Architecture Overview

### New Components (Phase 7)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│            "Check compliance for Client #8821-X"                            │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🎯 SMART ROUTER                                           │
│   query_intent: DECISION                                                    │
│   execution_intent: COMPLIANCE_CHECK  ← NEW                                 │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────────┐         ┌─────────────────┐
│  📊 DATA AGENT  │            │ ⚖️ COMPLIANCE AGENT │         │   📄 RAG AGENT  │
│  Fetch holdings │───────────▶│      (NEW!)         │◀────────│  IPS extraction │
│  with ISIN/sector│           │                     │         │                 │
└─────────────────┘            │  1. Load IPS        │         └─────────────────┘
                               │  2. Check allocation│
                               │  3. Check conc.     │
                               │  4. ESG screening   │
                               │  5. Classify breach │
                               └──────────┬──────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🧠 DECISION ENGINE (Enhanced)                        │
│   RiskAssessment now includes: compliance_breaches: List[ComplianceCheck]   │
│   PMDecisionSummary includes: compliance_status, remediation_actions        │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SYNTHESIZER                                     │
│                    Generates Compliance Memo Output                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Database Tables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEW TABLES (Phase 7.0)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  clients                    client_ips                 esg_exclusions        │
│  ┌──────────────────┐      ┌──────────────────────┐   ┌──────────────────┐  │
│  │ id               │      │ id                   │   │ id               │  │
│  │ client_id (uniq) │◀────▶│ client_id (FK)       │   │ isin             │  │
│  │ name             │      │ constraint_type      │   │ ticker           │  │
│  │ type             │      │ asset_class          │   │ company_name     │  │
│  │ risk_profile     │      │ min_weight           │   │ category         │  │
│  │ created_at       │      │ max_weight           │   │ reason           │  │
│  └──────────────────┘      │ tolerance            │   │ source           │  │
│          │                 │ exemptions (JSON)    │   │ effective_date   │  │
│          │                 │ effective_date       │   └──────────────────┘  │
│          ▼                 └──────────────────────┘                         │
│  portfolios (existing)                                                       │
│  ┌──────────────────┐      compliance_breaches                              │
│  │ + client_id (FK) │      ┌──────────────────────┐                         │
│  └──────────────────┘      │ id                   │                         │
│                            │ portfolio_id (FK)    │                         │
│  assets (existing)         │ constraint_id (FK)   │                         │
│  ┌──────────────────┐      │ breach_type          │                         │
│  │ + isin           │      │ severity             │                         │
│  │ + asset_subclass │      │ current_value        │                         │
│  └──────────────────┘      │ limit_value          │                         │
│                            │ timestamp            │                         │
│                            │ resolved             │                         │
│                            └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Phase 7.0: Schema Foundation

**Goal:** Extend database to support compliance workflows  
**Duration:** 1-2 days  
**Dependencies:** None  

### Task 7.0.1: Extend `Asset` Table

Add fields for compliance identification:

```python
# In database_setup.py, modify Asset class:

class Asset(Base):
    __tablename__ = 'assets'
    
    # ... existing fields ...
    
    # NEW FIELDS (Phase 7.0)
    isin = Column(String(12), nullable=True, unique=True, index=True)
    # ISIN format: 2-letter country + 9 alphanum + 1 check digit
    # Example: "US0378331005" (Apple), "GB0002875804" (BAT)
    
    asset_subclass = Column(String(50), nullable=True)
    # Examples: "large_cap_equity", "government_bond", "corporate_bond", 
    #           "money_market", "commodity", "reit"
    # Used for exemptions like "excluding US Treasuries"
    
    is_esg_excluded = Column(Boolean, default=False, index=True)
    # Quick flag set by ESG screening - denormalized for performance
```

**Migration SQL:**
```sql
ALTER TABLE assets ADD COLUMN isin VARCHAR(12) UNIQUE;
ALTER TABLE assets ADD COLUMN asset_subclass VARCHAR(50);
ALTER TABLE assets ADD COLUMN is_esg_excluded BOOLEAN DEFAULT FALSE;

CREATE INDEX ix_assets_isin ON assets(isin);
CREATE INDEX ix_assets_subclass ON assets(asset_subclass);
CREATE INDEX ix_assets_esg ON assets(is_esg_excluded);
```

### Task 7.0.2: Create `Client` Table

```python
class Client(Base):
    """
    Represents an investment client (individual, trust, institution).
    
    Each client has their own IPS (Investment Policy Statement) with
    unique constraints, risk tolerance, and restrictions.
    
    Example:
        Client(
            client_id="8821-X",
            name="The Anders Family Trust",
            client_type="trust",
            risk_profile="moderate"
        )
    """
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), unique=True, nullable=False, index=True)
    # External identifier (e.g., "8821-X", "ACME-001")
    
    name = Column(String(200), nullable=False)
    # Display name (e.g., "The Anders Family Trust")
    
    client_type = Column(String(50), nullable=False)
    # "individual", "trust", "foundation", "pension", "endowment", "corporate"
    
    risk_profile = Column(String(50), nullable=False, default="moderate")
    # "conservative", "moderate", "aggressive", "custom"
    
    tax_status = Column(String(50), nullable=True)
    # "taxable", "tax_exempt", "tax_deferred"
    
    jurisdiction = Column(String(50), nullable=True)
    # "US", "EU", "UK", etc. - affects regulatory requirements
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, 
                       onupdate=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship('Portfolio', back_populates='client')
    ips_constraints = relationship('ClientIPS', back_populates='client', 
                                   cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Client(id={self.client_id}, name='{self.name}', type='{self.client_type}')>"
```

### Task 7.0.3: Create `ClientIPS` Table

```python
class IPSConstraintType(enum.Enum):
    """Types of IPS constraints."""
    ALLOCATION = "allocation"         # Asset class min/max (e.g., "Equity 60-70%")
    CONCENTRATION = "concentration"   # Single issuer limit (e.g., "No >5%")
    LIQUIDITY = "liquidity"           # Cash minimums (e.g., "Min 5% cash")
    SECTOR = "sector"                 # Sector limits (e.g., "Tech <30%")
    DURATION = "duration"             # Bond duration limits
    CREDIT = "credit"                 # Credit quality minimums
    ESG = "esg"                       # ESG exclusions
    GEOGRAPHY = "geography"           # Country/region limits
    CURRENCY = "currency"             # Currency exposure limits


class ClientIPS(Base):
    """
    Investment Policy Statement constraints for a client.
    
    Each row represents ONE constraint from the client's IPS.
    A client typically has 5-15 constraints.
    
    Example Constraints:
        - "Max Equity: 65% (+/- 5%)"
        - "No single issuer > 5% (excluding US Treasuries)"
        - "Min Cash: 5%"
        - "No Tobacco producers"
    """
    __tablename__ = 'client_ips'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), 
                       nullable=False, index=True)
    
    # Constraint identification
    constraint_type = Column(Enum(IPSConstraintType), nullable=False)
    constraint_name = Column(String(100), nullable=False)
    # Human-readable name, e.g., "Equity Allocation Limit"
    
    # Target specification
    asset_class = Column(String(50), nullable=True)
    # "equity", "fixed_income", "cash", "alternatives", "real_estate"
    # NULL for constraints that span classes (e.g., concentration)
    
    sector = Column(String(50), nullable=True)
    # For sector-specific constraints, e.g., "technology", "energy"
    
    # Numeric limits
    min_weight = Column(Float, nullable=True)
    max_weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)
    tolerance = Column(Float, nullable=True, default=0.05)
    # Drift tolerance before flagging (e.g., 0.05 = 5%)
    
    # Rule specification (for complex constraints)
    rule_json = Column(JSON, nullable=True)
    # Stores complex rules like:
    # {"type": "single_issuer", "max": 0.05, "exemptions": ["asset_subclass:government_bond"]}
    
    # Exemptions
    exemptions = Column(JSON, nullable=True)
    # List of exempted categories, e.g., ["US Treasury", "Money Market"]
    
    # Severity when breached
    breach_severity = Column(String(20), default="high")
    # "critical", "high", "medium", "low"
    
    # Validity
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Source tracking
    source_document = Column(String(255), nullable=True)
    # Reference to IPS document, e.g., "IPS_8821_X_v2024.pdf"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    
    # Relationships
    client = relationship('Client', back_populates='ips_constraints')
    
    __table_args__ = (
        Index('ix_ips_client_type', 'client_id', 'constraint_type'),
        Index('ix_ips_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ClientIPS(client={self.client_id}, type='{self.constraint_type.value}', name='{self.constraint_name}')>"
```

### Task 7.0.4: Create `ESGExclusion` Table

```python
class ESGCategory(enum.Enum):
    """ESG exclusion categories."""
    TOBACCO = "tobacco"
    COAL = "thermal_coal"
    WEAPONS = "weapons"
    CONTROVERSIAL_WEAPONS = "controversial_weapons"
    GAMBLING = "gambling"
    ADULT_ENTERTAINMENT = "adult_entertainment"
    NUCLEAR = "nuclear"
    PALM_OIL = "palm_oil"
    PRIVATE_PRISONS = "private_prisons"
    ANIMAL_TESTING = "animal_testing"
    OTHER = "other"


class ESGExclusion(Base):
    """
    ESG exclusion list - securities that fail ESG screening.
    
    This table is populated from external ESG data providers
    (e.g., MSCI ESG Manager) or manually maintained.
    
    Example:
        ESGExclusion(
            isin="GB0002875804",
            ticker="BTI",
            company_name="British American Tobacco",
            category=ESGCategory.TOBACCO,
            reason="Tobacco producer - fails ESG screen",
            source="MSCI ESG Manager"
        )
    """
    __tablename__ = 'esg_exclusions'
    
    id = Column(Integer, primary_key=True)
    
    # Security identification (at least one required)
    isin = Column(String(12), nullable=True, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    company_name = Column(String(200), nullable=False)
    
    # Exclusion details
    category = Column(Enum(ESGCategory), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    # More specific, e.g., "Tobacco - Manufacturer" vs "Tobacco - Retailer"
    
    reason = Column(String(500), nullable=False)
    # Human-readable explanation
    
    # Source and validity
    source = Column(String(100), nullable=False)
    # "MSCI", "Sustainalytics", "ISS", "internal", "manual"
    
    effective_date = Column(Date, nullable=False, default=datetime.date.today)
    expiry_date = Column(Date, nullable=True)
    # NULL = no expiry (permanent exclusion)
    
    is_active = Column(Boolean, default=True, index=True)
    
    # Revenue threshold (some exclusions only apply if >X% revenue)
    revenue_threshold = Column(Float, nullable=True)
    # e.g., 0.05 = only exclude if >5% revenue from activity
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        Index('ix_esg_isin', 'isin'),
        Index('ix_esg_ticker', 'ticker'),
        Index('ix_esg_category', 'category'),
        Index('ix_esg_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ESGExclusion(company='{self.company_name}', category='{self.category.value}')>"
```

### Task 7.0.5: Create `ComplianceBreach` Table

```python
class BreachSeverity(enum.Enum):
    """Severity levels for compliance breaches."""
    CRITICAL = "critical"   # 🔴 Immediate action required
    HIGH = "high"           # 🟠 Action required within 24-48h
    MEDIUM = "medium"       # 🟡 Review in next rebalance
    LOW = "low"             # ℹ️ Informational only


class ComplianceBreach(Base):
    """
    Audit log of all compliance breaches.
    
    Every time a compliance check finds a breach, it's logged here.
    This provides:
    - Historical audit trail for regulators
    - Tracking of breach resolution
    - Analytics on recurring issues
    
    Example:
        ComplianceBreach(
            portfolio_id=1,
            constraint_id=5,
            breach_type="concentration",
            severity=BreachSeverity.HIGH,
            current_value=0.062,
            limit_value=0.05,
            ticker="NVDA",
            description="Single issuer limit exceeded: 6.2% vs 5.0% max"
        )
    """
    __tablename__ = 'compliance_breaches'
    
    id = Column(Integer, primary_key=True)
    
    # What portfolio and constraint?
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    constraint_id = Column(Integer, ForeignKey('client_ips.id', ondelete='SET NULL'),
                          nullable=True, index=True)
    # NULL if breach is from ESG screening (not IPS constraint)
    
    # Breach classification
    breach_type = Column(String(50), nullable=False)
    # "allocation", "concentration", "liquidity", "esg", "sector", etc.
    
    severity = Column(Enum(BreachSeverity), nullable=False, index=True)
    
    # Breach details
    current_value = Column(Float, nullable=False)
    limit_value = Column(Float, nullable=False)
    
    # What security/asset class is involved?
    ticker = Column(String(20), nullable=True)
    isin = Column(String(12), nullable=True)
    asset_class = Column(String(50), nullable=True)
    
    # Human-readable description
    description = Column(String(500), nullable=False)
    
    # Recommended action
    recommended_action = Column(String(500), nullable=True)
    
    # Timing
    detected_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Resolution tracking
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(String(500), nullable=True)
    
    # Link to compliance run
    compliance_run_id = Column(String(50), nullable=True, index=True)
    # Groups all breaches from one compliance check
    
    __table_args__ = (
        Index('ix_breach_portfolio', 'portfolio_id'),
        Index('ix_breach_severity', 'severity'),
        Index('ix_breach_resolved', 'resolved'),
        Index('ix_breach_detected', 'detected_at'),
    )
    
    def __repr__(self):
        return f"<ComplianceBreach(type='{self.breach_type}', severity='{self.severity.value}', resolved={self.resolved})>"
```

### Task 7.0.6: Link `Portfolio` to `Client`

```python
# Modify existing Portfolio class:

class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    # ... existing fields ...
    
    # NEW: Link to client (Phase 7.0)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    # NULL = standalone portfolio (backward compatible)
    
    # NEW: Relationship
    client = relationship('Client', back_populates='portfolios')
```

**Migration SQL:**
```sql
ALTER TABLE portfolios ADD COLUMN client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL;
CREATE INDEX ix_portfolio_client ON portfolios(client_id);
```

### Task 7.0.7: Add Document Field to DecisionLog

```python
# Modify existing DecisionLog class:

class DecisionLog(Base):
    # ... existing fields ...
    
    # NEW: Compliance context (Phase 7.0)
    compliance_status = Column(String(20), nullable=True)
    # "compliant", "non_compliant", "warning"
    
    compliance_breaches = Column(JSON, nullable=True)
    # Snapshot of breaches at decision time
    # [{"type": "esg", "severity": "critical", "ticker": "BTI", ...}]
    
    document_citations = Column(JSON, nullable=True)
    # Already exists in PMDecisionSummary - ensure DB has it too
```

### Deliverable: Migration Script

Create `migrations/007_compliance_schema.py`:

```python
"""
Phase 7.0: Compliance Schema Migration

Creates tables for:
- clients
- client_ips
- esg_exclusions
- compliance_breaches

Modifies:
- assets (adds isin, asset_subclass, is_esg_excluded)
- portfolios (adds client_id)
- decision_logs (adds compliance_status, compliance_breaches)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# ... full migration script ...
```

---

## 6. Phase 7.1: IPS Constraint System

**Goal:** Structured representation of investment policy constraints  
**Duration:** 2-3 days  
**Dependencies:** Phase 7.0  

### Task 7.1.1: Define Pydantic Schemas

Create `src/agents/compliance_schemas.py`:

```python
"""
Compliance Layer Schemas for IPS Constraint Enforcement.

Phase: 7.1 - IPS Constraint System

PURPOSE:
These schemas define the contract for compliance checking.
They validate IPS constraints and breach reports.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator


class ConstraintType(str, Enum):
    """Types of IPS constraints."""
    ALLOCATION = "allocation"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"
    SECTOR = "sector"
    DURATION = "duration"
    CREDIT = "credit"
    ESG = "esg"
    GEOGRAPHY = "geography"
    CURRENCY = "currency"


class BreachSeverity(str, Enum):
    """Severity classification for breaches."""
    CRITICAL = "critical"   # 🔴 Immediate action
    HIGH = "high"           # 🟠 24-48h action
    MEDIUM = "medium"       # 🟡 Next rebalance
    LOW = "low"             # ℹ️ Informational


class ComplianceStatus(str, Enum):
    """Overall compliance status."""
    COMPLIANT = "compliant"
    WARNING = "warning"           # Within tolerance but near limit
    NON_COMPLIANT = "non_compliant"


class IPSConstraint(BaseModel):
    """
    A single IPS constraint.
    
    Example:
        IPSConstraint(
            type=ConstraintType.ALLOCATION,
            name="Equity Allocation Limit",
            asset_class="equity",
            max_weight=0.65,
            tolerance=0.05,
            breach_severity=BreachSeverity.HIGH
        )
    """
    type: ConstraintType
    name: str
    
    # What this constraint applies to
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    ticker: Optional[str] = None      # For single-issuer rules
    
    # Numeric bounds
    min_weight: Optional[float] = Field(None, ge=0, le=1)
    max_weight: Optional[float] = Field(None, ge=0, le=1)
    target_weight: Optional[float] = Field(None, ge=0, le=1)
    tolerance: float = Field(0.05, ge=0, le=0.5)
    
    # Exemptions
    exemptions: List[str] = Field(default_factory=list)
    # e.g., ["asset_subclass:government_bond", "ticker:BIL"]
    
    # Severity when breached
    breach_severity: BreachSeverity = BreachSeverity.HIGH
    
    # Complex rules (JSON)
    rule: Optional[Dict[str, Any]] = None
    
    @field_validator('max_weight', mode='after')
    @classmethod
    def max_ge_min(cls, v, info):
        """Ensure max >= min if both specified."""
        min_w = info.data.get('min_weight')
        if v is not None and min_w is not None and v < min_w:
            raise ValueError('max_weight must be >= min_weight')
        return v


class ComplianceCheck(BaseModel):
    """
    Result of checking ONE constraint.
    
    Example:
        ComplianceCheck(
            constraint_name="Single Issuer Limit",
            constraint_type=ConstraintType.CONCENTRATION,
            status="breach",
            severity=BreachSeverity.HIGH,
            current_value=0.062,
            limit_value=0.05,
            ticker="NVDA",
            message="NVDA at 6.2% exceeds 5.0% limit",
            action="TRIM by 1.2%"
        )
    """
    constraint_name: str
    constraint_type: ConstraintType
    
    status: Literal["pass", "warning", "breach"]
    severity: Optional[BreachSeverity] = None  # Only if breach/warning
    
    current_value: float
    limit_value: float
    
    # What's affected
    ticker: Optional[str] = None
    isin: Optional[str] = None
    asset_class: Optional[str] = None
    
    # Human-readable
    message: str
    action: Optional[str] = None  # Recommended remediation


class ComplianceReport(BaseModel):
    """
    Full compliance report for a portfolio.
    
    This is the OUTPUT of the Compliance Agent.
    """
    # Header
    portfolio_id: int
    portfolio_name: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    
    # Timing
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    compliance_run_id: str
    
    # Overall status
    status: ComplianceStatus
    
    # Summary metrics
    total_aum: float
    num_positions: int
    
    # Detailed checks (all of them)
    checks: List[ComplianceCheck] = Field(default_factory=list)
    
    # Just the breaches (filtered)
    @property
    def breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "breach"]
    
    @property
    def warnings(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "warning"]
    
    @property
    def critical_breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.breaches if c.severity == BreachSeverity.CRITICAL]
    
    # Asset allocation snapshot
    allocation: Dict[str, float] = Field(default_factory=dict)
    # {"equity": 0.70, "fixed_income": 0.28, "cash": 0.02}
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    
    def format_summary(self) -> str:
        """Format for human-readable output."""
        emoji = {"compliant": "✅", "warning": "⚠️", "non_compliant": "🔴"}
        return f"""
═══════════════════════════════════════════════════════════════
                     COMPLIANCE REPORT
═══════════════════════════════════════════════════════════════
Portfolio: {self.portfolio_name} (ID: {self.portfolio_id})
Client: {self.client_name or 'N/A'} ({self.client_id or 'N/A'})
Date: {self.as_of_date.strftime('%Y-%m-%d %H:%M')}
Status: {emoji.get(self.status.value, '')} {self.status.value.upper()}

Total AUM: ${self.total_aum:,.2f}
Positions: {self.num_positions}
Breaches: {len(self.breaches)} ({len(self.critical_breaches)} critical)
Warnings: {len(self.warnings)}

Run ID: {self.compliance_run_id}
═══════════════════════════════════════════════════════════════
"""
```

### Task 7.1.2: Create IPSManager Class

Create `src/portfolio_tool/ips_manager.py`:

```python
"""
IPS Manager - CRUD operations for client IPS constraints.

Phase: 7.1 - IPS Constraint System

PATTERN:
- Follows PortfolioManager pattern (strict CRUD, no business logic)
- Uses existing session management
- All writes are idempotent (upsert)
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from .database_setup import Client, ClientIPS, IPSConstraintType, get_session
from ..agents.compliance_schemas import IPSConstraint, ConstraintType


class IPSManager:
    """
    Manages IPS constraint CRUD operations.
    
    Usage:
        manager = IPSManager()
        
        # Create client
        client_id = manager.create_client("8821-X", "Anders Family Trust", "trust")
        
        # Add constraints
        manager.add_constraint(
            client_db_id=client_id,
            constraint=IPSConstraint(
                type=ConstraintType.ALLOCATION,
                name="Max Equity",
                asset_class="equity",
                max_weight=0.65,
                tolerance=0.05
            )
        )
        
        # Load all constraints for a client
        constraints = manager.get_client_constraints(client_db_id=client_id)
    """
    
    def __init__(self, session: Optional[Session] = None):
        self._session = session
    
    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session
    
    # ─────────────────────────────────────────────────────────────
    # CLIENT OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def create_client(
        self,
        client_id: str,
        name: str,
        client_type: str,
        risk_profile: str = "moderate",
        **kwargs
    ) -> int:
        """Create a new client. Returns database ID."""
        client = Client(
            client_id=client_id,
            name=name,
            client_type=client_type,
            risk_profile=risk_profile,
            **kwargs
        )
        self.session.add(client)
        self.session.commit()
        return client.id
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by external ID."""
        return self.session.query(Client).filter(
            Client.client_id == client_id
        ).first()
    
    def get_client_by_portfolio(self, portfolio_id: int) -> Optional[Client]:
        """Get client associated with a portfolio."""
        from .database_setup import Portfolio
        portfolio = self.session.query(Portfolio).get(portfolio_id)
        if portfolio and portfolio.client_id:
            return self.session.query(Client).get(portfolio.client_id)
        return None
    
    # ─────────────────────────────────────────────────────────────
    # CONSTRAINT OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def add_constraint(
        self,
        client_db_id: int,
        constraint: IPSConstraint,
        effective_date: Optional[date] = None,
        source_document: Optional[str] = None
    ) -> int:
        """Add an IPS constraint for a client."""
        db_constraint = ClientIPS(
            client_id=client_db_id,
            constraint_type=IPSConstraintType[constraint.type.value.upper()],
            constraint_name=constraint.name,
            asset_class=constraint.asset_class,
            sector=constraint.sector,
            min_weight=constraint.min_weight,
            max_weight=constraint.max_weight,
            target_weight=constraint.target_weight,
            tolerance=constraint.tolerance,
            exemptions=constraint.exemptions,
            breach_severity=constraint.breach_severity.value,
            effective_date=effective_date or date.today(),
            source_document=source_document,
            is_active=True
        )
        self.session.add(db_constraint)
        self.session.commit()
        return db_constraint.id
    
    def get_client_constraints(
        self,
        client_db_id: int,
        constraint_type: Optional[ConstraintType] = None,
        active_only: bool = True
    ) -> List[IPSConstraint]:
        """Get all IPS constraints for a client."""
        query = self.session.query(ClientIPS).filter(
            ClientIPS.client_id == client_db_id
        )
        
        if active_only:
            query = query.filter(ClientIPS.is_active == True)
        
        if constraint_type:
            query = query.filter(
                ClientIPS.constraint_type == IPSConstraintType[constraint_type.value.upper()]
            )
        
        constraints = []
        for db_row in query.all():
            constraints.append(IPSConstraint(
                type=ConstraintType(db_row.constraint_type.value.lower()),
                name=db_row.constraint_name,
                asset_class=db_row.asset_class,
                sector=db_row.sector,
                min_weight=db_row.min_weight,
                max_weight=db_row.max_weight,
                target_weight=db_row.target_weight,
                tolerance=db_row.tolerance or 0.05,
                exemptions=db_row.exemptions or [],
                breach_severity=BreachSeverity(db_row.breach_severity)
            ))
        
        return constraints
    
    def deactivate_constraint(self, constraint_id: int) -> bool:
        """Soft-delete a constraint."""
        constraint = self.session.query(ClientIPS).get(constraint_id)
        if constraint:
            constraint.is_active = False
            self.session.commit()
            return True
        return False
    
    # ─────────────────────────────────────────────────────────────
    # BULK OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def load_default_constraints(self, client_db_id: int, profile: str = "moderate"):
        """
        Load standard constraint templates based on risk profile.
        
        Profiles:
        - conservative: 40% max equity, 10% min cash
        - moderate: 65% max equity, 5% min cash
        - aggressive: 80% max equity, 2% min cash
        """
        templates = {
            "conservative": [
                IPSConstraint(type=ConstraintType.ALLOCATION, name="Max Equity", 
                             asset_class="equity", max_weight=0.40, tolerance=0.05),
                IPSConstraint(type=ConstraintType.LIQUIDITY, name="Min Cash",
                             asset_class="cash", min_weight=0.10, tolerance=0.02),
                IPSConstraint(type=ConstraintType.CONCENTRATION, name="Single Issuer",
                             max_weight=0.05, exemptions=["asset_subclass:government_bond"]),
            ],
            "moderate": [
                IPSConstraint(type=ConstraintType.ALLOCATION, name="Max Equity",
                             asset_class="equity", max_weight=0.65, tolerance=0.05),
                IPSConstraint(type=ConstraintType.LIQUIDITY, name="Min Cash",
                             asset_class="cash", min_weight=0.05, tolerance=0.02),
                IPSConstraint(type=ConstraintType.CONCENTRATION, name="Single Issuer",
                             max_weight=0.05, exemptions=["asset_subclass:government_bond"]),
            ],
            "aggressive": [
                IPSConstraint(type=ConstraintType.ALLOCATION, name="Max Equity",
                             asset_class="equity", max_weight=0.80, tolerance=0.05),
                IPSConstraint(type=ConstraintType.LIQUIDITY, name="Min Cash",
                             asset_class="cash", min_weight=0.02, tolerance=0.01),
                IPSConstraint(type=ConstraintType.CONCENTRATION, name="Single Issuer",
                             max_weight=0.08, exemptions=["asset_subclass:government_bond"]),
            ],
        }
        
        for constraint in templates.get(profile, templates["moderate"]):
            self.add_constraint(client_db_id, constraint)
```

### Task 7.1.3-7.1.6: Tests and CLI

(Detailed test cases and CLI commands...)

---

## 7. Phase 7.2: ESG Screening Module

**Goal:** Negative screening against exclusion lists  
**Duration:** 1-2 days  
**Dependencies:** Phase 7.0  

### Task 7.2.1: Seed ESG Exclusions

Create `scripts/seed_esg_exclusions.py`:

```python
"""
Seed ESG exclusion data.

This provides a realistic set of excluded securities for demo purposes.
In production, this would come from MSCI, Sustainalytics, etc.
"""

ESG_EXCLUSIONS = [
    # TOBACCO
    {"isin": "GB0002875804", "ticker": "BTI", "company_name": "British American Tobacco",
     "category": "tobacco", "reason": "Tobacco manufacturer", "source": "demo"},
    {"isin": "US7181721090", "ticker": "PM", "company_name": "Philip Morris International",
     "category": "tobacco", "reason": "Tobacco manufacturer", "source": "demo"},
    {"isin": "US0298991011", "ticker": "MO", "company_name": "Altria Group",
     "category": "tobacco", "reason": "Tobacco manufacturer", "source": "demo"},
    
    # THERMAL COAL
    {"isin": "US6708371033", "ticker": "BTU", "company_name": "Peabody Energy",
     "category": "thermal_coal", "reason": "Thermal coal mining >30% revenue", "source": "demo"},
    {"isin": "US12626K2033", "ticker": "CNX", "company_name": "CNX Resources",
     "category": "thermal_coal", "reason": "Coal production", "source": "demo"},
    
    # CONTROVERSIAL WEAPONS
    {"isin": "US5398301094", "ticker": "LMT", "company_name": "Lockheed Martin",
     "category": "controversial_weapons", "reason": "Nuclear weapons systems", "source": "demo"},
    {"isin": "US6974351057", "ticker": "RTX", "company_name": "RTX Corporation",
     "category": "controversial_weapons", "reason": "Cluster munitions components", "source": "demo"},
    
    # GAMBLING
    {"isin": "US5178341070", "ticker": "LVS", "company_name": "Las Vegas Sands",
     "category": "gambling", "reason": "Casino operator", "source": "demo"},
    
    # PRIVATE PRISONS
    {"isin": "US22025Y4070", "ticker": "CXW", "company_name": "CoreCivic",
     "category": "private_prisons", "reason": "Private prison operator", "source": "demo"},
]
```

### Task 7.2.2: Create ESGScreener Class

Create `src/portfolio_tool/esg_screener.py`:

```python
"""
ESG Screener - Checks holdings against exclusion lists.

Phase: 7.2 - ESG Screening Module
"""

from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session

from .database_setup import (
    ESGExclusion, ESGCategory, PortfolioHolding, Asset, get_session
)
from ..agents.compliance_schemas import ComplianceCheck, ConstraintType, BreachSeverity


class ESGScreener:
    """
    Screens portfolio holdings against ESG exclusion list.
    
    Usage:
        screener = ESGScreener()
        breaches = screener.check_holdings(portfolio_id=1)
        
        # Check specific categories
        breaches = screener.check_holdings(
            portfolio_id=1,
            categories=[ESGCategory.TOBACCO, ESGCategory.COAL]
        )
    """
    
    def __init__(self, session: Optional[Session] = None):
        self._session = session
    
    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session
    
    def get_exclusion_set(
        self,
        categories: Optional[List[ESGCategory]] = None
    ) -> Dict[str, Dict]:
        """
        Get the current exclusion set.
        
        Returns dict keyed by ISIN and ticker for fast lookup.
        """
        query = self.session.query(ESGExclusion).filter(
            ESGExclusion.is_active == True
        )
        
        if categories:
            query = query.filter(ESGExclusion.category.in_(categories))
        
        exclusions = {}
        for exc in query.all():
            key_data = {
                "company_name": exc.company_name,
                "category": exc.category.value,
                "reason": exc.reason,
                "source": exc.source
            }
            if exc.isin:
                exclusions[f"isin:{exc.isin}"] = key_data
            if exc.ticker:
                exclusions[f"ticker:{exc.ticker}"] = key_data
        
        return exclusions
    
    def check_holdings(
        self,
        portfolio_id: int,
        categories: Optional[List[ESGCategory]] = None
    ) -> List[ComplianceCheck]:
        """
        Check all holdings in a portfolio against ESG exclusions.
        
        Returns list of ComplianceCheck for any breaches found.
        """
        exclusions = self.get_exclusion_set(categories)
        
        # Get holdings with asset details
        holdings = (
            self.session.query(PortfolioHolding, Asset)
            .join(Asset, PortfolioHolding.asset_id == Asset.id)
            .filter(PortfolioHolding.portfolio_id == portfolio_id)
            .all()
        )
        
        # Calculate total portfolio value for weight calculation
        total_value = sum(
            h.quantity * (h.average_price or 0) for h, a in holdings
        )
        
        breaches = []
        for holding, asset in holdings:
            # Check by ISIN
            isin_key = f"isin:{asset.isin}" if asset.isin else None
            ticker_key = f"ticker:{asset.ticker}"
            
            exclusion = None
            if isin_key and isin_key in exclusions:
                exclusion = exclusions[isin_key]
            elif ticker_key in exclusions:
                exclusion = exclusions[ticker_key]
            
            if exclusion:
                position_value = holding.quantity * (holding.average_price or 0)
                weight = position_value / total_value if total_value > 0 else 0
                
                breaches.append(ComplianceCheck(
                    constraint_name=f"ESG: No {exclusion['category'].replace('_', ' ').title()}",
                    constraint_type=ConstraintType.ESG,
                    status="breach",
                    severity=BreachSeverity.CRITICAL,  # ESG breaches are always critical
                    current_value=weight,
                    limit_value=0.0,  # Zero tolerance
                    ticker=asset.ticker,
                    isin=asset.isin,
                    message=f"{asset.ticker} ({exclusion['company_name']}) violates ESG policy: {exclusion['reason']}",
                    action=f"SELL IMMEDIATE: Liquidate entire {asset.ticker} position (~${position_value:,.0f})"
                ))
        
        return breaches
    
    def check_single_security(
        self,
        ticker: Optional[str] = None,
        isin: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Check if a single security is on the exclusion list.
        
        Useful for pre-trade compliance checks.
        """
        query = self.session.query(ESGExclusion).filter(
            ESGExclusion.is_active == True
        )
        
        if isin:
            result = query.filter(ESGExclusion.isin == isin).first()
            if result:
                return {
                    "excluded": True,
                    "category": result.category.value,
                    "reason": result.reason
                }
        
        if ticker:
            result = query.filter(ESGExclusion.ticker == ticker).first()
            if result:
                return {
                    "excluded": True,
                    "category": result.category.value,
                    "reason": result.reason
                }
        
        return {"excluded": False}
```

---

## 8. Phase 7.3: Compliance Agent

**Goal:** The core agent that orchestrates all compliance checks  
**Duration:** 3-4 days  
**Dependencies:** Phase 7.1, 7.2  

### Task 7.3.1: Create ComplianceAgent

Create `src/agents/compliance_agent.py`:

```python
"""
Compliance Agent - Orchestrates IPS compliance checking.

Phase: 7.3 - Compliance Agent

PATTERN:
- Follows existing agent patterns (DataAgent, MacroAgent)
- Pure orchestration - no LLM calls for calculations
- Deterministic rule checking

RESPONSIBILITIES:
1. Load client IPS constraints
2. Check allocation limits
3. Check concentration limits  
4. Run ESG screening
5. Classify breach severity
6. Generate ComplianceReport
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import uuid4

from .compliance_schemas import (
    IPSConstraint, ConstraintType, BreachSeverity,
    ComplianceCheck, ComplianceReport, ComplianceStatus
)
from ..portfolio_tool.ips_manager import IPSManager
from ..portfolio_tool.esg_screener import ESGScreener
from ..portfolio_tool.portfolio_manager import PortfolioManager
from ..config import config


class ComplianceAgent:
    """
    Orchestrates compliance checking for a portfolio.
    
    Usage:
        agent = ComplianceAgent()
        report = agent.run_compliance_check(portfolio_id=1)
        
        # With specific client
        report = agent.run_compliance_check(
            portfolio_id=1,
            client_id="8821-X"
        )
    """
    
    def __init__(self):
        self.ips_manager = IPSManager()
        self.esg_screener = ESGScreener()
        self.portfolio_manager = PortfolioManager()
    
    def run_compliance_check(
        self,
        portfolio_id: int,
        client_id: Optional[str] = None,
        include_esg: bool = True,
        constraints_override: Optional[List[IPSConstraint]] = None
    ) -> ComplianceReport:
        """
        Run full compliance check on a portfolio.
        
        Args:
            portfolio_id: Portfolio to check
            client_id: Client ID (if not linked to portfolio)
            include_esg: Whether to run ESG screening
            constraints_override: Use these constraints instead of DB
        
        Returns:
            ComplianceReport with all checks and breaches
        """
        run_id = f"COMP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"
        
        # 1. Load portfolio data
        portfolio = self.portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        holdings = self.portfolio_manager.get_holdings(portfolio_id)
        if not holdings:
            raise ValueError(f"Portfolio {portfolio_id} has no holdings")
        
        # 2. Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(holdings)
        
        # 3. Load constraints
        if constraints_override:
            constraints = constraints_override
        else:
            constraints = self._load_constraints(portfolio_id, client_id)
        
        # 4. Run all checks
        all_checks = []
        
        # 4a. Allocation checks
        allocation_checks = self._check_allocation_constraints(
            constraints, portfolio_metrics
        )
        all_checks.extend(allocation_checks)
        
        # 4b. Concentration checks
        concentration_checks = self._check_concentration_constraints(
            constraints, holdings, portfolio_metrics
        )
        all_checks.extend(concentration_checks)
        
        # 4c. Liquidity checks
        liquidity_checks = self._check_liquidity_constraints(
            constraints, portfolio_metrics
        )
        all_checks.extend(liquidity_checks)
        
        # 4d. ESG screening
        if include_esg:
            esg_checks = self.esg_screener.check_holdings(portfolio_id)
            all_checks.extend(esg_checks)
        
        # 5. Determine overall status
        status = self._determine_status(all_checks)
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(all_checks)
        
        # 7. Build report
        client = self.ips_manager.get_client(client_id) if client_id else \
                 self.ips_manager.get_client_by_portfolio(portfolio_id)
        
        return ComplianceReport(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.get("name", f"Portfolio {portfolio_id}"),
            client_id=client.client_id if client else None,
            client_name=client.name if client else None,
            as_of_date=datetime.utcnow(),
            compliance_run_id=run_id,
            status=status,
            total_aum=portfolio_metrics["total_value"],
            num_positions=portfolio_metrics["num_positions"],
            checks=all_checks,
            allocation=portfolio_metrics["allocation"],
            recommendations=recommendations
        )
    
    def _calculate_portfolio_metrics(
        self, 
        holdings: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate portfolio-level metrics from holdings."""
        total_value = 0.0
        allocation = {"equity": 0.0, "fixed_income": 0.0, "cash": 0.0, "other": 0.0}
        weights = {}
        
        for h in holdings:
            value = h["quantity"] * h.get("current_price", h.get("average_price", 0))
            total_value += value
            
            # Track by ticker
            weights[h["ticker"]] = {"value": value, "asset_class": h.get("asset_class")}
            
            # Aggregate by asset class
            asset_class = (h.get("asset_class") or "other").lower()
            if "equity" in asset_class or "stock" in asset_class:
                allocation["equity"] += value
            elif "bond" in asset_class or "fixed" in asset_class:
                allocation["fixed_income"] += value
            elif "cash" in asset_class or "money" in asset_class:
                allocation["cash"] += value
            else:
                allocation["other"] += value
        
        # Convert to percentages
        if total_value > 0:
            for ticker, data in weights.items():
                data["weight"] = data["value"] / total_value
            for k in allocation:
                allocation[k] = allocation[k] / total_value
        
        return {
            "total_value": total_value,
            "num_positions": len(holdings),
            "weights": weights,
            "allocation": allocation,
            "max_position_weight": max((d["weight"] for d in weights.values()), default=0)
        }
    
    def _load_constraints(
        self,
        portfolio_id: int,
        client_id: Optional[str]
    ) -> List[IPSConstraint]:
        """Load IPS constraints for portfolio's client."""
        client = None
        
        if client_id:
            client = self.ips_manager.get_client(client_id)
        else:
            client = self.ips_manager.get_client_by_portfolio(portfolio_id)
        
        if client:
            return self.ips_manager.get_client_constraints(client.id)
        
        # No client - return default constraints
        return self._get_default_constraints()
    
    def _get_default_constraints(self) -> List[IPSConstraint]:
        """Return sensible default constraints when no IPS exists."""
        return [
            IPSConstraint(
                type=ConstraintType.ALLOCATION,
                name="Default Max Equity",
                asset_class="equity",
                max_weight=0.80,
                tolerance=0.05,
                breach_severity=BreachSeverity.MEDIUM
            ),
            IPSConstraint(
                type=ConstraintType.CONCENTRATION,
                name="Default Single Issuer",
                max_weight=0.10,
                tolerance=0.02,
                breach_severity=BreachSeverity.HIGH
            ),
            IPSConstraint(
                type=ConstraintType.LIQUIDITY,
                name="Default Min Cash",
                asset_class="cash",
                min_weight=0.02,
                tolerance=0.01,
                breach_severity=BreachSeverity.MEDIUM
            ),
        ]
    
    def _check_allocation_constraints(
        self,
        constraints: List[IPSConstraint],
        metrics: Dict
    ) -> List[ComplianceCheck]:
        """Check asset allocation constraints."""
        checks = []
        allocation = metrics["allocation"]
        
        for c in constraints:
            if c.type != ConstraintType.ALLOCATION:
                continue
            
            asset_class = c.asset_class.lower() if c.asset_class else None
            if not asset_class or asset_class not in allocation:
                continue
            
            current = allocation[asset_class]
            
            # Check max
            if c.max_weight is not None:
                if current > c.max_weight + c.tolerance:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="breach",
                        severity=c.breach_severity,
                        current_value=current,
                        limit_value=c.max_weight,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current:.1%} exceeds {c.max_weight:.1%} max",
                        action=f"Reduce {asset_class} allocation by {(current - c.max_weight):.1%}"
                    ))
                elif current > c.max_weight:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="warning",
                        severity=BreachSeverity.LOW,
                        current_value=current,
                        limit_value=c.max_weight,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current:.1%} near {c.max_weight:.1%} limit",
                        action=None
                    ))
                else:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="pass",
                        current_value=current,
                        limit_value=c.max_weight,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current:.1%} within {c.max_weight:.1%} limit"
                    ))
            
            # Check min
            if c.min_weight is not None:
                if current < c.min_weight - c.tolerance:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="breach",
                        severity=c.breach_severity,
                        current_value=current,
                        limit_value=c.min_weight,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current:.1%} below {c.min_weight:.1%} min",
                        action=f"Increase {asset_class} allocation by {(c.min_weight - current):.1%}"
                    ))
        
        return checks
    
    def _check_concentration_constraints(
        self,
        constraints: List[IPSConstraint],
        holdings: List[Dict],
        metrics: Dict
    ) -> List[ComplianceCheck]:
        """Check single-issuer concentration constraints."""
        checks = []
        weights = metrics["weights"]
        
        for c in constraints:
            if c.type != ConstraintType.CONCENTRATION:
                continue
            
            max_weight = c.max_weight or 0.05
            exemptions = set(c.exemptions or [])
            
            for ticker, data in weights.items():
                # Check exemptions
                if self._is_exempt(ticker, data, exemptions):
                    continue
                
                weight = data["weight"]
                
                if weight > max_weight + c.tolerance:
                    holding = next((h for h in holdings if h["ticker"] == ticker), {})
                    value = data["value"]
                    excess = weight - max_weight
                    
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.CONCENTRATION,
                        status="breach",
                        severity=c.breach_severity,
                        current_value=weight,
                        limit_value=max_weight,
                        ticker=ticker,
                        message=f"{ticker} at {weight:.1%} exceeds {max_weight:.1%} single-issuer limit",
                        action=f"TRIM {ticker} by {excess:.1%} (~${value * excess / weight:,.0f})"
                    ))
                elif weight > max_weight:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.CONCENTRATION,
                        status="warning",
                        severity=BreachSeverity.LOW,
                        current_value=weight,
                        limit_value=max_weight,
                        ticker=ticker,
                        message=f"{ticker} at {weight:.1%} near {max_weight:.1%} limit"
                    ))
        
        return checks
    
    def _is_exempt(
        self,
        ticker: str,
        data: Dict,
        exemptions: set
    ) -> bool:
        """Check if a position is exempt from a constraint."""
        for exemption in exemptions:
            if exemption.startswith("ticker:"):
                if ticker == exemption.split(":")[1]:
                    return True
            elif exemption.startswith("asset_subclass:"):
                subclass = exemption.split(":")[1]
                if data.get("asset_subclass") == subclass:
                    return True
            elif exemption.startswith("asset_class:"):
                asset_class = exemption.split(":")[1]
                if data.get("asset_class", "").lower() == asset_class.lower():
                    return True
        return False
    
    def _check_liquidity_constraints(
        self,
        constraints: List[IPSConstraint],
        metrics: Dict
    ) -> List[ComplianceCheck]:
        """Check liquidity (cash) constraints."""
        checks = []
        cash_pct = metrics["allocation"].get("cash", 0)
        
        for c in constraints:
            if c.type != ConstraintType.LIQUIDITY:
                continue
            
            if c.min_weight is not None:
                if cash_pct < c.min_weight - c.tolerance:
                    checks.append(ComplianceCheck(
                        constraint_name=c.name,
                        constraint_type=ConstraintType.LIQUIDITY,
                        status="breach",
                        severity=c.breach_severity,
                        current_value=cash_pct,
                        limit_value=c.min_weight,
                        asset_class="cash",
                        message=f"Cash at {cash_pct:.1%} below {c.min_weight:.1%} minimum",
                        action=f"Raise cash by {(c.min_weight - cash_pct):.1%}"
                    ))
        
        return checks
    
    def _determine_status(self, checks: List[ComplianceCheck]) -> ComplianceStatus:
        """Determine overall compliance status from checks."""
        breaches = [c for c in checks if c.status == "breach"]
        warnings = [c for c in checks if c.status == "warning"]
        
        if any(c.severity == BreachSeverity.CRITICAL for c in breaches):
            return ComplianceStatus.NON_COMPLIANT
        if len(breaches) >= 2:
            return ComplianceStatus.NON_COMPLIANT
        if breaches:
            return ComplianceStatus.NON_COMPLIANT
        if warnings:
            return ComplianceStatus.WARNING
        return ComplianceStatus.COMPLIANT
    
    def _generate_recommendations(
        self, 
        checks: List[ComplianceCheck]
    ) -> List[str]:
        """Generate prioritized recommendations from breaches."""
        recommendations = []
        
        # Sort breaches by severity
        breaches = sorted(
            [c for c in checks if c.status == "breach"],
            key=lambda x: ["critical", "high", "medium", "low"].index(
                x.severity.value if x.severity else "low"
            )
        )
        
        for i, breach in enumerate(breaches[:5], 1):  # Top 5
            if breach.action:
                recommendations.append(f"{i}. {breach.action}")
        
        return recommendations
```

---

## 9. Phase 7.4: Router & Graph Integration

**Goal:** Wire Compliance Agent into existing LangGraph  
**Duration:** 1-2 days  
**Dependencies:** Phase 7.3  

### Task 7.4.1: Add ExecutionIntent

In `src/agents/schemas.py`:

```python
class ExecutionIntent(str, Enum):
    # ... existing intents ...
    
    COMPLIANCE_CHECK = "compliance_check"  # NEW: DataAgent → ComplianceAgent
```

### Task 7.4.2: Add AgentName

```python
class AgentName(str, Enum):
    # ... existing agents ...
    
    COMPLIANCE_AGENT = "ComplianceAgent"  # NEW
```

### Task 7.4.3: Add Routing Examples

In `src/agents/router_prompts.py`:

```python
COMPLIANCE_EXAMPLES = """
User: "Check IPS compliance for Client 8821-X"
→ query_intent: decision
→ execution_intent: compliance_check
→ agents: [DataAgent, ComplianceAgent]

User: "Run compliance check on my portfolio"
→ query_intent: decision
→ execution_intent: compliance_check
→ agents: [DataAgent, ComplianceAgent]

User: "Are there any IPS breaches?"
→ query_intent: information
→ execution_intent: compliance_check
→ agents: [DataAgent, ComplianceAgent]

User: "Check ESG violations in portfolio 1"
→ query_intent: decision
→ execution_intent: compliance_check
→ agents: [DataAgent, ComplianceAgent]
"""
```

### Task 7.4.4: Create compliance_node

In `src/agents/nodes.py`:

```python
async def compliance_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Compliance Agent node - runs IPS compliance checks.
    
    Requires: DataAgent (holdings data)
    Produces: ComplianceReport in sub_results["ComplianceAgent"]
    """
    from .compliance_agent import ComplianceAgent
    
    portfolio_id = state.get("portfolio_id")
    if not portfolio_id:
        return add_error(state, "No portfolio specified for compliance check")
    
    # Get client_id from router parameters if provided
    router_decision = state.get("router_decision", {})
    params = router_decision.get("parameters", {})
    client_id = params.get("client_id")
    
    try:
        agent = ComplianceAgent()
        report = agent.run_compliance_check(
            portfolio_id=portfolio_id,
            client_id=client_id
        )
        
        result = {
            "success": True,
            "status": report.status.value,
            "breaches": len(report.breaches),
            "critical_breaches": len(report.critical_breaches),
            "recommendations": report.recommendations,
            "report": report.model_dump(),
            "summary": report.format_summary()
        }
        
        return {
            **mark_agent_complete(state, "ComplianceAgent", result),
            **add_shared_data(state, "compliance_report", report.model_dump())
        }
        
    except Exception as e:
        return add_error(state, f"Compliance check failed: {str(e)}")
```

### Task 7.4.5: Wire into graph

In `src/agents/graph.py`:

```python
from .nodes import compliance_agent_node

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # ... existing nodes ...
    
    graph.add_node("ComplianceAgent", compliance_agent_node)  # NEW
    
    # ... edges ...
```

---

## 10-13: Remaining Phases

(Phases 7.5-7.8 follow similar detailed patterns for Decision Engine Integration, IPS Document Extraction, Compliance Reporting, and Hardening...)

---

## 14. Test Strategy

### Test Files to Create

| File | Tests | Focus |
|------|-------|-------|
| `test_compliance_schemas.py` | 15 | Pydantic validation |
| `test_ips_manager.py` | 20 | CRUD operations |
| `test_esg_screener.py` | 15 | ESG screening logic |
| `test_compliance_agent.py` | 30 | Full compliance checks |
| `test_compliance_integration.py` | 20 | End-to-end flows |

**Target: 100+ new tests**

---

## 15. Interview Demo Prompts

### The "Golden Prompt"

```
Check IPS compliance for Client Account #8821-X (The Anders Family Trust).
Flag any breaches immediately.
```

### Additional WOW Prompts

```
1. "My portfolio holds British American Tobacco. Is that allowed under our ESG policy?"

2. "What's our current equity exposure vs. the IPS limit?"

3. "Run a pre-trade compliance check: Can I buy 1000 shares of NVDA?"

4. "Generate a compliance memo for the Q4 board meeting."

5. "Which positions are closest to their concentration limits?"
```

---

## 16. File Manifest

### New Files (Phase 7)

```
src/
├── agents/
│   ├── compliance_agent.py          # 7.3 - Core agent
│   └── compliance_schemas.py        # 7.1 - Pydantic schemas
│
├── portfolio_tool/
│   ├── ips_manager.py               # 7.1 - IPS CRUD
│   ├── esg_screener.py              # 7.2 - ESG screening
│   └── compliance_tools.py          # 7.4 - Tool wrappers
│
migrations/
└── 007_compliance_schema.py         # 7.0 - Schema migration

scripts/
├── seed_esg_exclusions.py           # 7.2 - ESG data
└── seed_sample_clients.py           # 7.1 - Demo clients

tests/
├── test_compliance_schemas.py
├── test_ips_manager.py
├── test_esg_screener.py
├── test_compliance_agent.py
└── test_compliance_integration.py
```

### Modified Files

```
src/
├── agents/
│   ├── schemas.py                   # Add COMPLIANCE_CHECK intent
│   ├── nodes.py                     # Add compliance_agent_node
│   ├── graph.py                     # Wire compliance node
│   ├── router_prompts.py            # Add compliance examples
│   ├── decision_engine.py           # Integrate compliance
│   └── decision_schemas.py          # Add compliance fields
│
├── portfolio_tool/
│   └── database_setup.py            # New tables + modifications
│
└── config.py                        # Add ComplianceConfig
```

---

## ✅ Ready to Start

**Phase 7.0 can begin immediately.**

Upload request: To start Phase 7.0.1, I need to confirm the exact location and import paths. Please confirm:

1. Is `database_setup.py` at `src/portfolio_tool/database_setup.py`?
2. Do you use Alembic for migrations, or raw SQL scripts?
3. Should I create a separate `compliance_schemas.py` or add to existing `decision_schemas.py`?

Once confirmed, I'll generate the complete migration and model code for Task 7.0.1-7.0.7.