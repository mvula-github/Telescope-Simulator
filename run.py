#!/usr/bin/env python3
"""
Simple run script for the Telescope Simulator
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """Run the telescope simulator"""
    print("*" * 50)
    print("Starting Telescope Simulator...")
    print("*" * 50)
    
    try:
        # Import and run the main application
        from main import main as app_main
        app_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please check that all packages are properly installed.")
        return 1
    except Exception as e:
        print(f"Application error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
