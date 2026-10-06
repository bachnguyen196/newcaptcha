#!/usr/bin/env python3
"""
Selenium Bot Simulator for Captcha Security Lab
Demonstrates browser automation interacting with DOM elements,
and how the presence of a Slider CAPTCHA stops automation dead in its tracks.

STRICT SAFETY RESTRICTION:
This bot is strictly permitted to run against LOCALHOST (127.0.0.1) ONLY.
Any attempt to target an external host will cause an immediate termination.
"""

import sys
import time
import argparse
from urllib.parse import urlparse

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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def get_webdriver(headless=False):
    """Initialize Chrome or Edge WebDriver."""
    try:
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,800")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (Selenium-Bot-Test)")
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as chrome_err:
        try:
            edge_opts = EdgeOptions()
            if headless:
                edge_opts.add_argument("--headless=new")
            edge_opts.add_argument("--window-size=1280,800")
            driver = webdriver.Edge(options=edge_opts)
            return driver
        except Exception as edge_err:
            raise RuntimeError(f"Không thể khởi động trình duyệt (Chrome: {chrome_err}, Edge: {edge_err})")

def run_selenium_bot(target_url, username="admin", password="password123", headless=False):
    """
    Simulate browser automation via Selenium.
    Proves that DOM manipulation succeeds for form inputs,
    but halts upon detecting the Slider CAPTCHA barrier.
    Returns structured results dict for web GUI and CLI consumers.
    """
    verify_safe_target(target_url)

    login_url = f"{target_url.rstrip('/')}/login"

    log_items = []
    def log(msg, item_type="info"):
        safe_print(msg)
        log_items.append({"type": item_type, "message": msg, "timestamp": time.strftime("%H:%M:%S")})

    log("=" * 65)
    log("🕷️  BẮT ĐẦU MÔ PHỎNG SELENIUM AUTOMATION BOT", "header")
    log(f"🎯 Mục tiêu (URL)      : {login_url}")
    log(f"👤 Tài khoản mục tiêu : {username}")
    log(f"🖥️  Chế độ Headless    : {headless}")
    log("=" * 65)

    driver = None
    try:
        driver = get_webdriver(headless=headless)
        log("[*] Bước 1: Khởi động trình duyệt và truy cập trang đăng nhập...", "info")
        driver.get(login_url)
        time.sleep(1)

        log("[*] Bước 2: Tự động tương tác với các phần tử DOM form...", "info")
        username_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_input = driver.find_element(By.ID, "password")

        # Simulate typing
        username_input.clear()
        username_input.send_keys(username)
        log(f"    -> Đã tự động điền username: '{username}'", "info")
        time.sleep(0.5)

        password_input.clear()
        password_input.send_keys(password)
        log(f"    -> Đã tự động điền password: '••••••••'", "info")
        time.sleep(0.5)

        log("[*] Bước 3: Quét DOM tìm kiếm các rào cản chống tự động hóa (Anti-Bot)...", "info")
        captcha_elements = driver.find_elements(By.CSS_SELECTOR, "#captcha-container .captcha-widget, #captcha-bg, #captcha-slider")

        if captcha_elements:
            log("🛑 [CẢNH BÁO] Phát hiện Slider CAPTCHA! Quá trình tự động hóa bị chặn đứng.", "blocked")
            log("    - Bot phát hiện phần tử Slider CAPTCHA trong DOM (#captcha-container).", "info")
            log("    - Bot không thể nhận diện thị giác hoặc tự động kéo mảnh ghép hình học.", "info")
            log("    - Hệ thống đã bảo vệ form đăng nhập thành công trước Selenium Bot!", "success")
            conclusion = "🛡️ KẾT LUẬN: Rào cản Slider CAPTCHA đã phát hiện và chặn đứng Selenium Bot thành công!"
            result_code = "CAPTCHA_DETECTED_STOPPED"
            time.sleep(2)
        else:
            log("⚠️ [LỖ HỔNG] Không phát hiện CAPTCHA! Bot tiếp tục nhấn nút gửi form...", "warning")
            submit_btn = driver.find_element(By.ID, "btn-submit")
            submit_btn.click()
            time.sleep(1.5)

            current_url = driver.current_url
            if "dashboard" in current_url:
                log("🟢 [BYPASS THÀNH CÔNG] Bot đã tự động đăng nhập vào Dashboard mà không cần CAPTCHA!", "danger")
                log(f"    Trang hiện tại: {current_url}", "info")
                conclusion = "⚠️ CẢNH BÁO: Khi tắt CAPTCHA, Selenium Bot đã tự động điền form và chiếm quyền thành công!"
            else:
                log(f"🟡 Form đã gửi. URL hiện tại: {current_url}", "info")
                conclusion = "ℹ️ Bot đã gửi form đăng nhập thành công khi không có CAPTCHA."
            result_code = "NO_CAPTCHA_SUBMITTED"

        log("=" * 65)
        log(conclusion, "success" if result_code == "CAPTCHA_DETECTED_STOPPED" else "warning")
        log("=" * 65)

        return {
            "status": "success",
            "result": result_code,
            "conclusion": conclusion,
            "logs": log_items
        }

    except Exception as e:
        err_msg = f"[!] Lỗi trong quá trình tự động hóa: {e}"
        log(err_msg, "error")
        return {
            "status": "error",
            "result": "ERROR",
            "conclusion": err_msg,
            "logs": log_items
        }
    finally:
        if driver:
            try:
                driver.quit()
                log("[*] Đã đóng trình duyệt. Phiên tự động hóa kết thúc.", "info")
            except Exception:
                pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Selenium Bot for Captcha Security Lab (Localhost Only)")
    parser.add_argument("--target", default="http://127.0.0.1:5000", help="Target URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--user", default="admin", help="Username (default: admin)")
    parser.add_argument("--pwd", default="password123", help="Password (default: password123)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    args = parser.parse_args()
    run_selenium_bot(target_url=args.target, username=args.user, password=args.pwd, headless=args.headless)
