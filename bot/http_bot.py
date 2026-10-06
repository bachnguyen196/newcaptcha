#!/usr/bin/env python3
"""
HTTP Bot Simulator for Captcha Security Lab
Simulates automated HTTP dictionary attacks / API spamming.

STRICT SAFETY RESTRICTION:
This bot is strictly permitted to run against LOCALHOST (127.0.0.1) ONLY.
Any attempt to target an external host will cause an immediate termination.
"""

import sys
import time
import argparse
from urllib.parse import urlparse
import requests

# Reconfigure stdout/stderr for Windows UTF-8 console compatibility
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def safe_print(msg):
    """Print safely without throwing UnicodeEncodeError on any Windows console."""
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode('ascii', errors='backslashreplace').decode('ascii'))
        except Exception:
            pass

# Safety Guardrail: Permitted Target Hosts
ALLOWED_HOSTS = {'127.0.0.1', 'localhost', '::1'}

def verify_safe_target(url):
    """Enforce strict localhost execution policy."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname or hostname not in ALLOWED_HOSTS:
            safe_print("=" * 60)
            safe_print("[!] CRITICAL ETHICAL & SAFETY VIOLATION")
            safe_print(f"[!] Target '{url}' is NOT a permitted local address!")
            safe_print(f"[!] Allowed targets: {ALLOWED_HOSTS}")
            safe_print("[!] Automation terminated immediately.")
            safe_print("=" * 60)
            raise ValueError(f"Target '{url}' is not a permitted localhost address!")
    except Exception as e:
        safe_print(f"[!] Error validating target URL: {e}")
        raise

def run_http_bot(target_url, total_requests=10, delay=0.3, username="admin"):
    """
    Execute HTTP Bot attack simulation against target login endpoint.
    Demonstrates bot behavior when CAPTCHA is ON vs OFF.
    Returns structured results dict for web GUI and CLI consumers.
    """
    verify_safe_target(target_url)

    login_endpoint = f"{target_url.rstrip('/')}/login"

    passwords = [
        "123456", "admin", "password", "root", "qwerty",
        "12345678", "guest", "admin123", "password123", "test"
    ]

    log_items = []
    def log(msg, item_type="info"):
        safe_print(msg)
        log_items.append({"type": item_type, "message": msg, "timestamp": time.strftime("%H:%M:%S")})

    log("=" * 65)
    log("🚀 BẮT ĐẦU MÔ PHỎNG TẤN CÔNG HTTP BOT (Python Requests)", "header")
    log(f"🎯 Mục tiêu (Endpoint) : {login_endpoint}")
    log(f"📊 Số lượt gửi (Total) : {total_requests}")
    log(f"⏱️  Khoảng nghỉ (Delay): {delay}s")
    log(f"👤 Tài khoản mục tiêu  : {username}")
    log("=" * 65)

    headers = {
        'User-Agent': 'python-requests/2.34.2 (HTTP-Bot-Test; SecurityLab)',
        'Content-Type': 'application/json'
    }

    stats = {
        "total": total_requests,
        "success": 0,
        "blocked_captcha": 0,
        "blocked_rate_limit": 0,
        "bad_credentials": 0,
        "other": 0
    }

    for i in range(1, total_requests + 1):
        pwd = passwords[(i - 1) % len(passwords)]
        payload = {
            "username": username,
            "password": pwd
        }

        start_time = time.time()
        try:
            res = requests.post(login_endpoint, json=payload, headers=headers, timeout=5)
            elapsed = int((time.time() - start_time) * 1000)

            if res.status_code == 200:
                stats["success"] += 1
                status_icon = "🟢 [THÀNH CÔNG - BYPASS]"
                item_type = "success"
                detail = f"Đăng nhập thành công với mật khẩu '{pwd}'!"
            elif res.status_code == 429:
                stats["blocked_rate_limit"] += 1
                status_icon = "🛑 [RATE LIMITED (429)]"
                item_type = "warning"
                detail = "Bị chặn bởi Rate Limiter (quá nhiều request)!"
            elif res.status_code == 400:
                stats["blocked_captcha"] += 1
                status_icon = "🛡️ [CHẶN BỞI CAPTCHA (400)]"
                item_type = "blocked"
                detail = res.json().get('message', 'Thiếu hoặc sai tọa độ Slider CAPTCHA')
            elif res.status_code == 401:
                stats["bad_credentials"] += 1
                status_icon = "🟡 [SAI MẬT KHẨU (401)]"
                item_type = "fail"
                detail = f"Mật khẩu không đúng '{pwd}'"
            else:
                stats["other"] += 1
                status_icon = f"⚪ [MÃ {res.status_code}]"
                item_type = "info"
                detail = res.text[:40]

            log(f"[{i:02d}/{total_requests:02d}] {status_icon} ({elapsed}ms) | {detail}", item_type)

        except requests.exceptions.ConnectionError:
            log(f"[{i:02d}/{total_requests:02d}] ❌ [MẤT KẾT NỐI] Web server chưa bật tại {target_url}!", "error")
            break
        except Exception as e:
            log(f"[{i:02d}/{total_requests:02d}] ❌ [LỖI] {e}", "error")

        if i < total_requests:
            time.sleep(delay)

    log("-" * 65)
    log("📋 BÁO CÁO TỔNG KẾT MÔ PHỎNG HTTP BOT", "header")
    log(f"• Tổng số request đã gửi    : {total_requests}")
    log(f"• Đăng nhập thành công (200) : {stats['success']}")
    log(f"• Bị chặn bởi CAPTCHA (400) : {stats['blocked_captcha']}")
    log(f"• Bị chặn bởi Rate Limit (429): {stats['blocked_rate_limit']}")
    log(f"• Thất bại do sai pass (401) : {stats['bad_credentials']}")
    log("-" * 65)

    if stats["blocked_captcha"] > 0:
        conclusion = "🛡️ KẾT LUẬN: Cơ chế Slider CAPTCHA đã ngăn chặn 100% tấn công tự động của HTTP Bot!"
        concl_type = "success"
    elif stats["success"] > 0:
        conclusion = "⚠️ CẢNH BÁO: Khi CAPTCHA TẮT, HTTP Bot đã tấn công dò mật khẩu thành công!"
        concl_type = "warning"
    elif stats["blocked_rate_limit"] > 0:
        conclusion = "🛑 KẾT LUẬN: Rate Limiter đã bảo vệ server khi lượng request dồn dập (HTTP 429)!"
        concl_type = "warning"
    else:
        conclusion = "ℹ️ Mô phỏng hoàn tất."
        concl_type = "info"

    log(conclusion, concl_type)
    log("=" * 65)

    return {
        "status": "success",
        "target_url": target_url,
        "total_requests": total_requests,
        "stats": stats,
        "logs": log_items,
        "conclusion": conclusion
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HTTP Bot Simulator for Captcha Security Lab (Localhost Only)")
    parser.add_argument("--target", default="http://127.0.0.1:5000", help="Target base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--requests", type=int, default=10, help="Number of requests to send (default: 10)")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests in seconds (default: 0.3)")
    parser.add_argument("--user", default="admin", help="Username to target (default: admin)")

    args = parser.parse_args()
    run_http_bot(target_url=args.target, total_requests=args.requests, delay=args.delay, username=args.user)
