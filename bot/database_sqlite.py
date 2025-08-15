import sqlite3, os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _resolve_sqlite_path(db_url: str) -> str:
    # expected form: sqlite:///relative/path.db  (absolute also accepted)
    if not db_url.startswith("sqlite:///"):
        rel = "data/users.db"
    else:
        rel = db_url[len("sqlite:///"):]
    if os.path.isabs(rel):
        path = rel
    else:
        path = os.path.join(BASE_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

DB_URL = os.getenv("DB_URL", "sqlite:///data/users.db")
DB_PATH = _resolve_sqlite_path(DB_URL)

def get_conn():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         telegram_id INTEGER UNIQUE,
#         full_name TEXT,
#         username TEXT,
#         preferred_language TEXT DEFAULT 'fa',
#         instructions TEXT,
#         created_at TEXT DEFAULT CURRENT_TIMESTAMP,
#         updated_at TEXT
#     )""")
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS settings (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         key TEXT UNIQUE,
#         value TEXT
#     )""")
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS jobs (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER,
#         status TEXT,
#         provider TEXT,
#         retry_count INTEGER DEFAULT 0,
#         error_message TEXT,
#         created_at TEXT DEFAULT CURRENT_TIMESTAMP,
#         completed_at TEXT,
#         FOREIGN KEY(user_id) REFERENCES users(id)
#     )""")
#     # seed from env once
#     import os as _os
#     def seed(k, envk, default):
#         cur.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?,?)", (k, _os.getenv(envk, default)))
#     seed("rate_limit_seconds","RATE_LIMIT_SECONDS","30")
#     seed("max_words","MAX_WORDS","5000")
#     seed("allowed_languages","ALLOWED_LANGUAGES","fa,en,ar")
#     seed("default_provider","DEFAULT_PROVIDER","openai")
#     conn.commit()
#     conn.close()

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # --- tables ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        full_name TEXT,
        username TEXT,
        preferred_language TEXT DEFAULT 'fa',
        instructions TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT,
        provider TEXT,
        retry_count INTEGER DEFAULT 0,
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # --- migration: add per-user provider if missing ---
    try:
        cur.execute("ALTER TABLE users ADD COLUMN preferred_provider TEXT")
    except Exception:
        # ستون از قبل وجود دارد؛ ایرادی نیست
        pass

    # --- seed settings from env (only if not already present) ---
    import os as _os
    def seed(k, envk, default):
        cur.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)",
            (k, _os.getenv(envk, default)),
        )

    seed("rate_limit_seconds", "RATE_LIMIT_SECONDS", "30")
    seed("max_words", "MAX_WORDS", "5000")
    seed("allowed_languages", "ALLOWED_LANGUAGES", "fa,en,ar")
    seed("default_provider", "DEFAULT_PROVIDER", "openai")

    conn.commit()
    conn.close()


def upsert_user(telegram_id: int, full_name: str, username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET full_name=?, username=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?",
                    (full_name, username, telegram_id))
    else:
        cur.execute("INSERT INTO users(telegram_id, full_name, username) VALUES(?,?,?)",
                    (telegram_id, full_name, username))
    conn.commit()
    conn.close()

def get_user_by_tid(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return row

def set_user_instruction(telegram_id: int, instructions: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET instructions=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?",
                (instructions, telegram_id))
    conn.commit()
    conn.close()

def set_user_language(telegram_id: int, lang: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET preferred_language=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?",
                (lang, telegram_id))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    if row and row["value"] is not None:
        return row["value"]
    return default

def set_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def enqueue_job(user_id: int, provider: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs(user_id, status, provider) VALUES(?, 'pending', ?)", (user_id, provider))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id

def update_job(job_id: int, **fields):
    conn = get_conn()
    cur = conn.cursor()
    sets, vals = [], []
    for k, v in fields.items():
        sets.append(f"{k}=?"); vals.append(v)
    if "status" in fields and fields["status"] == "done":
        sets.append("completed_at=CURRENT_TIMESTAMP")
    query = f"UPDATE jobs SET {', '.join(sets)} WHERE id=?"
    vals.append(job_id)
    cur.execute(query, tuple(vals))
    conn.commit()
    conn.close()

def stats_counts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users"); users = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM jobs"); jobs = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status='pending'"); pend = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status='processing'"); proc = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status='done'"); done = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status='error'"); err = cur.fetchone()["c"]
    conn.close()
    return {"users": users, "jobs": jobs, "pending": pend, "processing": proc, "done": done, "error": err}

def set_user_provider(telegram_id: int, provider: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET preferred_provider=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?",
                (provider, telegram_id))
    conn.commit()
    conn.close()

def get_user_provider(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT preferred_provider FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return row["preferred_provider"] if row and row["preferred_provider"] else None
