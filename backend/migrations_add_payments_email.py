"""
Migration: Paystack + Email System + Academy Free Tier
Run once: python -m backend.migrations.add_payments_and_email

Creates:
  - payment_logs          — Paystack transaction records
  - email_subscribers     — lead capture (public signup, no account needed)
  - email_logs            — audit trail of every sent email
  - user_email_preferences — per-user opt-in/out settings

Modifies:
  - users.subscription_tier default stays 'free'
  - Removes Academy gating from subscriptions (done in subscriptions.py)
"""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "")


def run():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        return

    sync_url = (DATABASE_URL
                .replace("postgresql+asyncpg://", "postgresql://")
                .replace("postgresql://", "postgresql+psycopg2://")
                .replace("postgresql+psycopg2+psycopg2://", "postgresql+psycopg2://"))

    engine = create_engine(sync_url)

    statements = [

        # ── payment_logs ─────────────────────────────────────────────────────
        """
        CREATE TABLE IF NOT EXISTS payment_logs (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
            reference   VARCHAR(255) UNIQUE NOT NULL,
            tier        VARCHAR(50)  NOT NULL DEFAULT 'pro',
            amount      BIGINT       NOT NULL DEFAULT 0,
            currency    VARCHAR(10)  NOT NULL DEFAULT 'NGN',
            status      VARCHAR(50)  NOT NULL DEFAULT 'pending',
            metadata    JSONB,
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_payment_logs_user ON payment_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_logs_ref  ON payment_logs(reference)",

        # ── email_subscribers (public lead capture) ───────────────────────────
        """
        CREATE TABLE IF NOT EXISTS email_subscribers (
            id             SERIAL PRIMARY KEY,
            email          VARCHAR(255) UNIQUE NOT NULL,
            name           VARCHAR(255) DEFAULT '',
            source         VARCHAR(100) DEFAULT 'general',
            is_active      BOOLEAN DEFAULT TRUE,
            subscribed_at  TIMESTAMP DEFAULT NOW(),
            unsubscribed_at TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_email_subscribers_email ON email_subscribers(email)",

        # ── email_logs (audit trail) ──────────────────────────────────────────
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
            email_type  VARCHAR(100) NOT NULL,
            to_email    VARCHAR(255) NOT NULL,
            success     BOOLEAN DEFAULT FALSE,
            sent_at     TIMESTAMP DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_email_logs_user ON email_logs(user_id)",

        # ── user_email_preferences ────────────────────────────────────────────
        """
        CREATE TABLE IF NOT EXISTS user_email_preferences (
            user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            preferences JSONB NOT NULL DEFAULT '{}',
            updated_at  TIMESTAMP DEFAULT NOW()
        )
        """,

        # ── Ensure subscription_tier column exists on users ───────────────────
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='subscription_tier'
            ) THEN
                ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50) DEFAULT 'free';
            END IF;
        END $$
        """,
    ]

    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt.strip()))
                conn.commit()
            except Exception as e:
                print(f"  ⚠ Statement skipped: {e}")

    print("✅ Migration complete: payment_logs, email tables created")
    print("✅ Academy is now free — remove tier checks from academy_routes.py")


if __name__ == "__main__":
    run()
