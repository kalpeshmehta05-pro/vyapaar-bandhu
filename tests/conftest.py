"""
Test configuration -- add backend to sys.path so `app` imports work.
"""

import sys
from pathlib import Path

# Add backend directory to path so `from app.xxx` imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
