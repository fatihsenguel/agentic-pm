# src/agents/compliance_agent.py
"""
Compliance Agent - Orchestrates IPS compliance checking.

Phase: 7.2 - Compliance Agent

PURPOSE:
The Compliance Agent is the "brain" that checks portfolios against
Investment Policy Statement (IPS) constraints. It orchestrates:
- Allocation limit checks (asset class min/max)
- Concentration limit checks (single issuer limits)
- Liquidity checks (cash minimums)
- ESG screening (exclusion list)

PATTERN:
- Deterministic rule engine (NO LLM for calculations)
- Uses IPSManager for constraint loading
- Uses ESGScreener for exclusion checks
- Outputs structured ComplianceReport

USAGE:
    from agents.compliance_agent import ComplianceAgent
    
    agent = ComplianceAgent()
    report = agent.run_compliance_check(portfolio_id=1)
    
    if report.status == ComplianceStatus.NON_COMPLIANT:
        print(report.format_full_report())
        for trade in report.remediation_trades:
            print(trade.format_instruction())

INTERVIEW TALKING POINT:
    "The Compliance Agent is purely deterministic - no LLM interprets
    the rules. This is critical for audit trails. The LLM only helps
    with natural language IPS extraction (Phase 7.6), never rule execution."
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import uuid

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import (
    get_session,
    Portfolio,
    PortfolioHolding,
    Asset,
    DailyPrice,
    Client
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.ips_manager import IPSManager
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.esg_screener import ESGScreener
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.decision_schemas import (
    IPSConstraint,
    ConstraintType,
    BreachSeverity,
    ComplianceStatus,
    ComplianceCheck,
    ComplianceReport,
    RemediationTrade
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.config import config


class ComplianceAgent:
    """
    Orchestrates portfolio compliance checking against IPS constraints.
    
    The agent is stateless - all state is passed in or loaded fresh.
    This ensures reproducible compliance runs.
    
    Interview Talking Point:
        "Each compliance run generates a unique ID and timestamp.
        We can reproduce any historical check by loading the same
        portfolio snapshot and constraints."
    """
    
    def __init__(self):
        """Initialize ComplianceAgent with config."""
        self.config = config.compliance
        self._session = None
        self._ips_manager = None
        self._esg_screener = None
    
    @property
    def session(self):
        """Lazy session initialization."""
        if self._session is None:
            self._session = get_session()
        return self._session
    
    @property
    def ips_manager(self) -> IPSManager:
        """Lazy IPSManager initialization."""
        if self._ips_manager is None:
            self._ips_manager = IPSManager(session=self.session)
        return self._ips_manager
    
    @property
    def esg_screener(self) -> ESGScreener:
        """Lazy ESGScreener initialization."""
        if self._esg_screener is None:
            self._esg_screener = ESGScreener(session=self.session)
        return self._esg_screener
    
    def close(self):
        """Clean up resources."""
        if self._session is not None:
            self._session.close()
            self._session = None
            self._ips_manager = None
            self._esg_screener = None
    
    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================
    
    def run_compliance_check(
        self,
        portfolio_id: int,
        client_id: Optional[str] = None,
        include_passing: bool = False
    ) -> ComplianceReport:
        """
        Run a full compliance check on a portfolio.
        
        This is the PRIMARY method - call this from the graph/router.
        
        Args:
            portfolio_id: Portfolio's database ID
            client_id: Optional client ID override (if not linked to portfolio)
            include_passing: Whether to include passing checks in report
            
        Returns:
            ComplianceReport with all checks and recommendations
        """
        # Generate unique run ID
        run_id = self._generate_run_id()
        
        # Load portfolio
        portfolio = self.session.get(Portfolio, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")
        
        # Load client (from portfolio link or override)
        client = None
        if client_id:
            client = self.ips_manager.get_client(client_id)
        elif portfolio.client_id:
            client = self.session.get(Client, portfolio.client_id)
        
        # Load holdings with current values
        holdings_data = self._load_holdings(portfolio_id)
        
        if not holdings_data["holdings"]:
            # Empty portfolio - return compliant report
            return ComplianceReport(
                portfolio_id=portfolio_id,
                portfolio_name=portfolio.name,
                client_id=client.client_id if client else None,
                client_name=client.name if client else None,
                compliance_run_id=run_id,
                status=ComplianceStatus.COMPLIANT,
                total_aum=portfolio.cash_balance or 0,
                num_positions=0,
                allocation={"cash": 1.0}
            )
        
        # Load constraints
        if client:
            constraints = self.ips_manager.get_client_constraints(client.id)
            esg_categories = self.ips_manager.get_esg_categories(client.id)
        else:
            # Use defaults
            constraints = self.ips_manager.get_default_constraints()
            esg_categories = list(self.config.default_esg_categories)
        
        # Run all checks
        all_checks = []
        
        # 1. Allocation checks
        allocation_checks = self._check_allocation_constraints(
            holdings_data, constraints
        )
        all_checks.extend(allocation_checks)
        
        # 2. Concentration checks
        concentration_checks = self._check_concentration_constraints(
            holdings_data, constraints
        )
        all_checks.extend(concentration_checks)
        
        # 3. Liquidity checks
        liquidity_checks = self._check_liquidity_constraints(
            holdings_data, constraints, portfolio.cash_balance or 0
        )
        all_checks.extend(liquidity_checks)
        
        # 4. ESG screening
        if self.config.esg_enabled and esg_categories:
            esg_checks = self.esg_screener.check_holdings_list(
                holdings_data["holdings_list"],
                categories=esg_categories
            )
            all_checks.extend(esg_checks)
        
        # Determine overall status
        status = self._determine_status(all_checks)
        
        # Filter checks for report
        if include_passing:
            report_checks = all_checks
        else:
            report_checks = [c for c in all_checks if c.status != "pass"]
        
        # Generate recommendations and remediation trades
        recommendations, remediation_trades = self._generate_recommendations(
            all_checks, holdings_data
        )
        
        # Build report
        report = ComplianceReport(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            client_id=client.client_id if client else None,
            client_name=client.name if client else None,
            as_of_date=datetime.utcnow(),
            compliance_run_id=run_id,
            status=status,
            total_aum=holdings_data["total_value"],
            num_positions=len(holdings_data["holdings"]),
            checks=report_checks,
            allocation=holdings_data["allocation"],
            recommendations=recommendations,
            remediation_trades=remediation_trades
        )
        
        return report
    
    # =========================================================================
    # ALLOCATION CHECKS
    # =========================================================================
    
    def _check_allocation_constraints(
        self,
        holdings_data: Dict,
        constraints: List[IPSConstraint]
    ) -> List[ComplianceCheck]:
        """
        Check allocation constraints (asset class min/max).
        
        Examples:
            - "Max Equity: 65%"
            - "Min Fixed Income: 20%"
        """
        checks = []
        allocation = holdings_data["allocation"]
        
        # Filter to allocation constraints
        allocation_constraints = [
            c for c in constraints 
            if c.type == ConstraintType.ALLOCATION and c.asset_class
        ]
        
        for constraint in allocation_constraints:
            asset_class = constraint.asset_class.lower()
            current_weight = allocation.get(asset_class, 0.0)
            
            # Check max limit
            if constraint.max_weight is not None:
                limit = constraint.max_weight
                tolerance = constraint.tolerance or 0
                
                if current_weight > limit + tolerance:
                    # Breach
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="breach",
                        severity=constraint.breach_severity,
                        current_value=current_weight,
                        limit_value=limit,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current_weight:.1%} exceeds {limit:.1%} limit",
                        action=f"REDUCE {asset_class.title()} by {current_weight - limit:.1%}"
                    ))
                elif current_weight > limit:
                    # Warning (within tolerance)
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="warning",
                        severity=BreachSeverity.LOW,
                        current_value=current_weight,
                        limit_value=limit,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current_weight:.1%} near {limit:.1%} limit"
                    ))
                else:
                    # Pass
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="pass",
                        current_value=current_weight,
                        limit_value=limit,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current_weight:.1%} within {limit:.1%} limit"
                    ))
            
            # Check min limit
            if constraint.min_weight is not None:
                limit = constraint.min_weight
                tolerance = constraint.tolerance or 0
                
                if current_weight < limit - tolerance:
                    # Breach
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="breach",
                        severity=constraint.breach_severity,
                        current_value=current_weight,
                        limit_value=limit,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current_weight:.1%} below {limit:.1%} minimum",
                        action=f"INCREASE {asset_class.title()} by {limit - current_weight:.1%}"
                    ))
                elif current_weight < limit:
                    # Warning
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.ALLOCATION,
                        status="warning",
                        severity=BreachSeverity.LOW,
                        current_value=current_weight,
                        limit_value=limit,
                        asset_class=asset_class,
                        message=f"{asset_class.title()} at {current_weight:.1%} near {limit:.1%} minimum"
                    ))
        
        return checks
    
    # =========================================================================
    # CONCENTRATION CHECKS
    # =========================================================================
    
    def _check_concentration_constraints(
        self,
        holdings_data: Dict,
        constraints: List[IPSConstraint]
    ) -> List[ComplianceCheck]:
        """
        Check concentration constraints (single issuer limits).
        
        Examples:
            - "No single issuer > 5% (excluding US Treasuries)"
        """
        checks = []
        holdings = holdings_data["holdings"]
        total_value = holdings_data["total_value"]
        
        # Filter to concentration constraints
        concentration_constraints = [
            c for c in constraints 
            if c.type == ConstraintType.CONCENTRATION
        ]
        
        for constraint in concentration_constraints:
            max_weight = constraint.max_weight
            if max_weight is None:
                continue
            
            tolerance = constraint.tolerance or 0
            exemptions = constraint.exemptions or []
            
            # Check each holding
            for holding in holdings:
                ticker = holding["ticker"]
                weight = holding["weight"]
                asset_subclass = holding.get("asset_subclass", "")
                
                # Check if exempt
                if self._is_exempt(holding, exemptions):
                    continue
                
                if weight > max_weight + tolerance:
                    # Breach
                    excess = weight - max_weight
                    excess_value = excess * total_value
                    
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.CONCENTRATION,
                        status="breach",
                        severity=constraint.breach_severity,
                        current_value=weight,
                        limit_value=max_weight,
                        ticker=ticker,
                        asset_class=holding.get("asset_class"),
                        message=f"{ticker} at {weight:.1%} exceeds {max_weight:.1%} single-issuer limit",
                        action=f"TRIM {ticker} by {excess:.1%} (~${excess_value:,.0f})"
                    ))
                elif weight > max_weight:
                    # Warning
                    checks.append(ComplianceCheck(
                        constraint_name=constraint.name,
                        constraint_type=ConstraintType.CONCENTRATION,
                        status="warning",
                        severity=BreachSeverity.LOW,
                        current_value=weight,
                        limit_value=max_weight,
                        ticker=ticker,
                        message=f"{ticker} at {weight:.1%} near {max_weight:.1%} limit"
                    ))
        
        return checks
    
    # =========================================================================
    # LIQUIDITY CHECKS
    # =========================================================================
    
    def _check_liquidity_constraints(
        self,
        holdings_data: Dict,
        constraints: List[IPSConstraint],
        cash_balance: float
    ) -> List[ComplianceCheck]:
        """
        Check liquidity constraints (cash minimums).
        
        Examples:
            - "Min Cash: 5%"
        """
        checks = []
        total_value = holdings_data["total_value"]
        allocation = holdings_data["allocation"]
        
        # Filter to liquidity constraints
        liquidity_constraints = [
            c for c in constraints 
            if c.type == ConstraintType.LIQUIDITY
        ]
        
        for constraint in liquidity_constraints:
            if constraint.min_weight is None:
                continue
            
            min_weight = constraint.min_weight
            tolerance = constraint.tolerance or 0
            
            # Get cash weight (from allocation or calculate)
            cash_weight = allocation.get("cash", 0)
            if cash_weight == 0 and total_value > 0:
                cash_weight = cash_balance / total_value
            
            if cash_weight < min_weight - tolerance:
                # Breach
                shortfall = min_weight - cash_weight
                shortfall_value = shortfall * total_value
                
                checks.append(ComplianceCheck(
                    constraint_name=constraint.name,
                    constraint_type=ConstraintType.LIQUIDITY,
                    status="breach",
                    severity=constraint.breach_severity,
                    current_value=cash_weight,
                    limit_value=min_weight,
                    asset_class="cash",
                    message=f"Cash at {cash_weight:.1%} below {min_weight:.1%} minimum",
                    action=f"RAISE CASH by {shortfall:.1%} (~${shortfall_value:,.0f})"
                ))
            elif cash_weight < min_weight:
                # Warning
                checks.append(ComplianceCheck(
                    constraint_name=constraint.name,
                    constraint_type=ConstraintType.LIQUIDITY,
                    status="warning",
                    severity=BreachSeverity.LOW,
                    current_value=cash_weight,
                    limit_value=min_weight,
                    asset_class="cash",
                    message=f"Cash at {cash_weight:.1%} near {min_weight:.1%} minimum"
                ))
            else:
                # Pass
                checks.append(ComplianceCheck(
                    constraint_name=constraint.name,
                    constraint_type=ConstraintType.LIQUIDITY,
                    status="pass",
                    current_value=cash_weight,
                    limit_value=min_weight,
                    asset_class="cash",
                    message=f"Cash at {cash_weight:.1%} above {min_weight:.1%} minimum"
                ))
        
        return checks
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _load_holdings(self, portfolio_id: int) -> Dict:
        """
        Load portfolio holdings with current prices and weights.
        
        Returns:
            Dict with keys:
                - holdings: List of holding dicts
                - holdings_list: Same list (for ESG screener)
                - total_value: Total portfolio value
                - allocation: Asset class allocation dict
        """
        holdings_query = (
            self.session.query(PortfolioHolding, Asset)
            .join(Asset, PortfolioHolding.asset_id == Asset.id)
            .filter(PortfolioHolding.portfolio_id == portfolio_id)
            .all()
        )
        
        holdings = []
        total_value = 0.0
        allocation_values = {}
        
        for holding, asset in holdings_query:
            # Get current price
            price = self._get_current_price(asset.id)
            if price is None:
                price = holding.average_price or 0
            
            value = holding.quantity * price
            total_value += value
            
            # Track by asset class
            asset_class = (asset.asset_class or "other").lower()
            allocation_values[asset_class] = allocation_values.get(asset_class, 0) + value
            
            holdings.append({
                "ticker": asset.ticker,
                "isin": asset.isin,
                "name": asset.name,
                "asset_class": asset_class,
                "asset_subclass": asset.asset_subclass,
                "sector": asset.sector,
                "quantity": holding.quantity,
                "price": price,
                "value": value,
                "weight": 0  # Calculated below
            })
        
        # Calculate weights
        for h in holdings:
            h["weight"] = h["value"] / total_value if total_value > 0 else 0
        
        # Calculate allocation percentages
        allocation = {}
        for asset_class, value in allocation_values.items():
            allocation[asset_class] = value / total_value if total_value > 0 else 0
        
        return {
            "holdings": holdings,
            "holdings_list": holdings,  # Alias for ESG screener
            "total_value": total_value,
            "allocation": allocation
        }
    
    def _get_current_price(self, asset_id: int) -> Optional[float]:
        """Get most recent price for an asset."""
        latest = (
            self.session.query(DailyPrice)
            .filter(DailyPrice.asset_id == asset_id)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        return latest.close if latest else None
    
    def _is_exempt(self, holding: Dict, exemptions: List[str]) -> bool:
        """
        Check if a holding is exempt from a constraint.
        
        Exemption format: "field:value"
        Examples:
            - "asset_subclass:government_bond"
            - "ticker:BIL"
            - "sector:utilities"
        """
        for exemption in exemptions:
            if ":" not in exemption:
                continue
            
            field, value = exemption.split(":", 1)
            field = field.lower()
            value = value.lower()
            
            holding_value = str(holding.get(field, "")).lower()
            
            if holding_value == value:
                return True
        
        return False
    
    def _determine_status(self, checks: List[ComplianceCheck]) -> ComplianceStatus:
        """Determine overall compliance status from checks."""
        breaches = [c for c in checks if c.status == "breach"]
        warnings = [c for c in checks if c.status == "warning"]
        
        # Any critical breach = non-compliant
        critical = [c for c in breaches if c.severity == BreachSeverity.CRITICAL]
        if critical and self.config.critical_auto_escalate:
            return ComplianceStatus.NON_COMPLIANT
        
        # Check breach count threshold
        if len(breaches) >= self.config.non_compliant_breach_count:
            return ComplianceStatus.NON_COMPLIANT
        
        # Warnings only
        if warnings:
            return ComplianceStatus.WARNING
        
        return ComplianceStatus.COMPLIANT
    
    def _generate_recommendations(
        self,
        checks: List[ComplianceCheck],
        holdings_data: Dict
    ) -> Tuple[List[str], List[RemediationTrade]]:
        """
        Generate prioritized recommendations and remediation trades.
        
        Returns:
            Tuple of (text recommendations, structured trades)
        """
        recommendations = []
        trades = []
        
        # Get breaches sorted by severity
        breaches = [c for c in checks if c.status == "breach"]
        breaches.sort(key=lambda c: 
            ["critical", "high", "medium", "low"].index(
                c.severity.value if c.severity else "low"
            )
        )
        
        priority = 1
        for breach in breaches[:self.config.max_recommendations]:
            # Text recommendation
            if breach.action:
                recommendations.append(breach.action)
            else:
                recommendations.append(f"Address {breach.constraint_name}: {breach.message}")
            
            # Structured trade
            trade = self._breach_to_trade(breach, holdings_data, priority)
            if trade:
                trades.append(trade)
                priority += 1
        
        return recommendations, trades
    
    def _breach_to_trade(
        self,
        breach: ComplianceCheck,
        holdings_data: Dict,
        priority: int
    ) -> Optional[RemediationTrade]:
        """Convert a breach into a structured remediation trade."""
        total_value = holdings_data["total_value"]
        
        # ESG breach = full liquidation
        if breach.constraint_type == ConstraintType.ESG:
            holding = next(
                (h for h in holdings_data["holdings"] if h["ticker"] == breach.ticker),
                None
            )
            if holding:
                return RemediationTrade(
                    action="SELL",
                    ticker=breach.ticker,
                    shares=holding["quantity"],
                    estimated_value=holding["value"],
                    reason=f"ESG violation: {breach.message}",
                    priority=priority,
                    breach_type="esg"
                )
        
        # Concentration breach = trim to limit
        elif breach.constraint_type == ConstraintType.CONCENTRATION:
            holding = next(
                (h for h in holdings_data["holdings"] if h["ticker"] == breach.ticker),
                None
            )
            if holding:
                excess = breach.current_value - breach.limit_value
                trim_value = excess * total_value
                trim_shares = trim_value / holding["price"] if holding["price"] > 0 else 0
                
                return RemediationTrade(
                    action="TRIM",
                    ticker=breach.ticker,
                    shares=trim_shares,
                    target_weight=breach.limit_value,
                    estimated_value=trim_value,
                    reason=f"Exceeds {breach.limit_value:.0%} concentration limit",
                    priority=priority,
                    breach_type="concentration"
                )
        
        # Liquidity breach = raise cash
        elif breach.constraint_type == ConstraintType.LIQUIDITY:
            shortfall = breach.limit_value - breach.current_value
            raise_value = shortfall * total_value
            
            return RemediationTrade(
                action="SELL",
                ticker="VARIOUS",
                estimated_value=raise_value,
                reason=f"Raise cash to meet {breach.limit_value:.0%} minimum",
                priority=priority,
                breach_type="liquidity"
            )
        
        return None
    
    def _generate_run_id(self) -> str:
        """Generate unique compliance run ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        unique = uuid.uuid4().hex[:6]
        return f"{self.config.run_id_prefix}-{timestamp}-{unique}"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_compliance_check(
    portfolio_id: int,
    client_id: Optional[str] = None
) -> ComplianceReport:
    """
    Convenience function to run a compliance check.
    
    Args:
        portfolio_id: Portfolio's database ID
        client_id: Optional client ID override
        
    Returns:
        ComplianceReport
    """
    agent = ComplianceAgent()
    try:
        return agent.run_compliance_check(portfolio_id, client_id)
    finally:
        agent.close()


def check_portfolio_compliance(portfolio_id: int) -> Dict:
    """
    Quick compliance check returning simple dict.
    
    Args:
        portfolio_id: Portfolio's database ID
        
    Returns:
        Dict with status, num_breaches, breaches list
    """
    report = run_compliance_check(portfolio_id)
    return {
        "status": report.status.value,
        "num_breaches": report.num_breaches,
        "num_critical": report.num_critical,
        "breaches": [
            {
                "type": b.constraint_type.value,
                "severity": b.severity.value if b.severity else None,
                "ticker": b.ticker,
                "message": b.message
            }
            for b in report.breaches
        ]
    }
