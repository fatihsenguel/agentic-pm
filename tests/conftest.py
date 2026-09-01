# tests/conftest.py
"""
Pytest configuration for the test suite.
This file is automatically loaded by pytest.

It ensures that the src/ directory is in the Python path,
so imports like 'from portfolio_tool.xxx import yyy' work correctly.
"""

import sys
from pathlib import Path

# Add src/ to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Optional: Set environment variables for testing
import os
os.environ.setdefault("USE_MOCK_QUOTA", "True")