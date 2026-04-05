#!/usr/bin/env python
"""Run the Flask application"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tranotra.main import create_app
from tranotra.config import load_config

if __name__ == "__main__":
    app = create_app()
    config = load_config()

    app.run(
        host=config["FLASK_HOST"],
        port=config["FLASK_PORT"],
        debug=config.get("FLASK_DEBUG", False)
    )
