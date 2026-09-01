# 🚀 Phase 7.0 Implementation Guide
## Compliance Schema Foundation - Step-by-Step

**Time Estimate:** 2-4 hours  
**Difficulty:** Medium  
**Prerequisites:** Working database, existing codebase  

---

## 📋 Table of Contents

1. [Quick Start (TL;DR)](#1-quick-start-tldr)
2. [File Changes Overview](#2-file-changes-overview)
3. [Step 1: Update database_setup.py](#3-step-1-update-database_setuppy)
4. [Step 2: Update decision_schemas.py](#4-step-2-update-decision_schemaspy)
5. [Step 3: Update config.py](#5-step-3-update-configpy)
6. [Step 4: Update schemas.py](#6-step-4-update-schemaspy)
7. [Step 5: Run Migration / Recreate DB](#7-step-5-run-migration--recreate-db)
8. [Step 6: Seed Data](#8-step-6-seed-data)
9. [Step 7: Verify Installation](#9-step-7-verify-installation)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Quick Start (TL;DR)

```bash
# Option A: Delete and recreate DB (FASTEST - lose existing data)
rm data/portfolio.db
python -c "from src.portfolio_tool.database_setup import Base, engine; Base.metadata.create_all(engine)"
python scripts/seed_esg_exclusions.py
python scripts/seed_sample_clients.py

# Option B: Use Alembic migration (SAFE - keep existing data)
alembic upgrade head
python scripts/seed_esg_exclusions.py
python scripts/seed_sample_clients.py
```

---

## 2. File Changes Overview

| File | Changes | Lines |
|------|---------|-------|
| `src/portfolio_tool/database_setup.py` | Add 3 enums, 4 models, modify 3 models | +300 |
| `src/agents/decision_schemas.py` | Add 3 enums, 4 dataclasses | +350 |
| `src/config.py` | Add ComplianceConfig dataclass | +80 |
| `src/agents/schemas.py` | Add COMPLIANCE_CHECK intent, COMPLIANCE_AGENT name | +4 |
| `scripts/seed_esg_exclusions.py` | New file | 250 |
| `scripts/seed_sample_clients.py` | New file | 300 |
| `migrations/versions/007_compliance_schema.py` | New file (if using Alembic) | 180 |

---

## 3. Step 1: Update database_setup.py

### Location: `src/portfolio_tool/database_setup.py`

### 1.1 Add New Enums (after existing `PipelineRunStatus` enum, ~line 186)

```python
# =============================================================================
# PHASE 7.0: COMPLIANCE ENUMS
# =============================================================================

class IPSConstraintType(enum.Enum):
    """Types of IPS constraints."""
    ALLOCATION = "allocation"         # Asset class min/max
    CONCENTRATION = "concentration"   # Single issuer limit
    LIQUIDITY = "liquidity"           # Cash minimums
    SECTOR = "sector"                 # Sector limits
    DURATION = "duration"             # Bond duration limits
    CREDIT = "credit"                 # Credit quality minimums
    ESG = "esg"                       # ESG exclusions
    GEOGRAPHY = "geography"           # Country/region limits
    CURRENCY = "currency"             # Currency exposure limits


class ESGCategory(enum.Enum):
    """ESG exclusion categories."""
    TOBACCO = "tobacco"
    THERMAL_COAL = "thermal_coal"
    WEAPONS = "weapons"
    CONTROVERSIAL_WEAPONS = "controversial_weapons"
    GAMBLING = "gambling"
    ADULT_ENTERTAINMENT = "adult_entertainment"
    NUCLEAR = "nuclear"
    PALM_OIL = "palm_oil"
    PRIVATE_PRISONS = "private_prisons"
    ANIMAL_TESTING = "animal_testing"
    OTHER = "other"


class BreachSeverity(enum.Enum):
    """Severity levels for compliance breaches."""
    CRITICAL = "critical"   # 🔴 Immediate action required
    HIGH = "high"           # 🟠 Action required within 24-48h
    MEDIUM = "medium"       # 🟡 Review in next rebalance
    LOW = "low"             # ℹ️ Informational only
```

### 1.2 Add New Models (BEFORE the `Portfolio` class, ~line 400)

```python
# =============================================================================
# PHASE 7.0: COMPLIANCE MODELS
# =============================================================================

class Client(Base):
    """
    Represents an investment client (individual, trust, institution).
    Phase: 7.0 - Compliance Schema Foundation
    """
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    client_type = Column(String(50), nullable=False)
    risk_profile = Column(String(50), nullable=False, default="moderate")
    tax_status = Column(String(50), nullable=True)
    jurisdiction = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, 
                       onupdate=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    portfolios = relationship('Portfolio', back_populates='client')
    ips_constraints = relationship('ClientIPS', back_populates='client', 
                                   cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Client(client_id='{self.client_id}', name='{self.name}')>"


class ClientIPS(Base):
    """
    Investment Policy Statement constraints for a client.
    Phase: 7.0 - Compliance Schema Foundation
    """
    __tablename__ = 'client_ips'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), 
                       nullable=False, index=True)
    
    # Constraint identification
    constraint_type = Column(Enum(IPSConstraintType), nullable=False, index=True)
    constraint_name = Column(String(100), nullable=False)
    
    # Target specification
    asset_class = Column(String(50), nullable=True)
    sector = Column(String(50), nullable=True)
    
    # Numeric limits
    min_weight = Column(Float, nullable=True)
    max_weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)
    tolerance = Column(Float, nullable=True, default=0.05)
    
    # Complex rules
    rule_json = Column(JSON, nullable=True)
    exemptions = Column(JSON, nullable=True)
    
    # Severity
    breach_severity = Column(String(20), default="high")
    
    # Validity
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Source tracking
    source_document = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    
    # Relationship
    client = relationship('Client', back_populates='ips_constraints')
    
    __table_args__ = (
        Index('ix_ips_client_type', 'client_id', 'constraint_type'),
    )
    
    def __repr__(self):
        return f"<ClientIPS(client_id={self.client_id}, name='{self.constraint_name}')>"


class ESGExclusion(Base):
    """
    ESG exclusion list - securities that fail ESG screening.
    Phase: 7.0 - Compliance Schema Foundation
    """
    __tablename__ = 'esg_exclusions'
    
    id = Column(Integer, primary_key=True)
    
    # Security identification (ticker fallback for YFinance compatibility)
    isin = Column(String(12), nullable=True, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    company_name = Column(String(200), nullable=False)
    
    # Exclusion details
    category = Column(Enum(ESGCategory), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    reason = Column(String(500), nullable=False)
    
    # Source and validity
    source = Column(String(100), nullable=False)
    effective_date = Column(Date, nullable=False, default=datetime.date.today)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Threshold (for partial involvement screening)
    revenue_threshold = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        Index('ix_esg_isin_active', 'isin', 'is_active'),
        Index('ix_esg_ticker_active', 'ticker', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ESGExclusion(company='{self.company_name}', category='{self.category.value}')>"


class ComplianceBreach(Base):
    """
    Audit log of all compliance breaches.
    Phase: 7.0 - Compliance Schema Foundation
    """
    __tablename__ = 'compliance_breaches'
    
    id = Column(Integer, primary_key=True)
    
    # What portfolio and constraint?
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    constraint_id = Column(Integer, ForeignKey('client_ips.id', ondelete='SET NULL'),
                          nullable=True, index=True)
    
    # Breach classification
    breach_type = Column(String(50), nullable=False)
    severity = Column(Enum(BreachSeverity), nullable=False, index=True)
    
    # Breach details
    current_value = Column(Float, nullable=False)
    limit_value = Column(Float, nullable=False)
    
    # What's involved
    ticker = Column(String(20), nullable=True)
    isin = Column(String(12), nullable=True)
    asset_class = Column(String(50), nullable=True)
    
    # Human-readable
    description = Column(String(500), nullable=False)
    recommended_action = Column(String(500), nullable=True)
    
    # Timing
    detected_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    
    # Resolution tracking
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(String(500), nullable=True)
    
    # Compliance run reference
    compliance_run_id = Column(String(50), nullable=True, index=True)
    
    # Relationships
    portfolio = relationship('Portfolio')
    constraint = relationship('ClientIPS')
    
    __table_args__ = (
        Index('ix_breach_portfolio_date', 'portfolio_id', 'detected_at'),
        Index('ix_breach_unresolved', 'portfolio_id', 'resolved'),
    )
    
    def __repr__(self):
        return f"<ComplianceBreach(type='{self.breach_type}', severity='{self.severity.value}')>"
```

### 1.3 Modify Existing `Asset` Class (~line 28)

**Add these 3 columns** to your existing Asset class:

```python
class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    asset_class = Column(String(50))
    sector = Column(String(50), nullable=True)
    industry = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    
    # =========== ADD THESE 3 NEW COLUMNS (Phase 7.0) ===========
    isin = Column(String(12), nullable=True, unique=True, index=True)
    asset_subclass = Column(String(50), nullable=True, index=True)
    is_esg_excluded = Column(Boolean, default=False, index=True)
    # ============================================================
    
    # ... rest of existing relationships ...
```

### 1.4 Modify Existing `Portfolio` Class (~line 401)

**Add client_id column and relationship:**

```python
class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    cash_balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, 
                       onupdate=datetime.datetime.utcnow)
    
    # =========== ADD THIS NEW COLUMN (Phase 7.0) ===========
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    # =======================================================
    
    # Relationships
    holdings = relationship('PortfolioHolding', back_populates='portfolio', 
                           cascade='all, delete-orphan')
    decision_logs = relationship('DecisionLog', back_populates='portfolio', 
                                cascade='all, delete-orphan')
    
    # =========== ADD THIS NEW RELATIONSHIP (Phase 7.0) ===========
    client = relationship('Client', back_populates='portfolios')
    # =============================================================

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"
```

### 1.5 Modify Existing `DecisionLog` Class (~line 457)

**Add compliance tracking fields:**

```python
class DecisionLog(Base):
    __tablename__ = 'decision_logs'
    
    # ... existing columns ...
    
    # =========== ADD THESE 2 NEW COLUMNS (Phase 7.0) ===========
    compliance_status = Column(String(20), nullable=True, index=True)
    # "compliant", "non_compliant", "warning"
    
    compliance_breaches = Column(JSON, nullable=True)
    # Snapshot of breaches when decision was made
    # ============================================================
    
    # ... rest of existing code ...
```

---

## 4. Step 2: Update decision_schemas.py

### Location: `src/agents/decision_schemas.py`

### 2.1 Update Imports (~line 22)

Change:
```python
from typing import List, Dict, Optional, Literal
```

To:
```python
from typing import List, Dict, Optional, Literal, Any
```

### 2.2 Add New Enums (after `RiskStatus` enum, ~line 46)

```python
# =============================================================================
# PHASE 7.0: COMPLIANCE ENUMS
# =============================================================================

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
    """Severity classification for compliance breaches."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceStatus(str, Enum):
    """Overall compliance status for a portfolio."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
```

### 2.3 Add New Dataclasses (at END of file, after `DecisionContext`)

```python
# =============================================================================
# PHASE 7.0: COMPLIANCE DATACLASSES
# =============================================================================

@dataclass
class IPSConstraint:
    """A single IPS constraint loaded from database."""
    type: ConstraintType
    name: str
    
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    ticker: Optional[str] = None
    
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    target_weight: Optional[float] = None
    tolerance: float = 0.05
    
    exemptions: List[str] = field(default_factory=list)
    breach_severity: BreachSeverity = BreachSeverity.HIGH
    rule: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "asset_class": self.asset_class,
            "sector": self.sector,
            "ticker": self.ticker,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "target_weight": self.target_weight,
            "tolerance": self.tolerance,
            "exemptions": self.exemptions,
            "breach_severity": self.breach_severity.value,
            "rule": self.rule
        }


@dataclass
class ComplianceCheck:
    """Result of checking ONE constraint against a portfolio."""
    constraint_name: str
    constraint_type: ConstraintType
    status: Literal["pass", "warning", "breach"]
    
    severity: Optional[BreachSeverity] = None
    current_value: float = 0.0
    limit_value: float = 0.0
    
    ticker: Optional[str] = None
    isin: Optional[str] = None
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    
    message: str = ""
    action: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "constraint_name": self.constraint_name,
            "constraint_type": self.constraint_type.value,
            "status": self.status,
            "severity": self.severity.value if self.severity else None,
            "current_value": self.current_value,
            "limit_value": self.limit_value,
            "ticker": self.ticker,
            "isin": self.isin,
            "asset_class": self.asset_class,
            "sector": self.sector,
            "message": self.message,
            "action": self.action
        }
    
    def format_row(self) -> str:
        """Format as a single row for display."""
        severity_emoji = {
            BreachSeverity.CRITICAL: "🔴",
            BreachSeverity.HIGH: "🟠",
            BreachSeverity.MEDIUM: "🟡",
            BreachSeverity.LOW: "ℹ️"
        }
        emoji = severity_emoji.get(self.severity, "✓") if self.status != "pass" else "✓"
        target = self.ticker or self.asset_class or self.sector or "Portfolio"
        return f"{emoji} {self.constraint_name}: {target} at {self.current_value:.1%} (limit: {self.limit_value:.1%})"


@dataclass
class RemediationTrade:
    """
    A specific trade to fix a compliance breach.
    Added based on Gemini feedback - connects breaches to actionable trades.
    """
    action: Literal["BUY", "SELL", "TRIM", "ADD"]
    ticker: str
    
    shares: Optional[float] = None
    target_weight: Optional[float] = None
    estimated_value: float = 0.0
    
    reason: str = ""
    priority: int = 1
    breach_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "ticker": self.ticker,
            "shares": self.shares,
            "target_weight": self.target_weight,
            "estimated_value": self.estimated_value,
            "reason": self.reason,
            "priority": self.priority,
            "breach_type": self.breach_type
        }
    
    def format_instruction(self) -> str:
        """Format as human-readable instruction."""
        if self.shares:
            return f"{self.action} {self.shares:.0f} shares of {self.ticker} (~${self.estimated_value:,.0f})"
        elif self.target_weight:
            return f"{self.action} {self.ticker} to {self.target_weight:.1%} weight (~${self.estimated_value:,.0f})"
        else:
            return f"{self.action} {self.ticker} (~${self.estimated_value:,.0f})"


@dataclass
class ComplianceReport:
    """Full compliance report for a portfolio."""
    
    portfolio_id: int
    portfolio_name: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    
    as_of_date: datetime = field(default_factory=datetime.utcnow)
    compliance_run_id: str = ""
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    
    total_aum: float = 0.0
    num_positions: int = 0
    
    checks: List[ComplianceCheck] = field(default_factory=list)
    allocation: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    remediation_trades: List[RemediationTrade] = field(default_factory=list)
    
    @property
    def breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "breach"]
    
    @property
    def warnings(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "warning"]
    
    @property
    def passes(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "pass"]
    
    @property
    def critical_breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.breaches if c.severity == BreachSeverity.CRITICAL]
    
    @property
    def num_breaches(self) -> int:
        return len(self.breaches)
    
    @property 
    def num_critical(self) -> int:
        return len(self.critical_breaches)
    
    def to_dict(self) -> Dict:
        return {
            "portfolio_id": self.portfolio_id,
            "portfolio_name": self.portfolio_name,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "as_of_date": self.as_of_date.isoformat(),
            "compliance_run_id": self.compliance_run_id,
            "status": self.status.value,
            "total_aum": self.total_aum,
            "num_positions": self.num_positions,
            "checks": [c.to_dict() for c in self.checks],
            "allocation": self.allocation,
            "recommendations": self.recommendations,
            "remediation_trades": [t.to_dict() for t in self.remediation_trades],
            "summary": {
                "num_breaches": self.num_breaches,
                "num_critical": self.num_critical,
                "num_warnings": len(self.warnings),
                "num_passes": len(self.passes)
            }
        }
    
    def format_summary(self) -> str:
        """Format executive summary."""
        status_emoji = {
            ComplianceStatus.COMPLIANT: "✅ COMPLIANT",
            ComplianceStatus.WARNING: "⚠️ WARNING",
            ComplianceStatus.NON_COMPLIANT: "🔴 NON-COMPLIANT"
        }
        
        lines = [
            "═" * 65,
            "                     COMPLIANCE REPORT",
            "═" * 65,
            f"Portfolio: {self.portfolio_name} (ID: {self.portfolio_id})",
            f"Client:    {self.client_name or 'N/A'} ({self.client_id or 'N/A'})",
            f"Date:      {self.as_of_date.strftime('%Y-%m-%d %H:%M')}",
            f"Status:    {status_emoji.get(self.status, self.status.value)}",
            "",
            f"Total AUM:    ${self.total_aum:,.2f}",
            f"Positions:    {self.num_positions}",
            f"Breaches:     {self.num_breaches} ({self.num_critical} critical)",
            f"Warnings:     {len(self.warnings)}",
            "",
            f"Run ID: {self.compliance_run_id}",
            "═" * 65,
        ]
        return "\n".join(lines)
    
    def format_breaches_table(self) -> str:
        """Format breach table for display."""
        if not self.breaches:
            return "✓ No breaches detected."
        
        lines = ["─" * 65, "DETAILED BREACHES", "─" * 65]
        
        severity_emoji = {
            BreachSeverity.CRITICAL: "🔴 CRIT",
            BreachSeverity.HIGH: "🟠 HIGH",
            BreachSeverity.MEDIUM: "🟡 MED ",
            BreachSeverity.LOW: "ℹ️  LOW "
        }
        
        sorted_breaches = sorted(
            self.breaches, 
            key=lambda x: ["critical", "high", "medium", "low"].index(
                x.severity.value if x.severity else "low"
            )
        )
        
        for b in sorted_breaches:
            sev = severity_emoji.get(b.severity, "    ")
            target = b.ticker or b.asset_class or "N/A"
            lines.append(
                f"{sev} │ {b.constraint_name[:25]:<25} │ {target:<8} │ "
                f"{b.current_value:>6.1%} vs {b.limit_value:>6.1%}"
            )
        
        lines.append("─" * 65)
        return "\n".join(lines)
    
    def format_remediation(self) -> str:
        """Format remediation trades."""
        if not self.remediation_trades:
            return "No remediation trades required."
        
        lines = ["─" * 65, "REMEDIATION TRADES", "─" * 65]
        
        for i, trade in enumerate(self.remediation_trades, 1):
            lines.append(f"  {i}. {trade.format_instruction()}")
            if trade.reason:
                lines.append(f"     Reason: {trade.reason}")
        
        lines.append("─" * 65)
        return "\n".join(lines)
    
    def format_full_report(self) -> str:
        """Format complete compliance report."""
        return "\n\n".join([
            self.format_summary(),
            self.format_breaches_table(),
            self.format_remediation(),
            "═" * 65
        ])
```

### 2.4 Update Existing `RiskAssessment` Dataclass (~line 48)

**Add this field:**

```python
@dataclass
class RiskAssessment:
    """Structured risk evaluation - runs BEFORE optimization."""
    status: RiskStatus
    
    primary_drivers: List[str] = field(default_factory=list)
    breaches: List[str] = field(default_factory=list)
    
    concentration_score: float = 0.0
    max_position_weight: float = 0.0
    num_positions: int = 0
    estimated_volatility: float = 0.0
    tail_risk_estimate: Optional[float] = None
    
    suggested_action: DecisionType = DecisionType.HOLD
    
    # =========== ADD THIS NEW FIELD (Phase 7.0) ===========
    compliance_breaches: List['ComplianceCheck'] = field(default_factory=list)
    # ======================================================
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "primary_drivers": self.primary_drivers,
            "breaches": self.breaches,
            "concentration_score": self.concentration_score,
            "max_position_weight": self.max_position_weight,
            "num_positions": self.num_positions,
            "estimated_volatility": self.estimated_volatility,
            "tail_risk_estimate": self.tail_risk_estimate,
            "suggested_action": self.suggested_action.value,
            # =========== ADD THIS (Phase 7.0) ===========
            "compliance_breaches": [b.to_dict() for b in self.compliance_breaches] if self.compliance_breaches else []
            # ============================================
        }
    
    # ... rest unchanged ...
```

---

## 5. Step 3: Update config.py

### Location: `src/config.py`

### 3.1 Add ComplianceConfig Class (after other config classes)

```python
@dataclass
class ComplianceConfig:
    """Compliance checking configuration. Phase 7.0"""
    
    # Default constraints
    default_max_equity: float = 0.80
    default_max_fixed_income: float = 0.80
    default_min_cash: float = 0.02
    default_max_single_issuer: float = 0.10
    default_concentration_exemptions: tuple = (
        "asset_subclass:government_bond",
        "asset_subclass:money_market",
    )
    
    # Tolerance settings
    allocation_tolerance: float = 0.05
    concentration_tolerance: float = 0.02
    liquidity_tolerance: float = 0.01
    warning_threshold: float = 0.90
    
    # Severity classification
    non_compliant_breach_count: int = 1
    critical_auto_escalate: bool = True
    esg_breach_severity: str = "critical"
    allocation_breach_severity: str = "high"
    concentration_breach_severity: str = "high"
    liquidity_breach_severity: str = "medium"
    
    # ESG screening
    esg_enabled: bool = True
    esg_zero_tolerance: bool = True
    esg_revenue_threshold: float = 0.05
    default_esg_categories: tuple = ("tobacco", "thermal_coal", "controversial_weapons")
    
    # Run settings
    run_id_prefix: str = "COMP"
    max_recommendations: int = 5
    persist_breaches: bool = True
    
    # Display
    display_currency: str = "USD"
    display_currency_symbol: str = "$"
```

### 3.2 Add to AppConfig

```python
@dataclass
class AppConfig:
    """Main configuration container."""
    data: DataConfig = field(default_factory=DataConfig)
    macro: MacroConfig = field(default_factory=MacroConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    rebalance: RebalanceConfig = field(default_factory=RebalanceConfig)
    risk: RiskManagerConfig = field(default_factory=RiskManagerConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)  # <-- ADD THIS
```

---

## 6. Step 4: Update schemas.py

### Location: `src/agents/schemas.py`

### 4.1 Add to ExecutionIntent Enum (~line 35)

```python
class ExecutionIntent(str, Enum):
    OPTIMIZATION = "optimization"
    MACRO_ANALYSIS = "macro_analysis"
    REBALANCING = "rebalancing"
    BACKTEST = "backtest"
    DATA_FETCH = "data_fetch"
    RISK_ANALYSIS = "risk_analysis"
    DATA_MANAGEMENT = "data_management"
    PORTFOLIO_MGMT = "portfolio_mgmt"
    CLARIFICATION_NEEDED = "clarification_needed"
    DOCUMENT_SEARCH = "document_search"
    COMPLIANCE_CHECK = "compliance_check"  # <-- ADD THIS
    UNKNOWN = "unknown"
```

### 4.2 Add to AgentName Enum (~line 64)

```python
class AgentName(str, Enum):
    DATA_AGENT = "DataAgent"
    MACRO_AGENT = "MacroAgent"
    OPTIMIZATION_AGENT = "OptimizationAgent"
    REBALANCE_AGENT = "RebalanceAgent"
    BACKTEST_AGENT = "BacktestAgent"
    ROUTER = "Router"
    RAG_AGENT = "RAGAgent"
    COMPLIANCE_AGENT = "ComplianceAgent"  # <-- ADD THIS
```

---

## 7. Step 5: Run Migration / Recreate DB

### Option A: Delete and Recreate (Recommended for Demo)

```bash
# Backup (optional)
cp data/portfolio.db data/portfolio.db.backup

# Delete
rm data/portfolio.db

# Recreate
python -c "from src.portfolio_tool.database_setup import Base, engine; Base.metadata.create_all(engine)"

# Verify
python -c "
from src.portfolio_tool.database_setup import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)
assert 'clients' in tables, 'Missing clients table!'
assert 'client_ips' in tables, 'Missing client_ips table!'
assert 'esg_exclusions' in tables, 'Missing esg_exclusions table!'
assert 'compliance_breaches' in tables, 'Missing compliance_breaches table!'
print('✓ All Phase 7.0 tables created!')
"
```

### Option B: Use Alembic (if you have existing data)

Use the migration file from `/phase7_output/migrations/versions/007_compliance_schema.py`

---

## 8. Step 6: Seed Data

Copy the seed scripts from `/phase7_output/scripts/` to your project, then:

```bash
# Seed ESG exclusions (25+ companies)
python scripts/seed_esg_exclusions.py

# Seed sample clients (including Anders Family Trust for the Golden Prompt)
python scripts/seed_sample_clients.py

# Link your portfolio to Anders (replace 1 with your portfolio ID)
python scripts/seed_sample_clients.py --link 1
```

---

## 9. Step 7: Verify Installation

```bash
python -c "
from src.portfolio_tool.database_setup import get_session, Client, ESGExclusion
from src.agents.decision_schemas import ComplianceReport, ComplianceStatus
from src.config import config

# Check database
session = get_session()
clients = session.query(Client).count()
exclusions = session.query(ESGExclusion).count()
print(f'✓ Clients: {clients}')
print(f'✓ ESG Exclusions: {exclusions}')

# Check Anders Family Trust
anders = session.query(Client).filter(Client.client_id == '8821-X').first()
if anders:
    print(f'✓ Anders Family Trust: {anders.name}')
else:
    print('⚠ Anders Family Trust not found - run seed_sample_clients.py')

# Check schemas
report = ComplianceReport(portfolio_id=1, portfolio_name='Test', status=ComplianceStatus.COMPLIANT)
print(f'✓ ComplianceReport: {report.status.value}')

# Check config
print(f'✓ Config: default_max_equity={config.compliance.default_max_equity}')

print('\\n✓ PHASE 7.0 COMPLETE!')
"
```

---

## 10. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `no such table: clients` | DB not recreated | `rm data/portfolio.db` then recreate |
| `cannot import ComplianceConfig` | config.py not updated | Add ComplianceConfig class |
| `column assets.isin does not exist` | Existing DB, no migration | Delete DB or run Alembic |
| `ImportError: BreachSeverity` | decision_schemas.py not updated | Add the enum |

---

## ✅ Phase 7.0 Complete!

**You now have:**
- 4 new database tables
- 3 modified tables  
- Compliance enums and dataclasses
- ComplianceConfig
- 25+ seeded ESG exclusions
- 4 sample clients with IPS constraints
- Anders Family Trust ready for the "Golden Prompt"

**Next: Phase 7.1** - Build `IPSManager` and `ESGScreener` classes.
