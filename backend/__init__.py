"""
Pipways Backend Package
"""
import sys

# Debug logging for Render deployment troubleshooting
print(f"[INIT] Backend package loaded", flush=True)
print(f"[INIT] Python path: {sys.path[:3]}...", flush=True)
print(f"[INIT] Backend location: {__file__}", flush=True)

__version__ = "1.0.0"

# Import all submodules for easy access
from backend import (
    auth,
    security,
    database,
    signals,
    courses,
    blog,
    webinars,
    media,
    admin,
    notifications,
    payments,
    risk_calculator,
    ai_screening,
    blog_enhanced,
    courses_enhanced,
)
