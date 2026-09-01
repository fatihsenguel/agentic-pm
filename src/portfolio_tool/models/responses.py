"""
Structured response models for agent communication.

These classes ensure agents receive consistent, typed data from tools.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class UpdateResult:
    """Standard response for data update operations."""
    
    success: bool
    operation: str  # Describes what was done
    affected_count: int  # How many records/chunks/rows
    
    # Generic identifier (what was updated)
    entities: List[str] = field(default_factory=list)
    entity_type: str = "unknown"  # "asset", "indicator", "document", etc.
    
    # Time relevance (if applicable)
    date_range: Optional[tuple[datetime, datetime]] = None
    
    # Type-specific details go here
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error info
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "success": self.success,
            "operation": self.operation,
            "affected_count": self.affected_count,
            "entities": self.entities,
            "entity_type": self.entity_type,
            "date_range": (
                [self.date_range[0].isoformat(), self.date_range[1].isoformat()] 
                if self.date_range else None
            ),
            "metadata": self.metadata,
            "error_message": self.error_message
        }


@dataclass
class QueryResult:
    """Standard response for data retrieval operations."""
    
    success: bool
    data: List[Dict[str, Any]]
    count: int
    query_type: str  # e.g., "get_balance_sheets"
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "success": self.success,
            "data": self.data,
            "count": self.count,
            "query_type": self.query_type,
            "metadata": self.metadata or {},
            "error_message": self.error_message
        }