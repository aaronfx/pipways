"""
Pipways Backend Package
"""
import sys

# Debug logging for Render deployment troubleshooting
print(f"[INIT] Backend package loaded", flush=True)
print(f"[INIT] Backend location: {__file__}", flush=True)

__version__ = "2.0.0"

# DO NOT import submodules here - causes circular imports when main.py imports them
# All modules are imported directly by main.py to avoid initialization loops
# This is especially important for: ai_mentor, chart_analysis, performance_analyzer
