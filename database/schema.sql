-- Database Schema for Captcha Security Lab

-- 1. Users Table for Authentication Demo
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Captcha Challenges Table (Strict Server-Side Validation)
CREATE TABLE IF NOT EXISTS captcha_challenges (
    challenge_id TEXT PRIMARY KEY,
    target_x INTEGER NOT NULL,
    created_at REAL NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);

-- 3. Security Audit & Bot Analysis Logs
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    endpoint TEXT NOT NULL,
    captcha_enabled INTEGER NOT NULL DEFAULT 1,
    captcha_result TEXT DEFAULT 'none',
    status_code INTEGER NOT NULL,
    action TEXT NOT NULL,
    bot_type TEXT NOT NULL DEFAULT 'human'
);

-- Indices for fast querying in Dashboard & Unit Tests
CREATE INDEX IF NOT EXISTS idx_challenges_id ON captcha_challenges(challenge_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON security_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_bot_type ON security_logs(bot_type);
