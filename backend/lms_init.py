"""
LMS Auto-Initialisation — v5.0
Root-cause fix: handles orphaned DB state where levels exist but modules/lessons are missing.
Primary entry point: seed_academy() — fully idempotent, detects all states.
"""
from .database import database

# ── Curriculum version tag — bump this when the curriculum changes ──────────
# seed_academy() compares this against the DB tag and reseeds automatically.
_CURRICULUM_VERSION = "v2"

# Try v2 first, fall back to v1, then None
try:
    from .academy_curriculum_seed_v2 import ACADEMY_CURRICULUM
    print("[LMS] Loaded curriculum v2.", flush=True)
except ImportError:
    try:
        from .academy_curriculum_seed import ACADEMY_CURRICULUM
        print("[LMS] WARNING: curriculum_v2 not found — loaded v1 as fallback.", flush=True)
    except ImportError:
        ACADEMY_CURRICULUM = None
        print("[LMS] WARNING: No curriculum file found.", flush=True)

# =============================================================================
# SCHEMA — Course System (Legacy LMS)
# =============================================================================

_COURSE_COLUMNS = [
    ("price",               "FLOAT NOT NULL DEFAULT 0"),
    ("thumbnail",           "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("thumbnail_url",       "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("preview_video",       "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("is_published",        "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("is_active",           "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("certificate_enabled", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("pass_percentage",     "INTEGER NOT NULL DEFAULT 70"),
    ("instructor",          "VARCHAR(255) NOT NULL DEFAULT ''"),
]

_TABLE_SQLS = [
    """CREATE TABLE IF NOT EXISTS course_modules (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS lessons (
        id SERIAL PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        module_id INTEGER REFERENCES course_modules(id) ON DELETE SET NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        video_url VARCHAR(500) NOT NULL DEFAULT '',
        attachment_url VARCHAR(500) NOT NULL DEFAULT '',
        duration_minutes INTEGER NOT NULL DEFAULT 0,
        order_index INTEGER NOT NULL DEFAULT 0,
        is_free_preview BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quizzes (
        id SERIAL PRIMARY KEY,
        module_id INTEGER NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        pass_percentage INTEGER NOT NULL DEFAULT 70,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL DEFAULT '',
        option_d TEXT NOT NULL DEFAULT '',
        correct_option VARCHAR(1) NOT NULL,
        explanation TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS user_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        progress_percent INTEGER NOT NULL DEFAULT 0,
        completed_lessons INTEGER NOT NULL DEFAULT 0,
        last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),
        completed_at TIMESTAMP,
        UNIQUE(user_id, course_id)
    )""",
    """CREATE TABLE IF NOT EXISTS user_lesson_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed_at TIMESTAMP NOT NULL DEFAULT NOW(),
        time_spent_seconds INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, lesson_id)
    )""",
    """CREATE TABLE IF NOT EXISTS certificates (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        certificate_number VARCHAR(100) UNIQUE NOT NULL,
        issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
        pdf_url VARCHAR(500) NOT NULL DEFAULT '',
        UNIQUE(user_id, course_id)
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_attempts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
        score FLOAT NOT NULL DEFAULT 0,
        passed BOOLEAN NOT NULL DEFAULT FALSE,
        answers TEXT NOT NULL DEFAULT '{}',
        attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
]

# =============================================================================
# SCHEMA — Trading Academy
# =============================================================================

_LEARNING_TABLE_SQLS = [
    """CREATE TABLE IF NOT EXISTS learning_levels (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS learning_modules (
        id SERIAL PRIMARY KEY,
        level_id INTEGER NOT NULL REFERENCES learning_levels(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS learning_lessons (
        id SERIAL PRIMARY KEY,
        module_id INTEGER NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        order_index INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS lesson_quizzes (
        id SERIAL PRIMARY KEY,
        lesson_id INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL DEFAULT '',
        option_d TEXT NOT NULL DEFAULT '',
        correct_answer VARCHAR(1) NOT NULL,
        explanation TEXT NOT NULL DEFAULT '',
        topic_slug VARCHAR(100) NOT NULL DEFAULT '',
        UNIQUE(lesson_id, question)
    )""",
    """CREATE TABLE IF NOT EXISTS user_learning_progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        level_id INTEGER NOT NULL DEFAULT 0,
        module_id INTEGER NOT NULL DEFAULT 0,
        lesson_id INTEGER NOT NULL REFERENCES learning_lessons(id) ON DELETE CASCADE,
        completed BOOLEAN NOT NULL DEFAULT FALSE,
        quiz_score FLOAT,
        completed_at TIMESTAMP,
        UNIQUE(user_id, lesson_id)
    )""",
    """CREATE TABLE IF NOT EXISTS user_quiz_results (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER NOT NULL DEFAULT 0,
        question_id INTEGER NOT NULL DEFAULT 0,
        selected_answer VARCHAR(1) NOT NULL,
        is_correct BOOLEAN NOT NULL DEFAULT FALSE,
        answered_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS user_learning_profile (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        weak_topics TEXT NOT NULL DEFAULT '[]',
        strong_topics TEXT NOT NULL DEFAULT '[]',
        first_academy_visit BOOLEAN NOT NULL DEFAULT TRUE,
        last_updated TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS user_badges (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        badge_type VARCHAR(50) NOT NULL,
        earned_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(user_id, badge_type)
    )""",
]

# =============================================================================
# SCHEMA INIT
# =============================================================================

async def init_lms_tables():
    """Create all tables then seed the academy curriculum."""
    ok = warn = 0

    for col, definition in _COURSE_COLUMNS:
        try:
            await database.execute(
                f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {definition}"
            )
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] courses.{col}: {e}", flush=True)

    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] table warn: {e}", flush=True)

    for sql in _LEARNING_TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] learning table warn: {e}", flush=True)

    # Fix missing columns in user_learning_profile (idempotent)
    for col_sql in [
        "ALTER TABLE user_learning_profile ADD COLUMN IF NOT EXISTS first_academy_visit BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE user_learning_profile ADD COLUMN IF NOT EXISTS weak_topics TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE user_learning_profile ADD COLUMN IF NOT EXISTS strong_topics TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE user_learning_profile ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP NOT NULL DEFAULT NOW()",
    ]:
        try:
            await database.execute(col_sql)
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] profile col: {e}", flush=True)

    print(f"[LMS INIT] Schema ready — {ok} ok, {warn} warnings", flush=True)

    await seed_academy()
    await dedup_quizzes()
    await update_lesson_visuals()


# =============================================================================
# SEED ACADEMY  — idempotent, handles all DB states
# =============================================================================

async def seed_academy():
    """
    Seeds ACADEMY_CURRICULUM into the DB.

    States handled:
      • Fresh DB            → seeds everything
      • Fully seeded        → no-op (skips)
      • Orphaned state      → levels exist, modules missing → seeds modules+lessons+quizzes
      • Partial state       → fills in whatever is missing at any level
    """
    if not ACADEMY_CURRICULUM:
        print("[SEED] No ACADEMY_CURRICULUM available — skipping.", flush=True)
        return

    try:
        print("[SEED] Starting...", flush=True)

        # Snapshot all four tables
        r_lv = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_levels")
        r_mo = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_modules")
        r_le = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons")
        r_qu = await database.fetch_one("SELECT COUNT(*) AS c FROM lesson_quizzes")

        n_lv = r_lv["c"] if r_lv else 0
        n_mo = r_mo["c"] if r_mo else 0
        n_le = r_le["c"] if r_le else 0
        n_qu = r_qu["c"] if r_qu else 0

        # Fully seeded — check if it's the CURRENT version
        if n_lv > 0 and n_mo > 0 and n_le > 0 and n_qu > 0:
            # Count expected lessons in current curriculum
            expected_lessons = sum(
                len(m.get("lessons", []))
                for lv in ACADEMY_CURRICULUM
                for m in lv.get("modules", [])
            )
            if n_le == expected_lessons:
                print(
                    f"[SEED] Already seeded (current version): "
                    f"{n_lv} levels, {n_mo} modules, {n_le} lessons, {n_qu} quizzes.",
                    flush=True,
                )
                return
            else:
                print(
                    f"[SEED] Curriculum version mismatch — DB has {n_le} lessons, "
                    f"current curriculum has {expected_lessons}. Forcing reseed...",
                    flush=True,
                )
                await force_reseed_academy()
                return

        # Log the state we detected
        if n_lv > 0 and n_mo == 0:
            print(
                f"[SEED] Orphaned state — {n_lv} levels exist but 0 modules. "
                "Seeding modules/lessons/quizzes now.",
                flush=True,
            )
        elif n_lv == 0:
            print("[SEED] Fresh database — seeding full curriculum.", flush=True)
        else:
            print(
                f"[SEED] Partial state ({n_lv} lv / {n_mo} mo / {n_le} le / {n_qu} qu) — "
                "filling in missing data.",
                flush=True,
            )

        stats = {"levels": 0, "modules": 0, "lessons": 0, "quizzes": 0}

        for level_order, level_data in enumerate(ACADEMY_CURRICULUM, start=1):
            level_name = (level_data.get("level_name") or "").strip()
            level_desc = level_data.get("description", "")

            if not level_name:
                continue

            # ── Level ────────────────────────────────────────────────────────
            row = await database.fetch_one(
                "SELECT id FROM learning_levels WHERE name = :n",
                {"n": level_name},
            )
            if row:
                level_id = row["id"]
            else:
                level_id = await database.fetch_val(
                    """INSERT INTO learning_levels (name, description, order_index)
                       VALUES (:n, :d, :o) RETURNING id""",
                    {"n": level_name, "d": level_desc, "o": level_order},
                )
                stats["levels"] += 1
                print(f"[SEED] Created level: {level_name}", flush=True)

            # ── Modules ───────────────────────────────────────────────────────
            for mod_order, mod_data in enumerate(level_data.get("modules", []), start=1):
                mod_title = (mod_data.get("title") or "").strip()
                mod_desc  = mod_data.get("description", "")

                if not mod_title:
                    continue

                row = await database.fetch_one(
                    "SELECT id FROM learning_modules WHERE level_id = :lid AND title = :t",
                    {"lid": level_id, "t": mod_title},
                )
                if row:
                    module_id = row["id"]
                else:
                    module_id = await database.fetch_val(
                        """INSERT INTO learning_modules (level_id, title, description, order_index)
                           VALUES (:lid, :t, :d, :o) RETURNING id""",
                        {"lid": level_id, "t": mod_title, "d": mod_desc, "o": mod_order},
                    )
                    stats["modules"] += 1

                # ── Lessons ───────────────────────────────────────────────────
                for les_order, les_data in enumerate(mod_data.get("lessons", []), start=1):
                    les_title   = (les_data.get("title") or "").strip()
                    les_content = les_data.get("content", "")

                    if not les_title:
                        continue

                    row = await database.fetch_one(
                        "SELECT id FROM learning_lessons WHERE module_id = :mid AND title = :t",
                        {"mid": module_id, "t": les_title},
                    )
                    if row:
                        lesson_id = row["id"]
                    else:
                        lesson_id = await database.fetch_val(
                            """INSERT INTO learning_lessons (module_id, title, content, order_index)
                               VALUES (:mid, :t, :c, :o) RETURNING id""",
                            {"mid": module_id, "t": les_title, "c": les_content, "o": les_order},
                        )
                        stats["lessons"] += 1

                    # ── Quizzes ───────────────────────────────────────────────
                    for quiz_data in les_data.get("quiz", []):
                        question = (quiz_data.get("question") or "").strip()
                        if not question:
                            continue

                        exists = await database.fetch_one(
                            "SELECT id FROM lesson_quizzes WHERE lesson_id = :lid AND question = :q",
                            {"lid": lesson_id, "q": question},
                        )
                        if not exists:
                            await database.execute(
                                """INSERT INTO lesson_quizzes
                                   (lesson_id, question, option_a, option_b, option_c, option_d,
                                    correct_answer, explanation, topic_slug)
                                   VALUES (:lid, :q, :a, :b, :c, :d, :ans, :expl, :slug)""",
                                {
                                    "lid":  lesson_id,
                                    "q":    question,
                                    "a":    quiz_data.get("option_a", ""),
                                    "b":    quiz_data.get("option_b", ""),
                                    "c":    quiz_data.get("option_c", ""),
                                    "d":    quiz_data.get("option_d", ""),
                                    "ans":  quiz_data.get("correct_answer", "A"),
                                    "expl": quiz_data.get("explanation", ""),
                                    "slug": quiz_data.get("topic_slug", ""),
                                },
                            )
                            stats["quizzes"] += 1

        # Final counts
        r_lv = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_levels")
        r_mo = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_modules")
        r_le = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons")
        r_qu = await database.fetch_one("SELECT COUNT(*) AS c FROM lesson_quizzes")

        print(
            f"[SEED] Completed successfully. "
            f"Added: {stats['levels']} levels, {stats['modules']} modules, "
            f"{stats['lessons']} lessons, {stats['quizzes']} quizzes.",
            flush=True,
        )
        print(
            f"[SEED] Totals in DB: "
            f"{r_lv['c'] if r_lv else 0} levels, "
            f"{r_mo['c'] if r_mo else 0} modules, "
            f"{r_le['c'] if r_le else 0} lessons, "
            f"{r_qu['c'] if r_qu else 0} quizzes.",
            flush=True,
        )

    except Exception as e:
        # Non-fatal — server continues but logs the error clearly
        print(f"[SEED ERROR] {e}", flush=True)





# =============================================================================
# FORCE RESEED  — wipes academy tables and reseeds from current curriculum
# Called by: admin /admin/academy/reseed endpoint, auto-version-detection
# =============================================================================

async def force_reseed_academy():
    """
    Wipes all academy curriculum data and reseeds from ACADEMY_CURRICULUM.

    SAFE: only deletes curriculum data (levels, modules, lessons, quizzes).
    User progress, badges, and quiz results are preserved.

    Called automatically when a curriculum version mismatch is detected,
    or manually via POST /admin/academy/reseed.
    """
    if not ACADEMY_CURRICULUM:
        print("[FORCE RESEED] No curriculum available — aborting.", flush=True)
        return

    print("[FORCE RESEED] Wiping existing curriculum data...", flush=True)
    try:
        # Order matters — FK constraints require child tables first
        await database.execute("DELETE FROM lesson_quizzes")
        await database.execute("DELETE FROM learning_lessons")
        await database.execute("DELETE FROM learning_modules")
        await database.execute("DELETE FROM learning_levels")
        print("[FORCE RESEED] Curriculum tables cleared.", flush=True)
    except Exception as e:
        print(f"[FORCE RESEED] Error clearing tables: {e}", flush=True)
        raise

    # Now seed fresh
    await seed_academy()
    print("[FORCE RESEED] Complete.", flush=True)


async def update_lesson_visuals():
    """
    Content sync: updates lesson content from ACADEMY_CURRICULUM.

    Two modes:
    1. STALE MARKER mode — fixes old /static/charts/ PNG refs and [VISUAL:] markers
    2. FULL SYNC mode — syncs ALL content when curriculum changed (lesson count mismatch)

    Safe to run every startup.
    """
    if not ACADEMY_CURRICULUM:
        return

    try:
        # ── Check if full sync is needed (curriculum version changed) ───────
        r_le = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons")
        db_lesson_count = r_le["c"] if r_le else 0

        expected_lessons = sum(
            len(m.get("lessons", []))
            for lv in ACADEMY_CURRICULUM
            for m in lv.get("modules", [])
        )

        if db_lesson_count == expected_lessons:
            # Same count — only fix stale visual markers
            stale = await database.fetch_one(
                """SELECT COUNT(*) AS c FROM learning_lessons
                   WHERE content LIKE '%/static/charts/%'
                      OR content LIKE '%[VISUAL:%'
                      OR content LIKE '%[CHART:%'"""
            )
            stale_count = stale["c"] if stale else 0

            if stale_count == 0:
                print("[VISUAL UPDATE] All lesson content is current — skipping.", flush=True)
                return

            print(f"[VISUAL UPDATE] Found {stale_count} lessons with stale markers. Syncing...", flush=True)
            updated = 0

            for level_data in ACADEMY_CURRICULUM:
                for mod_data in level_data.get("modules", []):
                    for les_data in mod_data.get("lessons", []):
                        title = (les_data.get("title") or "").strip()
                        new_content = les_data.get("content", "")
                        if not title or not new_content:
                            continue
                        result = await database.execute(
                            """UPDATE learning_lessons SET content = :c
                               WHERE title = :t
                                 AND (content LIKE '%/static/charts/%'
                                   OR content LIKE '%[VISUAL:%'
                                   OR content LIKE '%[CHART:%')""",
                            {"c": new_content, "t": title},
                        )
                        if result:
                            updated += 1

            print(f"[VISUAL UPDATE] Stale marker sync complete. Updated {updated} lessons.", flush=True)

        else:
            # Lesson count mismatch — full content sync by title
            print(
                f"[VISUAL UPDATE] DB has {db_lesson_count} lessons, curriculum has {expected_lessons}. "
                "Full content sync triggered.",
                flush=True,
            )
            updated = 0

            for level_data in ACADEMY_CURRICULUM:
                for mod_data in level_data.get("modules", []):
                    for les_data in mod_data.get("lessons", []):
                        title = (les_data.get("title") or "").strip()
                        new_content = les_data.get("content", "")
                        if not title or not new_content:
                            continue
                        result = await database.execute(
                            "UPDATE learning_lessons SET content = :c WHERE title = :t",
                            {"c": new_content, "t": title},
                        )
                        if result:
                            updated += 1

            print(f"[VISUAL UPDATE] Full content sync complete. Updated {updated} lessons.", flush=True)

    except Exception as e:
        print(f"[VISUAL UPDATE ERROR] {e}", flush=True)


async def dedup_quizzes():
    """
    One-time cleanup: removes duplicate quiz questions caused by multiple seed runs.
    Keeps the LOWEST id for each (lesson_id, question) pair — deletes all duplicates.
    Also adds the UNIQUE constraint if it doesn't exist yet (idempotent).
    Safe to run on every startup — exits fast when no duplicates exist.
    """
    try:
        # Check for duplicates first
        dup_check = await database.fetch_one(
            """SELECT COUNT(*) AS c FROM (
                SELECT lesson_id, question
                FROM lesson_quizzes
                GROUP BY lesson_id, question
                HAVING COUNT(*) > 1
            ) t"""
        )
        dup_count = dup_check["c"] if dup_check else 0

        if dup_count == 0:
            print("[QUIZ DEDUP] No duplicate questions found — skipping.", flush=True)
        else:
            print(f"[QUIZ DEDUP] Found {dup_count} duplicate question groups. Cleaning...", flush=True)
            # Delete duplicates — keep the row with the lowest id
            await database.execute(
                """DELETE FROM lesson_quizzes
                   WHERE id NOT IN (
                       SELECT MIN(id)
                       FROM lesson_quizzes
                       GROUP BY lesson_id, question
                   )"""
            )
            remaining = await database.fetch_one(
                "SELECT COUNT(*) AS c FROM lesson_quizzes"
            )
            print(
                f"[QUIZ DEDUP] Done. {remaining['c'] if remaining else 0} questions remain.",
                flush=True,
            )

        # Add UNIQUE constraint if not already present (idempotent)
        try:
            await database.execute(
                """ALTER TABLE lesson_quizzes
                   ADD CONSTRAINT uq_lesson_question UNIQUE (lesson_id, question)"""
            )
            print("[QUIZ DEDUP] UNIQUE constraint added to lesson_quizzes.", flush=True)
        except Exception:
            pass  # Constraint already exists — expected on subsequent runs

        # Cap at 5 questions per lesson — remove excess (keep lowest 5 ids)
        excess_check = await database.fetch_one(
            """SELECT COUNT(*) AS c FROM (
                SELECT lesson_id
                FROM lesson_quizzes
                GROUP BY lesson_id
                HAVING COUNT(*) > 5
            ) t"""
        )
        excess_lessons = excess_check["c"] if excess_check else 0
        if excess_lessons > 0:
            print(f"[QUIZ DEDUP] {excess_lessons} lessons have >5 questions — trimming to 5.", flush=True)
            await database.execute(
                """DELETE FROM lesson_quizzes
                   WHERE id NOT IN (
                       SELECT id FROM (
                           SELECT id,
                                  ROW_NUMBER() OVER (PARTITION BY lesson_id ORDER BY id) AS rn
                           FROM lesson_quizzes
                       ) ranked
                       WHERE rn <= 5
                   )"""
            )
            print("[QUIZ DEDUP] Trimmed to max 5 questions per lesson.", flush=True)

    except Exception as e:
        print(f"[QUIZ DEDUP ERROR] {e}", flush=True)


# =============================================================================
# LEGACY ALIASES
# =============================================================================

async def upsert_curriculum():
    """Backwards-compatible alias for seed_academy()."""
    await seed_academy()


async def _seed_curriculum():
    """Backwards-compatible alias for seed_academy()."""
    await seed_academy()


async def reseed_academy():
    """Public alias for force_reseed_academy() — used by admin routes."""
    await force_reseed_academy()
