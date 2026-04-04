#!/usr/bin/env python3
"""
Tranotra Leads - Application Launcher

This script starts the Flask application.
Usage: python run.py
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import tranotra module
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and create app using factory
from tranotra.main import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TRANOTRA LEADS - PHASE 1")
    print("="*60)
    print("[INFO] Starting Flask application...")
    print("[INFO] Visit: http://localhost:5000")
    print("="*60 + "\n")

    app.run(debug=True, host='localhost', port=5000)
