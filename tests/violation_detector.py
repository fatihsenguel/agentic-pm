# violation_detector.py
"""
Detect DRY and SoC violations in the codebase.

This script finds:
1. Duplicate constants
2. Hardcoded configuration values
3. Config classes that should be in config.py
4. Multiple definitions of the same value

Run: python violation_detector.py
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Patterns to look for
VIOLATION_PATTERNS = {
    "duplicate_constants": {
        "pattern": r"^([A-Z_]+)\s*=\s*(.+)$",
        "description": "Module-level constants (should be in config.py)",
        "severity": "HIGH"
    },
    "config_classes": {
        "pattern": r"class\s+(\w+Config)\(.*\):",
        "description": "Config classes (should be in config.py)",
        "severity": "HIGH"
    },
    "hardcoded_periods": {
        "pattern": r'(period|default_period)\s*[:=]\s*["\'](\d+[YMD])["\']',
        "description": "Hardcoded time periods",
        "severity": "MEDIUM"
    },
    "hardcoded_rates": {
        "pattern": r'(rate|threshold)\s*[:=]\s*(0\.\d+)',
        "description": "Hardcoded rates/thresholds",
        "severity": "MEDIUM"
    },
    "magic_numbers": {
        "pattern": r'\b(252|365|12|30)\b(?!\s*#)',
        "description": "Magic numbers (252=trading days, 365=days/year, etc.)",
        "severity": "LOW"
    },
}

class ViolationDetector:
    """Detect configuration and DRY violations."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.violations = defaultdict(list)
        self.constants = defaultdict(list)  # Track duplicate definitions
        
    def scan_file(self, filepath: Path):
        """Scan a single file for violations."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return
        
        rel_path = filepath.relative_to(self.project_root)
        
        # Skip config.py itself
        if "config.py" in str(filepath):
            return
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Check each pattern
            for violation_type, pattern_info in VIOLATION_PATTERNS.items():
                pattern = pattern_info["pattern"]
                matches = re.findall(pattern, line)
                
                if matches:
                    for match in matches:
                        self.violations[violation_type].append({
                            "file": str(rel_path),
                            "line": line_num,
                            "content": line,
                            "match": match,
                            "severity": pattern_info["severity"]
                        })
                        
                        # Track duplicate constants
                        if violation_type == "duplicate_constants":
                            const_name = match[0] if isinstance(match, tuple) else match
                            self.constants[const_name].append({
                                "file": str(rel_path),
                                "line": line_num,
                                "value": match[1] if isinstance(match, tuple) else None
                            })
    
    def scan_directory(self, directory: Path = None):
        """Scan all Python files in directory."""
        if directory is None:
            directory = self.project_root
        
        print(f"Scanning {directory}...")
        
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__, venv, etc.
            if any(skip in str(py_file) for skip in ["__pycache__", "venv", ".venv", "env"]):
                continue
            
            self.scan_file(py_file)
    
    def find_duplicates(self) -> Dict[str, List]:
        """Find constants defined in multiple places."""
        duplicates = {}
        for const_name, locations in self.constants.items():
            if len(locations) > 1:
                duplicates[const_name] = locations
        return duplicates
    
    def print_report(self):
        """Print a formatted report of all violations."""
        print("\n" + "="*80)
        print("CONFIGURATION VIOLATION REPORT")
        print("="*80)
        
        # 1. Duplicate Constants (CRITICAL)
        duplicates = self.find_duplicates()
        if duplicates:
            print("\n🔴 CRITICAL: DUPLICATE CONSTANTS")
            print("-" * 80)
            for const_name, locations in sorted(duplicates.items()):
                print(f"\n'{const_name}' defined in {len(locations)} places:")
                for loc in locations:
                    value = loc.get('value', 'N/A')
                    print(f"  • {loc['file']}:{loc['line']} = {value}")
                print(f"  ⚠️  FIX: Move to config.py as config.data.{const_name.lower()}")
        
        # 2. Config Classes
        config_classes = self.violations.get("config_classes", [])
        if config_classes:
            print("\n🟠 HIGH: CONFIG CLASSES (Should be in config.py)")
            print("-" * 80)
            by_file = defaultdict(list)
            for v in config_classes:
                by_file[v["file"]].append(v)
            
            for file, violations in sorted(by_file.items()):
                print(f"\n{file}:")
                for v in violations:
                    class_name = v["match"]
                    print(f"  Line {v['line']}: {class_name}")
                print(f"  ⚠️  FIX: Move configuration to config.py")
        
        # 3. Hardcoded Values
        for violation_type in ["hardcoded_periods", "hardcoded_rates"]:
            violations_list = self.violations.get(violation_type, [])
            if violations_list:
                severity = VIOLATION_PATTERNS[violation_type]["severity"]
                description = VIOLATION_PATTERNS[violation_type]["description"]
                
                print(f"\n🟡 {severity}: {description.upper()}")
                print("-" * 80)
                
                by_file = defaultdict(list)
                for v in violations_list:
                    by_file[v["file"]].append(v)
                
                for file, viols in sorted(by_file.items())[:5]:  # Show top 5 files
                    print(f"\n{file}:")
                    for v in viols[:3]:  # Show top 3 per file
                        print(f"  Line {v['line']}: {v['content'][:70]}")
                
                if len(by_file) > 5:
                    print(f"\n  ... and {len(by_file) - 5} more files")
        
        # 4. Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        total_duplicates = len(duplicates)
        total_config_classes = len(config_classes)
        total_hardcoded = sum(
            len(self.violations.get(vt, [])) 
            for vt in ["hardcoded_periods", "hardcoded_rates"]
        )
        
        print(f"Duplicate Constants: {total_duplicates}")
        print(f"Config Classes: {total_config_classes}")
        print(f"Hardcoded Values: {total_hardcoded}")
        
        print("\n📋 RECOMMENDED ACTIONS:")
        print("1. Move all constants to config.py")
        print("2. Delete XxxConfig classes from individual agent files")
        print("3. Replace hardcoded values with config.data.X references")
        print("4. Run this script again to verify fixes")
        
        print("\n" + "="*80)


def main():
    """Run the violation detector."""
    import sys
    
    # Get project root from command line or use current directory
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    detector = ViolationDetector(project_root)
    
    # Scan src/agents directory
    agents_dir = Path(project_root) / "src" / "agents"
    if agents_dir.exists():
        detector.scan_directory(agents_dir)
    else:
        print(f"Warning: {agents_dir} not found, scanning entire project...")
        detector.scan_directory()
    
    # Print report
    detector.print_report()
    
    # Save detailed report to file
    report_file = Path(project_root) / "violation_report.txt"
    import sys
    original_stdout = sys.stdout
    with open(report_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        detector.print_report()
    sys.stdout = original_stdout
    
    print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
