import sqlite3
from database.db import get_db_connection

def get_comparative_analytics():
    """
    Compute defense metrics comparing when CAPTCHA was ON vs OFF.
    Crucial for presenting the empirical effectiveness of the Defense-in-Depth layer.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Traffic when CAPTCHA was ON (captcha_enabled = 1)
        cursor.execute("SELECT COUNT(*) AS total FROM security_logs WHERE captcha_enabled = 1")
        on_total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS passed FROM security_logs WHERE captcha_enabled = 1 AND status_code = 200")
        on_passed = cursor.fetchone()['passed']

        cursor.execute("SELECT COUNT(*) AS blocked FROM security_logs WHERE captcha_enabled = 1 AND status_code IN (400, 401, 403, 429)")
        on_blocked = cursor.fetchone()['blocked']

        on_block_rate = round((on_blocked / on_total * 100), 1) if on_total > 0 else 0.0

        # 2. Traffic when CAPTCHA was OFF (captcha_enabled = 0)
        cursor.execute("SELECT COUNT(*) AS total FROM security_logs WHERE captcha_enabled = 0")
        off_total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS passed FROM security_logs WHERE captcha_enabled = 0 AND status_code = 200")
        off_passed = cursor.fetchone()['passed']

        cursor.execute("SELECT COUNT(*) AS blocked FROM security_logs WHERE captcha_enabled = 0 AND status_code IN (400, 401, 403, 429)")
        off_blocked = cursor.fetchone()['blocked']

        off_block_rate = round((off_blocked / off_total * 100), 1) if off_total > 0 else 0.0

        # 3. HTTP 429 Rate Limiter triggered count
        cursor.execute("SELECT COUNT(*) AS rl_count FROM security_logs WHERE status_code = 429")
        rate_limit_count = cursor.fetchone()['rl_count']

        return {
            "on": {
                "total": on_total,
                "passed": on_passed,
                "blocked": on_blocked,
                "block_rate": on_block_rate
            },
            "off": {
                "total": off_total,
                "passed": off_passed,
                "blocked": off_blocked,
                "block_rate": off_block_rate
            },
            "rate_limit_count": rate_limit_count
        }

def clear_all_security_logs():
    """Clear all records in security_logs for a fresh demo session."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM security_logs")
        conn.commit()
