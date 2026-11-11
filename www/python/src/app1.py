"""
# isort:skip_file
WSGI development entry point for the app.
"""

from __future__ import annotations
import sys
import os
import logging
import pymysql
from pathlib import Path

from dotenv import load_dotenv

os.environ["FLASK_ENV"] = "development"

sys.path.insert(0, str(Path(__file__).parent))
pymysql.install_as_MySQLdb()

# Load environment variables before any other imports

_env_file_path = str(Path(__file__).parent.parent.parent / ".env")
try:
    load_dotenv(_env_file_path)
except Exception:
    logging.warning(f"Failed to load .env file from {str(_env_file_path)}")

# import app here
from main_app import AppFactory  # noqa: E402

app = AppFactory.create()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
