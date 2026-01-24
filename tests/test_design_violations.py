"""
Design Violation Detector - Scans codebase for architectural issues

This script checks for common design violations in the multi-agent portfolio system:
- Separation of Concerns violations
- Data guessing/hardcoding
- Business logic in wrong layers
- Asset creation outside DataManager

Run: python tests/test_design_violations.py
"""

import os
import re
import sys
from typing import List, Dict, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class DesignViolation:
    """Represents a design violation found in code"""
    
    def __init__(self, file: str, line_num: int, violation_type: str, description: str, severity: str = "WARNING"):
        self.file = file
        self.line_num = line_num
        self.violation_type = violation_type
        self.description = description
        self.severity = severity  # CRITICAL, WARNING, INFO
    
    def __str__(self):
        return f"{self.severity}: {self.file}:{self.line_num} - {self.violation_type}\n  {self.description}"


class DesignViolationDetector:
    """Scans codebase for design violations"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.violations: List[DesignViolation] = []
    
    def scan_file(self, filepath: str):
        """Scan a single Python file for violations"""
        
        if not filepath.endswith('.py'):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return
        
        rel_path = os.path.relpath(filepath, self.project_root)
        
        for line_num, line in enumerate(lines, 1):
            # Check for various violations
            self._check_asset_creation(rel_path, line_num, line)
            self._check_hardcoded_defaults(rel_path, line_num, line)
            self._check_guessing_patterns(rel_path, line_num, line)
            self._check_llm_doing_math(rel_path, line_num, line)
            self._check_data_fetching_in_wrong_place(rel_path, line_num, line)
    
    def _check_asset_creation(self, filepath: str, line_num: int, line: str):
        """Check for Asset creation outside DataManager"""
        
        if 'Asset(' in line and 'data_manager.py' not in filepath and 'database_setup.py' not in filepath:
            # Check if it's creating an Asset object
            if re.search(r'Asset\s*\(', line):
                self.violations.append(DesignViolation(
                    filepath, line_num,
                    "ASSET_CREATION_VIOLATION",
                    "Asset objects should only be created in DataManager (after fetching real data)",
                    "CRITICAL"
                ))
    
    def _check_hardcoded_defaults(self, filepath: str, line_num: int, line: str):
        """Check for hardcoded asset properties"""
        
        # Check for hardcoded asset_class
        if re.search(r'asset_class\s*=\s*["\']EQUITY["\']', line):
            self.violations.append(DesignViolation(
                filepath, line_num,
                "HARDCODED_ASSET_CLASS",
                "asset_class='EQUITY' is hardcoded - should come from yfinance",
                "CRITICAL"
            ))
        
        if re.search(r'asset_class\s*=\s*["\']UNKNOWN["\']', line):
            self.violations.append(DesignViolation(
                filepath, line_num,
                "UNKNOWN_ASSET_CLASS",
                "asset_class='UNKNOWN' - should fetch real data instead",
                "WARNING"
            ))
        
        # Check for hardcoded currency (less critical)
        if re.search(r'currency\s*=\s*["\']USD["\']', line) and 'portfolio_manager' in filepath:
            self.violations.append(DesignViolation(
                filepath, line_num,
                "HARDCODED_CURRENCY",
                "currency='USD' is assumed - should come from yfinance",
                "INFO"
            ))
    
    def _check_guessing_patterns(self, filepath: str, line_num: int, line: str):
        """Check for code that guesses or assumes data"""
        
        # Check for comments that admit guessing
        if re.search(r'#.*guess|#.*assume|#.*default|#.*placeholder', line, re.IGNORECASE):
            if 'portfolio_manager' in filepath or 'agent' in filepath:
                self.violations.append(DesignViolation(
                    filepath, line_num,
                    "GUESSING_PATTERN",
                    "Code appears to be guessing/assuming data instead of using real data",
                    "WARNING"
                ))
    
    def _check_llm_doing_math(self, filepath: str, line_num: int, line: str):
        """Check for LLMs doing mathematical calculations"""
        
        if 'agent.py' in filepath and not 'data_agent.py' in filepath:
            # Check for math operations in agent files
            if re.search(r'(np\.|scipy\.|optimize|mean|std|cov|sharpe)', line):
                self.violations.append(DesignViolation(
                    filepath, line_num,
                    "LLM_DOING_MATH",
                    "Math/optimization should be in tools, not in agent code",
                    "WARNING"
                ))
    
    def _check_data_fetching_in_wrong_place(self, filepath: str, line_num: int, line: str):
        """Check for data fetching outside DataManager/providers"""
        
        if 'yf.download' in line or 'yf.Ticker' in line:
            if 'yfinance_provider.py' not in filepath and 'data_manager.py' not in filepath:
                self.violations.append(DesignViolation(
                    filepath, line_num,
                    "DATA_FETCHING_VIOLATION",
                    "Direct yfinance calls should only be in yfinance_provider.py",
                    "WARNING"
                ))
    
    def scan_directory(self, directory: str):
        """Recursively scan a directory"""
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.pytest_cache']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.scan_file(filepath)
    
    def report(self) -> Dict[str, int]:
        """Generate report of violations"""
        
        if not self.violations:
            print("\n" + "=" * 80)
            print("✅ NO DESIGN VIOLATIONS FOUND!")
            print("=" * 80)
            print("\nYour codebase follows all design principles:")
            print("  ✓ Separation of Concerns")
            print("  ✓ No guessing or hardcoding")
            print("  ✓ Assets created only in DataManager")
            print("  ✓ Math in tools, not LLMs")
            return {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        
        # Group by severity
        by_severity = {"CRITICAL": [], "WARNING": [], "INFO": []}
        for v in self.violations:
            by_severity[v.severity].append(v)
        
        print("\n" + "=" * 80)
        print("⚠️  DESIGN VIOLATIONS FOUND")
        print("=" * 80)
        
        # Print CRITICAL first
        if by_severity["CRITICAL"]:
            print(f"\n🚨 CRITICAL VIOLATIONS ({len(by_severity['CRITICAL'])})")
            print("=" * 80)
            for v in by_severity["CRITICAL"]:
                print(f"\n{v}")
        
        # Then WARNING
        if by_severity["WARNING"]:
            print(f"\n⚠️  WARNINGS ({len(by_severity['WARNING'])})")
            print("=" * 80)
            for v in by_severity["WARNING"]:
                print(f"\n{v}")
        
        # Then INFO
        if by_severity["INFO"]:
            print(f"\nℹ️  INFO ({len(by_severity['INFO'])})")
            print("=" * 80)
            for v in by_severity["INFO"]:
                print(f"\n{v}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total violations: {len(self.violations)}")
        print(f"  CRITICAL: {len(by_severity['CRITICAL'])}")
        print(f"  WARNING:  {len(by_severity['WARNING'])}")
        print(f"  INFO:     {len(by_severity['INFO'])}")
        
        if by_severity["CRITICAL"]:
            print("\n🚨 CRITICAL violations must be fixed before production!")
        
        return {
            "CRITICAL": len(by_severity["CRITICAL"]),
            "WARNING": len(by_severity["WARNING"]),
            "INFO": len(by_severity["INFO"])
        }


def check_specific_file(filepath: str):
    """Check a specific file for violations"""
    
    print(f"\nScanning {filepath}...")
    
    detector = DesignViolationDetector(os.path.dirname(filepath))
    detector.scan_file(filepath)
    
    return detector.report()


def scan_project(project_root: str):
    """Scan entire project for violations"""
    
    print("\n" + "=" * 80)
    print("🔍 DESIGN VIOLATION DETECTOR")
    print("=" * 80)
    print(f"\nScanning: {project_root}")
    print("\nChecking for:")
    print("  • Asset creation outside DataManager")
    print("  • Hardcoded asset properties (asset_class, currency)")
    print("  • Guessing patterns instead of real data")
    print("  • LLMs doing math (should be in tools)")
    print("  • Data fetching in wrong places")
    
    detector = DesignViolationDetector(project_root)
    
    # Scan important directories
    src_dir = os.path.join(project_root, 'src')
    if os.path.exists(src_dir):
        detector.scan_directory(src_dir)
    
    return detector.report()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check specific file
        filepath = sys.argv[1]
        results = check_specific_file(filepath)
    else:
        # Scan entire project
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results = scan_project(project_root)
    
    # Exit with error code if critical violations found
    if results["CRITICAL"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
