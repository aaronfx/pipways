"""
LMS Auto-Initialisation — Refactored v4.0
Separates curriculum content from initialization logic.
Imports ACADEMY_CURRICULUM from academy_curriculum_seed if available.
"""
from .database import database

# Optional: Import curriculum from external seed file
try:
    from .academy_curriculum_seed import ACADEMY_CURRICULUM
except ImportError:
    ACADEMY_CURRICULUM = None

# =============================================================================
# SCHEMA DEFINITIONS — Course System (Legacy LMS)
# =============================================================================

_COURSE_COLUMNS = [
    ("price", "FLOAT NOT NULL DEFAULT 0"),
    ("thumbnail", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("thumbnail_url", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("preview_video", "VARCHAR(500) NOT NULL DEFAULT ''"),
    ("is_published", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("certificate_enabled", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("pass_percentage", "INTEGER NOT NULL DEFAULT 70"),
    ("instructor", "VARCHAR(255) NOT NULL DEFAULT ''"),
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
# SCHEMA DEFINITIONS — Trading Academy System
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
        topic_slug VARCHAR(100) NOT NULL DEFAULT ''
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
# INITIALIZATION
# =============================================================================

async def init_lms_tables():
    """
    Create all LMS and Academy tables if they don't exist.
    Then safely seed curriculum from ACADEMY_CURRICULUM if provided.
    """
    ok = warn = 0

    # Add course columns (idempotent)
    for col, definition in _COURSE_COLUMNS:
        sql = f"ALTER TABLE courses ADD COLUMN IF NOT EXISTS {col} {definition}"
        try:
            await database.execute(sql)
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] courses.{col}: {e}", flush=True)

    # Create legacy LMS tables
    for sql in _TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] table warn: {e}", flush=True)

    # Create Academy tables
    for sql in _LEARNING_TABLE_SQLS:
        try:
            await database.execute(sql.strip())
            ok += 1
        except Exception as e:
            warn += 1
            print(f"[LMS INIT] learning table warn: {e}", flush=True)

    print(f"[LMS INIT] Schema ready — {ok} ok, {warn} warnings", flush=True)

    # Seed curriculum if available
    if ACADEMY_CURRICULUM:
        await upsert_curriculum()
    else:
        print("[LMS INIT] No ACADEMY_CURRICULUM found. Skipping seed.", flush=True)


async def upsert_curriculum():
    """
    Idempotent curriculum seeding from ACADEMY_CURRICULUM structure.
    Hierarchical: Level → Module → Lesson → Quiz
    Prevents duplicates by checking existing records.
    """
    try:
        # Check if curriculum already exists
        count = await database.fetch_one("SELECT COUNT(*) as c FROM learning_levels")
        if count and count['c'] > 0:
            print(f"[LMS UPSERT] Curriculum exists ({count['c']} levels). Checking for new content...", flush=True)
        
        stats = {"levels": 0, "modules": 0, "lessons": 0, "quizzes": 0}
        
        # Process each level
        for level_order, level_data in enumerate(ACADEMY_CURRICULUM, start=1):
            level_name = level_data.get("level_name")
            level_desc = level_data.get("description", "")
            
            # Check if level exists
            existing_level = await database.fetch_one(
                "SELECT id FROM learning_levels WHERE name = :name",
                {"name": level_name}
            )
            
            if existing_level:
                level_id = existing_level["id"]
            else:
                level_id = await database.fetch_val(
                    """INSERT INTO learning_levels (name, description, order_index) 
                       VALUES (:name, :desc, :order) RETURNING id""",
                    {"name": level_name, "desc": level_desc, "order": level_order}
                )
                stats["levels"] += 1
                print(f"[LMS UPSERT] Created level: {level_name}", flush=True)
            
            # Process modules
            modules = level_data.get("modules", [])
            for module_order, module_data in enumerate(modules, start=1):
                module_title = module_data.get("title")
                module_desc = module_data.get("description", "")
                
                # Check if module exists
                existing_module = await database.fetch_one(
                    "SELECT id FROM learning_modules WHERE level_id = :lid AND title = :title",
                    {"lid": level_id, "title": module_title}
                )
                
                if existing_module:
                    module_id = existing_module["id"]
                else:
                    module_id = await database.fetch_val(
                        """INSERT INTO learning_modules (level_id, title, description, order_index)
                           VALUES (:lid, :title, :desc, :order) RETURNING id""",
                        {"lid": level_id, "title": module_title, "desc": module_desc, "order": module_order}
                    )
                    stats["modules"] += 1
                
                # Process lessons
                lessons = module_data.get("lessons", [])
                for lesson_order, lesson_data in enumerate(lessons, start=1):
                    lesson_title = lesson_data.get("title")
                    lesson_content = lesson_data.get("content", "")
                    
                    # Check if lesson exists
                    existing_lesson = await database.fetch_one(
                        "SELECT id FROM learning_lessons WHERE module_id = :mid AND title = :title",
                        {"mid": module_id, "title": lesson_title}
                    )
                    
                    if existing_lesson:
                        lesson_id = existing_lesson["id"]
                    else:
                        lesson_id = await database.fetch_val(
                            """INSERT INTO learning_lessons (module_id, title, content, order_index)
                               VALUES (:mid, :title, :content, :order) RETURNING id""",
                            {
                                "mid": module_id, 
                                "title": lesson_title, 
                                "content": lesson_content, 
                                "order": lesson_order
                            }
                        )
                        stats["lessons"] += 1
                    
                    # Process quizzes (up to 5 per lesson)
                    quizzes = lesson_data.get("quiz", [])
                    for quiz_data in quizzes:
                        question = quiz_data.get("question")
                        
                        # Check if this exact question exists
                        existing_quiz = await database.fetch_one(
                            "SELECT id FROM lesson_quizzes WHERE lesson_id = :lid AND question = :q",
                            {"lid": lesson_id, "q": question}
                        )
                        
                        if not existing_quiz:
                            await database.execute(
                                """INSERT INTO lesson_quizzes 
                                   (lesson_id, question, option_a, option_b, option_c, option_d, 
                                    correct_answer, explanation, topic_slug)
                                   VALUES (:lid, :q, :a, :b, :c, :d, :correct, :expl, :slug)""",
                                {
                                    "lid": lesson_id,
                                    "q": question,
                                    "a": quiz_data.get("option_a", ""),
                                    "b": quiz_data.get("option_b", ""),
                                    "c": quiz_data.get("option_c", ""),
                                    "d": quiz_data.get("option_d", ""),
                                    "correct": quiz_data.get("correct_answer"),
                                    "expl": quiz_data.get("explanation", ""),
                                    "slug": quiz_data.get("topic_slug", "")
                                }
                            )
                            stats["quizzes"] += 1
        
        # Summary
        total_levels = await database.fetch_one("SELECT COUNT(*) as c FROM learning_levels")
        total_modules = await database.fetch_one("SELECT COUNT(*) as c FROM learning_modules")
        total_lessons = await database.fetch_one("SELECT COUNT(*) as c FROM learning_lessons")
        total_quizzes = await database.fetch_one("SELECT COUNT(*) as c FROM lesson_quizzes")
        
        print(f"[LMS UPSERT] Complete. Added: {stats['levels']} levels, {stats['modules']} modules, "
              f"{stats['lessons']} lessons, {stats['quizzes']} quizzes.", flush=True)
        print(f"[LMS UPSERT] Totals: {total_levels['c']} levels, {total_modules['c']} modules, "
              f"{total_lessons['c']} lessons, {total_quizzes['c']} quizzes.", flush=True)
              
    except Exception as e:
        print(f"[LMS UPSERT] Error: {e}", flush=True)
        raise


# Legacy wrapper for backwards compatibility
async def _seed_curriculum():
    """Legacy entry point — now handled by upsert_curriculum"""
    if ACADEMY_CURRICULUM:
        await upsert_curriculum()
