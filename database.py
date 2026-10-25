# ============================================================
#  AI Job Radar — database.py
#  Stores every job we've already seen so we never alert twice
# ============================================================

import sqlite3
import hashlib
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create the tables if they don't exist yet."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id          TEXT PRIMARY KEY,   -- unique hash of company+title+link
                company     TEXT NOT NULL,
                title       TEXT NOT NULL,
                location    TEXT,
                link        TEXT,
                salary      TEXT,
                posted_at   TEXT,
                found_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS run_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                jobs_found INTEGER DEFAULT 0,
                jobs_new   INTEGER DEFAULT 0,
                status     TEXT
            )
        """)
        conn.commit()


def make_job_id(company: str, title: str, link: str) -> str:
    """Create a unique ID for a job so we can detect duplicates."""
    raw = f"{company.lower()}|{title.lower()}|{link.lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_new_job(job_id: str) -> bool:
    """Return True if this job hasn't been seen before."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM seen_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    return row is None


def save_job(job: dict):
    """Save a job to the database so it won't alert again."""
    job_id = make_job_id(job["company"], job["title"], job.get("link", ""))
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO seen_jobs
                (id, company, title, location, link, salary, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            job.get("company", ""),
            job.get("title", ""),
            job.get("location", ""),
            job.get("link", ""),
            job.get("salary", ""),
            job.get("posted_at", ""),
        ))
        conn.commit()


def log_run(jobs_found: int, jobs_new: int, status: str = "success"):
    """Log each run for debugging."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO run_log (jobs_found, jobs_new, status)
            VALUES (?, ?, ?)
        """, (jobs_found, jobs_new, status))
        conn.commit()


def get_recent_jobs(limit: int = 20) -> list:
    """Return the most recently found jobs (for dashboard/debug)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT company, title, location, link, salary, found_at
            FROM seen_jobs
            ORDER BY found_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [
        {
            "company": r[0], "title": r[1], "location": r[2],
            "link": r[3], "salary": r[4], "found_at": r[5]
        }
        for r in rows
    ]
