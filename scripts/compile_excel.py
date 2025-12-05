#!/usr/bin/env python3
"""
Script to compile Excel files into Python rules

This script pre-compiles Excel calculator files into optimized Python code
for use with the Python engine.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.excel_engine.excel_compiler import ExcelCompilerCLI


def main():
    parser = argparse.ArgumentParser(
        description="Compile Excel calculator files to Python rules"
    )
    parser.add_argument(
        "excel_file",
        help="Path to Excel calculator file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory (defaults to Excel file directory)",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Compile Excel file
        output_file = ExcelCompilerCLI.compile_excel(
            args.excel_file,
            args.output
        )
        
        print(f"✅ Compilation successful!")
        print(f"   Generated: {output_file}")
        print(f"   To use: Copy to common/excel_engine/compiled_rules.py")
        
    except Exception as e:
        print(f"❌ Compilation failed: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())