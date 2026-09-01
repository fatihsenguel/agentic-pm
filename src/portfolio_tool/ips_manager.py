# src/portfolio_tool/ips_manager.py
"""
IPS Manager - CRUD operations for client IPS constraints.

Phase: 7.1 - IPS Constraint System

PURPOSE:
Manages client Investment Policy Statement (IPS) constraints.
Provides clean interface for loading, creating, and managing constraints.

USAGE:
    from portfolio_tool.ips_manager import IPSManager
    
    manager = IPSManager()
    client = manager.get_client("8821-X")
    constraints = manager.get_client_constraints(client.id)
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import (
    get_session, 
    Client, 
    ClientIPS, 
    Portfolio,
    IPSConstraintType
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.decision_schemas import (
    IPSConstraint, 
    ConstraintType, 
    BreachSeverity
)


class IPSManager:
    """
    Manages IPS constraint CRUD operations.
    
    Interview Talking Point:
        "The IPSManager provides a clean abstraction over the database.
        The Compliance Agent doesn't know about SQLAlchemy - it just
        asks for constraints and gets back typed dataclasses."
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize IPSManager.
        
        Args:
            session: Optional SQLAlchemy session. If not provided,
                    creates a new one from the session factory.
        """
        self._session = session
        self._owns_session = session is None
    
    @property
    def session(self) -> Session:
        """Lazy session initialization."""
        if self._session is None:
            self._session = get_session()
        return self._session
    
    def close(self):
        """Close session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
    
    # =========================================================================
    # CLIENT OPERATIONS
    # =========================================================================
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Get client by external ID (e.g., "8821-X").
        
        Args:
            client_id: The external client identifier
            
        Returns:
            Client object or None if not found
        """
        return self.session.query(Client).filter(
            and_(
                Client.client_id == client_id,
                Client.is_active == True
            )
        ).first()
    
    def get_client_by_db_id(self, db_id: int) -> Optional[Client]:
        """
        Get client by database primary key.
        
        Args:
            db_id: The database ID
            
        Returns:
            Client object or None if not found
        """
        return self.session.get(Client, db_id)
    
    def get_client_by_portfolio(self, portfolio_id: int) -> Optional[Client]:
        """
        Get the client associated with a portfolio.
        
        Args:
            portfolio_id: The portfolio's database ID
            
        Returns:
            Client object or None if portfolio has no client
        """
        portfolio = self.session.get(Portfolio, portfolio_id)
        if portfolio and portfolio.client_id:
            return self.session.get(Client, portfolio.client_id)
        return None
    
    def list_clients(self, active_only: bool = True) -> List[Client]:
        """
        List all clients.
        
        Args:
            active_only: If True, only return active clients
            
        Returns:
            List of Client objects
        """
        query = self.session.query(Client)
        if active_only:
            query = query.filter(Client.is_active == True)
        return query.order_by(Client.name).all()
    
    def create_client(
        self,
        client_id: str,
        name: str,
        client_type: str,
        risk_profile: str = "moderate",
        tax_status: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Client:
        """
        Create a new client.
        
        Args:
            client_id: External identifier (must be unique)
            name: Display name
            client_type: Type (individual, trust, pension, etc.)
            risk_profile: Risk tolerance level
            tax_status: Tax classification
            jurisdiction: Regulatory jurisdiction
            
        Returns:
            The created Client object
        """
        client = Client(
            client_id=client_id,
            name=name,
            client_type=client_type,
            risk_profile=risk_profile,
            tax_status=tax_status,
            jurisdiction=jurisdiction,
            is_active=True
        )
        self.session.add(client)
        self.session.commit()
        return client
    
    # =========================================================================
    # CONSTRAINT OPERATIONS
    # =========================================================================
    
    def get_client_constraints(
        self,
        client_db_id: int,
        constraint_type: Optional[ConstraintType] = None,
        active_only: bool = True
    ) -> List[IPSConstraint]:
        """
        Get all IPS constraints for a client as typed dataclasses.
        
        This is the PRIMARY method used by ComplianceAgent.
        
        Args:
            client_db_id: Client's database ID
            constraint_type: Optional filter by type
            active_only: If True, only return active constraints
            
        Returns:
            List of IPSConstraint dataclasses (not ORM objects)
        """
        query = self.session.query(ClientIPS).filter(
            ClientIPS.client_id == client_db_id
        )
        
        if active_only:
            query = query.filter(ClientIPS.is_active == True)
            # Also filter by effective date
            today = date.today()
            query = query.filter(ClientIPS.effective_date <= today)
            query = query.filter(
                (ClientIPS.expiry_date == None) | (ClientIPS.expiry_date >= today)
            )
        
        if constraint_type:
            # Map from schema enum to DB enum
            db_type = IPSConstraintType[constraint_type.value.upper()]
            query = query.filter(ClientIPS.constraint_type == db_type)
        
        constraints = []
        for db_row in query.all():
            constraints.append(self._db_to_dataclass(db_row))
        
        return constraints
    
    def get_constraints_by_portfolio(
        self,
        portfolio_id: int,
        active_only: bool = True
    ) -> List[IPSConstraint]:
        """
        Get IPS constraints for a portfolio's client.
        
        Convenience method that looks up the client first.
        
        Args:
            portfolio_id: Portfolio's database ID
            active_only: If True, only return active constraints
            
        Returns:
            List of IPSConstraint dataclasses, or empty list if no client
        """
        client = self.get_client_by_portfolio(portfolio_id)
        if not client:
            return []
        return self.get_client_constraints(client.id, active_only=active_only)
    
    def has_esg_constraints(self, client_db_id: int) -> bool:
        """
        Check if a client has any ESG constraints.
        
        Args:
            client_db_id: Client's database ID
            
        Returns:
            True if client has active ESG constraints
        """
        count = self.session.query(ClientIPS).filter(
            and_(
                ClientIPS.client_id == client_db_id,
                ClientIPS.constraint_type == IPSConstraintType.ESG,
                ClientIPS.is_active == True
            )
        ).count()
        return count > 0
    
    def get_esg_categories(self, client_db_id: int) -> List[str]:
        """
        Get the ESG categories this client restricts.
        
        Extracts categories from ESG constraint rule_json.
        
        Args:
            client_db_id: Client's database ID
            
        Returns:
            List of ESG category strings (e.g., ["tobacco", "thermal_coal"])
        """
        esg_constraints = self.session.query(ClientIPS).filter(
            and_(
                ClientIPS.client_id == client_db_id,
                ClientIPS.constraint_type == IPSConstraintType.ESG,
                ClientIPS.is_active == True
            )
        ).all()
        
        categories = []
        for constraint in esg_constraints:
            if constraint.rule_json and "category" in constraint.rule_json:
                categories.append(constraint.rule_json["category"])
        
        return categories
    
    def add_constraint(
        self,
        client_db_id: int,
        constraint: IPSConstraint,
        effective_date: Optional[date] = None,
        source_document: Optional[str] = None
    ) -> int:
        """
        Add an IPS constraint for a client.
        
        Args:
            client_db_id: Client's database ID
            constraint: IPSConstraint dataclass
            effective_date: When constraint becomes active (default: today)
            source_document: Reference to source IPS document
            
        Returns:
            Database ID of created constraint
        """
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
            exemptions=constraint.exemptions if constraint.exemptions else None,
            rule_json=constraint.rule if constraint.rule else None,
            breach_severity=constraint.breach_severity.value,
            effective_date=effective_date or date.today(),
            source_document=source_document,
            is_active=True
        )
        self.session.add(db_constraint)
        self.session.commit()
        return db_constraint.id
    
    def deactivate_constraint(self, constraint_id: int) -> bool:
        """
        Soft-delete a constraint (set is_active=False).
        
        Args:
            constraint_id: Database ID of constraint
            
        Returns:
            True if constraint was found and deactivated
        """
        constraint = self.session.get(ClientIPS, constraint_id)
        if constraint:
            constraint.is_active = False
            self.session.commit()
            return True
        return False
    
    # =========================================================================
    # DEFAULT CONSTRAINTS
    # =========================================================================
    
    def get_default_constraints(self, risk_profile: str = "moderate") -> List[IPSConstraint]:
        """
        Get default constraints for a risk profile.
        
        Used when a portfolio has no client or the client has no constraints.
        
        Args:
            risk_profile: Risk tolerance level
            
        Returns:
            List of default IPSConstraint dataclasses
        """
        # Import config here to avoid circular imports
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.config import config
        cfg = config.compliance
        
        profiles = {
            "conservative": {
                "max_equity": 0.40,
                "min_fixed_income": 0.40,
                "min_cash": 0.10,
                "max_single_issuer": 0.05,
            },
            "moderately_conservative": {
                "max_equity": 0.50,
                "min_fixed_income": 0.35,
                "min_cash": 0.05,
                "max_single_issuer": 0.05,
            },
            "moderate": {
                "max_equity": cfg.default_max_equity,
                "min_fixed_income": 0.20,
                "min_cash": cfg.default_min_cash,
                "max_single_issuer": cfg.default_max_single_issuer,
            },
            "moderately_aggressive": {
                "max_equity": 0.75,
                "min_fixed_income": 0.10,
                "min_cash": 0.02,
                "max_single_issuer": 0.08,
            },
            "aggressive": {
                "max_equity": 0.90,
                "min_fixed_income": 0.05,
                "min_cash": 0.02,
                "max_single_issuer": 0.10,
            },
        }
        
        p = profiles.get(risk_profile, profiles["moderate"])
        
        return [
            IPSConstraint(
                type=ConstraintType.ALLOCATION,
                name="Default Max Equity",
                asset_class="equity",
                max_weight=p["max_equity"],
                tolerance=cfg.allocation_tolerance,
                breach_severity=BreachSeverity(cfg.allocation_breach_severity)
            ),
            IPSConstraint(
                type=ConstraintType.ALLOCATION,
                name="Default Min Fixed Income",
                asset_class="fixed_income",
                min_weight=p["min_fixed_income"],
                tolerance=cfg.allocation_tolerance,
                breach_severity=BreachSeverity(cfg.allocation_breach_severity)
            ),
            IPSConstraint(
                type=ConstraintType.LIQUIDITY,
                name="Default Min Cash",
                asset_class="cash",
                min_weight=p["min_cash"],
                tolerance=cfg.liquidity_tolerance,
                breach_severity=BreachSeverity(cfg.liquidity_breach_severity)
            ),
            IPSConstraint(
                type=ConstraintType.CONCENTRATION,
                name="Default Single Issuer Limit",
                max_weight=p["max_single_issuer"],
                tolerance=cfg.concentration_tolerance,
                exemptions=list(cfg.default_concentration_exemptions),
                breach_severity=BreachSeverity(cfg.concentration_breach_severity)
            ),
        ]
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _db_to_dataclass(self, db_row: ClientIPS) -> IPSConstraint:
        """Convert database ORM object to typed dataclass."""
        # Map DB enum to schema enum
        constraint_type = ConstraintType(db_row.constraint_type.value.lower())
        
        # Map severity string to enum
        try:
            severity = BreachSeverity(db_row.breach_severity)
        except ValueError:
            severity = BreachSeverity.HIGH  # Default fallback
        
        return IPSConstraint(
            type=constraint_type,
            name=db_row.constraint_name,
            asset_class=db_row.asset_class,
            sector=db_row.sector,
            min_weight=db_row.min_weight,
            max_weight=db_row.max_weight,
            target_weight=db_row.target_weight,
            tolerance=db_row.tolerance or 0.05,
            exemptions=db_row.exemptions or [],
            breach_severity=severity,
            rule=db_row.rule_json
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_portfolio_constraints(portfolio_id: int) -> List[IPSConstraint]:
    """
    Convenience function to get constraints for a portfolio.
    
    Args:
        portfolio_id: Portfolio's database ID
        
    Returns:
        List of IPSConstraint dataclasses
    """
    manager = IPSManager()
    try:
        return manager.get_constraints_by_portfolio(portfolio_id)
    finally:
        manager.close()


def get_client_by_portfolio(portfolio_id: int) -> Optional[Client]:
    """
    Convenience function to get client for a portfolio.
    
    Args:
        portfolio_id: Portfolio's database ID
        
    Returns:
        Client object or None
    """
    manager = IPSManager()
    try:
        return manager.get_client_by_portfolio(portfolio_id)
    finally:
        manager.close()