import time
from functools import wraps
from threading import Lock
from flask import request, jsonify, flash, redirect, render_template

from config import Config
from database.db import log_security_event

class SlidingWindowRateLimiter:
    """
    Sliding Window Rate Limiter (Thread-Safe, In-Memory).
    Tracks timestamps per IP address within a rolling time window.
    Designed for clarity and straightforward academic defense.
    """
    def __init__(self, max_requests=10, window_seconds=10):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ip_records = {}  # { ip_address: [timestamp1, timestamp2, ...] }
        self.lock = Lock()

    def is_allowed(self, ip_address):
        """
        Check if an incoming request from ip_address is permitted.
        Returns:
            (allowed: bool, remaining: int, retry_after: int)
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self.lock:
            # Get existing timestamps and purge expired ones
            timestamps = self.ip_records.get(ip_address, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= self.max_requests:
                # Rate limit exceeded
                oldest_in_window = valid_timestamps[0]
                retry_after = int(oldest_in_window + self.window_seconds - now) + 1
                self.ip_records[ip_address] = valid_timestamps
                return False, 0, max(1, retry_after)

            # Record this request
            valid_timestamps.append(now)
            self.ip_records[ip_address] = valid_timestamps
            remaining = self.max_requests - len(valid_timestamps)
            return True, remaining, 0

    def reset(self):
        """Clear all rate limit tracking records."""
        with self.lock:
            self.ip_records.clear()

# Global Rate Limiter instance initialized with Config settings
limiter = SlidingWindowRateLimiter(
    max_requests=Config.RATE_LIMIT_REQUESTS,
    window_seconds=Config.RATE_LIMIT_WINDOW
)

def rate_limited():
    """
    Flask route decorator to enforce IP Rate Limiting.
    Returns HTTP 429 Too Many Requests if rate is exceeded.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1').split(',')[0].strip()
            ua = request.headers.get('User-Agent', '')

            # Classify bot type for security log
            ua_lower = ua.lower()
            if 'python-requests' in ua_lower or 'requests' in ua_lower:
                bot_type = 'http_bot'
            elif 'selenium' in ua_lower:
                bot_type = 'selenium_bot'
            else:
                bot_type = 'human'

            allowed, remaining, retry_after = limiter.is_allowed(ip)

            if not allowed:
                # Log Rate Limit violation in audit table
                log_security_event(
                    ip_address=ip,
                    user_agent=ua,
                    endpoint=request.path,
                    captcha_enabled=Config.CAPTCHA_ENABLED,
                    captcha_result='none',
                    status_code=429,
                    action='rate_limit_exceeded',
                    bot_type=bot_type
                )

                if request.is_json or request.path.startswith('/api/') or request.path.startswith('/captcha/'):
                    response = jsonify({
                        'status': 'error',
                        'code': 429,
                        'message': f"Too Many Requests. Rate limit of {Config.RATE_LIMIT_REQUESTS} req/{Config.RATE_LIMIT_WINDOW}s exceeded.",
                        'retry_after_seconds': retry_after
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(retry_after)
                    return response

                flash(f"⚠️ Phát hiện tần suất gửi yêu cầu quá nhanh! Vui lòng chờ {retry_after} giây trước khi thử lại.", "warning")
                return redirect(request.referrer or '/')

            response = f(*args, **kwargs)
            return response
        return decorated_function
    return decorator
