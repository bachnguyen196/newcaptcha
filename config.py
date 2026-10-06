import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Flask Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'captcha-lab-secret-key-2026-nam4')

    # Database Configuration
    DATABASE_PATH = BASE_DIR / 'database' / 'database.db'

    # CAPTCHA Security Settings
    # Toggle for A/B testing and demonstration
    CAPTCHA_ENABLED = os.environ.get('CAPTCHA_ENABLED', 'True').lower() in ('true', '1', 'yes')
    CAPTCHA_VISUAL_DEFENSE = os.environ.get(
        'CAPTCHA_VISUAL_DEFENSE', 'false'
    ).lower() in ('true', '1', 'yes')
    CAPTCHA_TTL_SECONDS = int(os.environ.get('CAPTCHA_TTL_SECONDS', 120))  # 2 minutes TTL
    CAPTCHA_TOLERANCE = int(os.environ.get('CAPTCHA_TOLERANCE', 5))  # Allowed margin of error in pixels

    # Rate Limiting Settings (10 requests per 10 seconds per IP)
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 10))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 10))  # in seconds

    # Server settings (Strictly localhost only)
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = True
