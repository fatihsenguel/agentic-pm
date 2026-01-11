import sys
import os
from sqlalchemy import create_engine, inspect

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from portfolio_tool.database_setup import FinancialStatement, Base, DATABASE_URL

def test_schema_expansion():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Create tables if they don't exist (this updates the schema for new tables, but for existing ones we need to check if columns are there)
    # Note: SQLAlchemy create_all does NOT update existing tables. 
    # However, for this verification, we want to check if the MODEL has the columns, 
    # and if we were to create a fresh DB, it would have them.
    # Since we are modifying an existing file, we should check the SQLAlchemy Inspector on the Model.
    
    inspector = inspect(engine)
    
    # Check if table exists
    if not inspector.has_table("financial_statements"):
        print("Table 'financial_statements' does not exist in DB. Creating it...")
        Base.metadata.create_all(engine)
    
    # Inspect columns in the database
    columns = [c['name'] for c in inspector.get_columns("financial_statements")]
    print(f"Existing columns in DB: {columns}")
    
    expected_columns = [
        'cost_of_revenue',
        'research_and_development',
        'selling_general_and_administrative',
        'interest_expense',
        'income_tax_expense',
        'cash_and_cash_equivalents',
        'accounts_receivable',
        'inventory',
        'property_plant_equipment',
        'accounts_payable',
        'current_debt',
        'long_term_debt',
        'common_stock',
        'retained_earnings',
        'accumulated_other_comprehensive_income',
        'depreciation_and_amortization',
        'stock_based_compensation',
        'change_in_working_capital',
        'capital_expenditure',
        'dividends_paid',
        'issuance_of_debt',
        'repayment_of_debt',
        'issuance_of_stock',
        'repurchase_of_stock'
    ]
    
    missing_columns = [col for col in expected_columns if col not in columns]
    
    if missing_columns:
        print(f"MISSING COLUMNS in DB: {missing_columns}")
        print("NOTE: SQLAlchemy does not automatically add columns to existing tables without Alembic.")
        print("Since this is a dev environment, you might need to delete the DB or use Alembic.")
        print("However, the Python Model `FinancialStatement` should have them.")
        
        # Check Python Model
        model_columns = FinancialStatement.__table__.columns.keys()
        missing_model_columns = [col for col in expected_columns if col not in model_columns]
        
        if not missing_model_columns:
            print("SUCCESS: Python Model `FinancialStatement` has all new columns.")
            print("Action required: Run migration or recreate DB to apply changes to SQLite file.")
        else:
            print(f"FAILURE: Python Model is missing columns: {missing_model_columns}")
    else:
        print("SUCCESS: Database table `financial_statements` has all new columns.")

if __name__ == "__main__":
    test_schema_expansion()
