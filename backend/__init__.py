"""
Pipways Backend Package
"""
import sys

# Debug logging for Render deployment troubleshooting
print(f"[INIT] Backend package loaded", flush=True)
print(f"[INIT] Backend location: {__file__}", flush=True)

__version__ = "2.0.0"

# Import all submodules for easy access
from . import (
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
    ai_mentor,
    chart_analysis,
    performance_analyzer,
    blog_enhanced,
    courses_enhanced,
)
