import sqlite3
import time
from pathlib import Path
from config import Config

def get_db_connection():
    """Return a database connection with sqlite3.Row for dict-like access."""
    # Ensure database directory exists
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database using schema.sql."""
    schema_path = Path(__file__).resolve().parent / 'schema.sql'
    with get_db_connection() as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()

# ================= USER OPERATIONS =================

def create_user(username, password_hash):
    """Insert a new user. Returns True on success, False if username already exists."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_username(username):
    """Retrieve user record by username."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

# ================= CAPTCHA CHALLENGE OPERATIONS =================

def save_challenge(challenge_id, target_x, created_at=None):
    """Store a generated CAPTCHA challenge in the database."""
    if created_at is None:
        created_at = time.time()
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO captcha_challenges (challenge_id, target_x, created_at, used) VALUES (?, ?, ?, 0)",
            (challenge_id, target_x, created_at)
        )
        conn.commit()

def get_challenge(challenge_id):
    """Fetch challenge record by challenge_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM captcha_challenges WHERE challenge_id = ?", (challenge_id,))
        return cursor.fetchone()

def mark_challenge_used(challenge_id):
    """Mark a challenge as used to prevent Replay Attacks."""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE captcha_challenges SET used = 1 WHERE challenge_id = ?",
            (challenge_id,)
        )
        conn.commit()

def cleanup_old_challenges(ttl_seconds=120):
    """Delete challenges older than TTL to keep database clean."""
    cutoff = time.time() - ttl_seconds
    with get_db_connection() as conn:
        conn.execute("DELETE FROM captcha_challenges WHERE created_at < ?", (cutoff,))
        conn.commit()

# ================= SECURITY AUDIT & LOGGING OPERATIONS =================

def log_security_event(ip_address, user_agent, endpoint, captcha_enabled, captcha_result, status_code, action, bot_type='human'):
    """Record an access/authentication event into security_logs."""
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO security_logs 
            (ip_address, user_agent, endpoint, captcha_enabled, captcha_result, status_code, action, bot_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ip_address,
                user_agent or 'unknown',
                endpoint,
                1 if captcha_enabled else 0,
                captcha_result,
                status_code,
                action,
                bot_type
            )
        )
        conn.commit()

def get_recent_logs(limit=50):
    """Retrieve the most recent security logs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM security_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_log_statistics():
    """Aggregate log data for the Dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) AS total FROM security_logs")
        total_requests = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS passed FROM security_logs WHERE status_code = 200")
        passed_requests = cursor.fetchone()['passed']

        cursor.execute("SELECT COUNT(*) AS blocked FROM security_logs WHERE status_code IN (400, 401, 403, 429)")
        blocked_requests = cursor.fetchone()['blocked']

        # Breakdown by bot_type
        cursor.execute("SELECT bot_type, COUNT(*) AS count FROM security_logs GROUP BY bot_type")
        bot_breakdown = {row['bot_type']: row['count'] for row in cursor.fetchall()}

        # Breakdown by action
        cursor.execute("SELECT action, COUNT(*) AS count FROM security_logs GROUP BY action")
        action_breakdown = {row['action']: row['count'] for row in cursor.fetchall()}

        # Breakdown by captcha result
        cursor.execute("SELECT captcha_result, COUNT(*) AS count FROM security_logs GROUP BY captcha_result")
        captcha_results = {row['captcha_result']: row['count'] for row in cursor.fetchall()}

        return {
            "total_requests": total_requests,
            "passed_requests": passed_requests,
            "blocked_requests": blocked_requests,
            "bot_breakdown": bot_breakdown,
            "action_breakdown": action_breakdown,
            "captcha_results": captcha_results
        }
