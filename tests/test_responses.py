"""
Test response models.

This ensures UpdateResult and QueryResult work correctly before we use them.
"""

import sys
sys.path.insert(0, r'E:\Programming\AGENTIC_FINANCE\src')

from datetime import datetime
from portfolio_tool.models import UpdateResult, QueryResult


def test_update_result_basic():
    """Test basic UpdateResult creation."""
    
    result = UpdateResult(
        success=True,
        operation="update_daily_prices",
        affected_count=150
    )
    
    # Verify object was created
    assert result.success == True
    assert result.operation == "update_daily_prices"
    assert result.affected_count == 150
    
    # Verify defaults
    assert result.entities == []  # Should be empty list by default
    assert result.entity_type == "unknown"
    assert result.error_message is None
    
    print("✅ Basic UpdateResult creation works!")


def test_update_result_with_entities():
    """Test UpdateResult with stock tickers."""
    
    result = UpdateResult(
        success=True,
        operation="update_daily_prices",
        affected_count=150,
        entities=["AAPL", "MSFT"],
        entity_type="asset",
        date_range=(datetime(2024, 1, 1), datetime(2024, 12, 31))
    )
    
    assert result.entities == ["AAPL", "MSFT"]
    assert result.entity_type == "asset"
    assert result.date_range[0] == datetime(2024, 1, 1)
    
    print("✅ UpdateResult with entities works!")
    print(f"   Entities: {result.entities}")
    print(f"   Type: {result.entity_type}")


def test_update_result_to_dict():
    """Test converting UpdateResult to dictionary."""
    
    result = UpdateResult(
        success=True,
        operation="update_daily_prices",
        affected_count=150,
        entities=["AAPL"],
        entity_type="asset",
        date_range=(datetime(2024, 1, 1), datetime(2024, 12, 31)),
        metadata={"provider": "yfinance"}
    )
    
    # Convert to dict
    result_dict = result.to_dict()
    
    # Verify it's a dictionary
    assert isinstance(result_dict, dict)
    
    # Verify all keys are present
    assert "success" in result_dict
    assert "operation" in result_dict
    assert "affected_count" in result_dict
    assert "entities" in result_dict
    assert "entity_type" in result_dict
    assert "date_range" in result_dict
    assert "metadata" in result_dict
    
    # Verify values
    assert result_dict["success"] == True
    assert result_dict["affected_count"] == 150
    assert result_dict["entities"] == ["AAPL"]
    assert result_dict["entity_type"] == "asset"
    assert result_dict["metadata"]["provider"] == "yfinance"
    
    # Verify date_range is ISO format strings
    assert result_dict["date_range"][0] == "2024-01-01T00:00:00"
    assert result_dict["date_range"][1] == "2024-12-31T00:00:00"
    
    print("✅ to_dict() conversion works!")
    print(f"   Dict keys: {list(result_dict.keys())}")


def test_update_result_error():
    """Test UpdateResult for error scenarios."""
    
    result = UpdateResult(
        success=False,
        operation="update_daily_prices",
        affected_count=0,
        entities=["AAPL"],
        entity_type="asset",
        error_message="API rate limit exceeded"
    )
    
    assert result.success == False
    assert result.affected_count == 0
    assert result.error_message == "API rate limit exceeded"
    
    print("✅ Error handling works!")
    print(f"   Error: {result.error_message}")


def test_query_result_basic():
    """Test basic QueryResult creation."""
    
    result = QueryResult(
        success=True,
        data=[
            {"ticker": "AAPL", "price": 150.0, "date": "2024-01-01"},
            {"ticker": "MSFT", "price": 380.0, "date": "2024-01-01"}
        ],
        count=2,
        query_type="get_daily_prices"
    )
    
    assert result.success == True
    assert result.count == 2
    assert len(result.data) == 2
    assert result.query_type == "get_daily_prices"
    
    print("✅ QueryResult creation works!")
    print(f"   Count: {result.count}")
    print(f"   Query type: {result.query_type}")


def test_query_result_to_dict():
    """Test converting QueryResult to dictionary."""
    
    result = QueryResult(
        success=True,
        data=[{"ticker": "AAPL", "price": 150.0}],
        count=1,
        query_type="get_prices",
        metadata={"source": "database", "cache_hit": True}
    )
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict["success"] == True
    assert result_dict["count"] == 1
    assert result_dict["metadata"]["source"] == "database"
    
    print("✅ QueryResult to_dict() works!")


def test_different_entity_types():
    """Test UpdateResult with different entity types."""
    
    # Stock data
    stock_result = UpdateResult(
        success=True,
        operation="update_prices",
        affected_count=100,
        entities=["AAPL", "MSFT"],
        entity_type="asset"
    )
    assert stock_result.entity_type == "asset"
    
    # Economic indicators
    econ_result = UpdateResult(
        success=True,
        operation="update_gdp",
        affected_count=12,
        entities=["US_GDP", "EU_GDP"],
        entity_type="indicator"
    )
    assert econ_result.entity_type == "indicator"
    
    # Documents
    doc_result = UpdateResult(
        success=True,
        operation="ingest_pdf",
        affected_count=45,
        entities=["earnings_Q4.pdf"],
        entity_type="document"
    )
    assert doc_result.entity_type == "document"
    
    print("✅ Different entity types work!")
    print(f"   Stock: {stock_result.entity_type}")
    print(f"   Economic: {econ_result.entity_type}")
    print(f"   Document: {doc_result.entity_type}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Testing Response Models")
    print("="*60 + "\n")
    
    test_update_result_basic()
    print()
    
    test_update_result_with_entities()
    print()
    
    test_update_result_to_dict()
    print()
    
    test_update_result_error()
    print()
    
    test_query_result_basic()
    print()
    
    test_query_result_to_dict()
    print()
    
    test_different_entity_types()
    print()
    
    print("="*60)
    print("🎉 All tests passed!")
    print("="*60)