import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # postgresql://user:pass@host:port/dbname

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users_editorial (
                telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
                preferred_language TEXT DEFAULT 'fa',
                instructions TEXT,
                preferred_provider TEXT,
                updated_at TIMESTAMP
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                status TEXT,
                provider TEXT,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
            """)

            def seed(k, envk, default):
                cur.execute("""
                    INSERT INTO settings(key, value) VALUES(%s, %s)
                    ON CONFLICT (key) DO NOTHING
                """, (k, os.getenv(envk, default)))

            seed("rate_limit_seconds", "RATE_LIMIT_SECONDS", "30")
            seed("max_words", "MAX_WORDS", "5000")
            seed("allowed_languages", "ALLOWED_LANGUAGES", "fa,en,ar")
            seed("default_provider", "DEFAULT_PROVIDER", "openai")

def upsert_user(telegram_id: int, full_name: str, username: str, profile_pic_path: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id = %s", (telegram_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO users (telegram_id, full_name, username, profile_pic)
                    VALUES (%s, %s, %s, %s)
                """, (telegram_id, full_name, username, profile_pic_path))

            cur.execute("SELECT telegram_id FROM users_editorial WHERE telegram_id = %s", (telegram_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO users_editorial (telegram_id)
                    VALUES (%s)
                """, (telegram_id,))

def get_user_by_tid(telegram_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.*, ue.preferred_language, ue.instructions, ue.preferred_provider
                FROM users u
                LEFT JOIN users_editorial ue ON u.telegram_id = ue.telegram_id
                WHERE u.telegram_id = %s
            """, (telegram_id,))
            return cur.fetchone()

def set_user_instruction(telegram_id: int, instructions: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users_editorial (telegram_id, instructions, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    instructions = EXCLUDED.instructions,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, instructions))

def set_user_language(telegram_id: int, lang: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users_editorial (telegram_id, preferred_language, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    preferred_language = EXCLUDED.preferred_language,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, lang))

def set_user_provider(telegram_id: int, provider: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users_editorial (telegram_id, preferred_provider, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    preferred_provider = EXCLUDED.preferred_provider,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, provider))

def get_user_provider(telegram_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT preferred_provider FROM users_editorial WHERE telegram_id = %s
            """, (telegram_id,))
            row = cur.fetchone()
            return row["preferred_provider"] if row and row["preferred_provider"] else None

def get_setting(key: str, default: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
            row = cur.fetchone()
            return row["value"] if row and row["value"] is not None else default

def set_setting(key: str, value: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO settings (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """, (key, value))

def enqueue_job(telegram_id: int, provider: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (user_id, status, provider)
                VALUES (%s, 'pending', %s)
                RETURNING id
            """, (telegram_id, provider))
            return cur.fetchone()["id"]

def update_job(job_id: int, **fields):
    with get_conn() as conn:
        with conn.cursor() as cur:
            sets, vals = [], []
            for k, v in fields.items():
                sets.append(f"{k} = %s")
                vals.append(v)
            if "status" in fields and fields["status"] == "done":
                sets.append("completed_at = CURRENT_TIMESTAMP")
            vals.append(job_id)
            query = f"UPDATE jobs SET {', '.join(sets)} WHERE id = %s"
            cur.execute(query, tuple(vals))

def stats_counts():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM users")
            users = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM jobs")
            jobs = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status = 'pending'")
            pending = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status = 'processing'")
            processing = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status = 'done'")
            done = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status = 'error'")
            error = cur.fetchone()["c"]

    return {
        "users": users,
        "jobs": jobs,
        "pending": pending,
        "processing": processing,
        "done": done,
        "error": error,
    }
