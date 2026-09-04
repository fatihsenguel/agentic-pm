# tests/conftest.py
"""
Pytest configuration for the test suite.
This file is automatically loaded by pytest.

Two jobs:

1. Put src/ on the Python path so 'from portfolio_tool.xxx import yyy' works.

2. Redirect the whole suite at a throwaway COPY of the database.

   Several tests write: they create portfolios, add holdings and fetch prices.
   Run against data/portfolio.db they mutate real data on every `pytest`, which
   is how a leaked "Integration Test" portfolio ended up in it.

   A copy rather than an empty file, because ~22 tests read cached prices that
   are already in the database. An empty one would refetch every series from
   yfinance: slow, network-dependent, and quota-consuming.

   This must happen before anything imports portfolio_tool, because
   database_setup.py creates its engine at module import from
   config.database.url. conftest.py is loaded before test modules, and
   load_dotenv() runs with override=False, so a value set here beats .env.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add src/ to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# --- Database redirection -------------------------------------------------

_REAL_DB = project_root / "data" / "portfolio.db"

if not _REAL_DB.exists():
    raise RuntimeError(
        f"Test database source not found: {_REAL_DB}\n"
        "\n"
        "The suite runs against a copy of the real database because many tests\n"
        "read cached price data from it. Running against an empty database\n"
        "would silently refetch everything from yfinance.\n"
        "\n"
        "Seed it first:\n"
        "  python src/portfolio_tool/scripts/seed_portfolio.py --reset"
    )

_TMP_DIR = tempfile.mkdtemp(prefix="agentic-pm-tests-")
_TEST_DB = Path(_TMP_DIR) / "portfolio.db"
shutil.copy2(_REAL_DB, _TEST_DB)

# Absolute, so config.resolve_database_url passes it through unchanged.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"


def pytest_sessionfinish(session, exitstatus):
    """Remove the temporary database copy when the run ends."""
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


# Optional: Set environment variables for testing
os.environ.setdefault("USE_MOCK_QUOTA", "True")
