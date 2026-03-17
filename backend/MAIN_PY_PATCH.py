# ══════════════════════════════════════════════════════════════════════════════
#  MAIN.PY — TWO ADDITIONS REQUIRED
#  Add these exactly as shown.  No other changes needed.
# ══════════════════════════════════════════════════════════════════════════════

# ── ADDITION 1 ─────────────────────────────────────────────────────────────
# In the "Import all routers" block (around line 20 in main.py),
# add this line alongside the other module imports:

from . import learning           # ← ADD THIS LINE

# ── ADDITION 2 ─────────────────────────────────────────────────────────────
# In the "API ROUTES" block (around line 160 in main.py),
# add this line alongside the other app.include_router(...) calls:

app.include_router(learning.router, prefix="/learning", tags=["Learning"])  # ← ADD THIS LINE


# ══════════════════════════════════════════════════════════════════════════════
#  lms_init.py is already wired via the existing stub:
#
#      try:
#          from .lms_init import init_lms_tables
#          _HAS_LMS_INIT = True
#      except ImportError:
#          _HAS_LMS_INIT = False
#          async def init_lms_tables():
#              print("[LMS INIT] lms_init.py not found — skipping")
#
#  As long as lms_init.py is in the backend package directory, it will be
#  picked up automatically on the next restart — no main.py change needed.
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  FILE PLACEMENT CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════
#
#  Backend directory (same folder as main.py, database.py, auth.py, etc.):
#    ✓  lms_init.py       ← database tables + curriculum seed
#    ✓  learning.py       ← FastAPI router with all /learning/* endpoints
#
#  Frontend directory (js/modules/):
#    ✓  academy.js        ← SPA module loaded by dashboard.html
#
#  dashboard.html: already patched — deploy the updated dashboard.html
#
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  QUICK DIAGNOSTIC — run this in your browser console after deploying
# ══════════════════════════════════════════════════════════════════════════════
#
#  fetch('/learning/health')
#      .then(r => r.json())
#      .then(d => console.table(d.tables))
#
#  Expected output when working:
#    learning_levels           3
#    learning_modules          4
#    learning_lessons          7
#    lesson_quizzes           20
#    user_learning_progress    0   (empty until users complete lessons)
#    user_quiz_results         0
#    user_learning_profile     0
#
#  If learning_levels shows 0, call the seed endpoint:
#    fetch('/learning/admin/seed', {
#        method: 'POST',
#        headers: { Authorization: 'Bearer ' + localStorage.getItem('pipways_token') }
#    }).then(r => r.json()).then(console.log)
#
# ══════════════════════════════════════════════════════════════════════════════
