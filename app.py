import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database.db import (
    init_db,
    create_user,
    get_user_by_username,
    save_challenge,
    cleanup_old_challenges,
    log_security_event,
    get_recent_logs,
    get_log_statistics
)
from captcha.generator import generate_captcha_challenge
from captcha.validator import validate_slider_captcha
from security.rate_limiter import rate_limited, limiter
from security.security_logger import get_comparative_analytics, clear_all_security_logs

def create_app():
    """Application factory for Flask Captcha Lab."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize SQLite Database and create initial demo account
    with app.app_context():
        init_db()
        # Seed default test user if not exists
        if not get_user_by_username('admin'):
            create_user('admin', generate_password_hash('password123'))

    # Inject global variables to all Jinja templates
    @app.context_processor
    def inject_globals():
        return {
            'captcha_enabled': Config.CAPTCHA_ENABLED
        }

    # ================= HELPER FUNCTIONS =================

    def detect_client_type(req):
        """Classify request origin based on User-Agent and headers."""
        ua = req.headers.get('User-Agent', '').lower()
        if 'python-requests' in ua or 'requests' in ua:
            return 'http_bot'
        if 'selenium' in ua or req.headers.get('X-Bot-Type') == 'selenium':
            return 'selenium_bot'
        if req.headers.get('X-Bot-Type') == 'computer_vision':
            return 'cv_bot'
        return 'human'

    def get_client_ip(req):
        """Extract client IP address."""
        if req.headers.get('X-Forwarded-For'):
            return req.headers.get('X-Forwarded-For').split(',')[0].strip()
        return req.remote_addr or '127.0.0.1'

    # ================= ROUTES =================

    @app.route('/')
    def index():
        """Home overview page."""
        return render_template('index.html')

    @app.route('/demo')
    def demo():
        """Interactive classroom lab for local computer-vision CAPTCHA testing."""
        stats = get_log_statistics()
        return render_template(
            'demo.html',
            logs=get_recent_logs(limit=12),
            stats=stats
        )

    @app.route('/login', methods=['GET', 'POST'])
    @rate_limited()
    def login():
        """User Login endpoint with Slider CAPTCHA enforcement."""
        if request.method == 'GET':
            return render_template('login.html')

        ip = get_client_ip(request)
        ua = request.headers.get('User-Agent', '')
        bot_type = detect_client_type(request)

        data = request.get_json(silent=True) if request.is_json else request.form
        if not data:
            data = request.form

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        challenge_id = data.get('captcha_challenge_id')
        user_x = data.get('captcha_user_x')

        captcha_result = 'none'

        # 1. CAPTCHA Verification Layer (Defense-in-depth)
        if Config.CAPTCHA_ENABLED:
            if not challenge_id or user_x is None or str(user_x).strip() == '':
                log_security_event(
                    ip_address=ip,
                    user_agent=ua,
                    endpoint='/login',
                    captcha_enabled=Config.CAPTCHA_ENABLED,
                    captcha_result='none',
                    status_code=400,
                    action='login_blocked_missing_captcha',
                    bot_type=bot_type
                )
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'Missing CAPTCHA challenge or coordinates.'}), 400
                flash("Vui lòng kéo thanh trượt để giải CAPTCHA trước khi đăng nhập!", "warning")
                return redirect(url_for('login'))

            is_valid, reason = validate_slider_captcha(challenge_id, user_x)
            captcha_result = 'pass' if is_valid else reason.lower()

            if not is_valid:
                log_security_event(
                    ip_address=ip,
                    user_agent=ua,
                    endpoint='/login',
                    captcha_enabled=Config.CAPTCHA_ENABLED,
                    captcha_result=captcha_result,
                    status_code=400,
                    action=f"login_blocked_captcha_{reason.lower()}",
                    bot_type=bot_type
                )
                error_msgs = {
                    "WRONG_POSITION": "Vị trí mảnh ghép chưa chính xác. Vui lòng căn chỉnh lại!",
                    "REPLAY_ATTACK": "Phát hiện mã CAPTCHA đã sử dụng (Replay Attack)! Vui lòng lấy câu đố mới.",
                    "EXPIRED": "Mã xác thực CAPTCHA đã hết hạn (quá 2 phút). Vui lòng đổi câu đố mới!",
                    "INVALID_CHALLENGE": "Mã câu đố không hợp lệ!",
                    "INVALID_INPUT": "Tọa độ gửi lên không đúng định dạng!"
                }
                msg = error_msgs.get(reason, "Xác thực CAPTCHA thất bại!")
                if request.is_json:
                    return jsonify({'status': 'error', 'message': msg, 'reason': reason}), 400
                flash(msg, "danger")
                return redirect(url_for('login'))

        # 2. Credential Verification Layer
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            log_security_event(
                ip_address=ip,
                user_agent=ua,
                endpoint='/login',
                captcha_enabled=Config.CAPTCHA_ENABLED,
                captcha_result=captcha_result,
                status_code=200,
                action='login_success',
                bot_type=bot_type
            )
            if request.is_json:
                return jsonify({'status': 'success', 'message': f'Welcome {username}'}), 200
            flash(f"Đăng nhập thành công! Chào mừng {username}.", "success")
            return redirect(url_for('dashboard'))
        else:
            log_security_event(
                ip_address=ip,
                user_agent=ua,
                endpoint='/login',
                captcha_enabled=Config.CAPTCHA_ENABLED,
                captcha_result=captcha_result,
                status_code=401,
                action='login_failed_bad_credentials',
                bot_type=bot_type
            )
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid username or password.'}), 401
            flash("Tên đăng nhập hoặc mật khẩu không chính xác.", "danger")
            return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    @rate_limited()
    def register():
        """User Registration endpoint with Slider CAPTCHA enforcement."""
        if request.method == 'GET':
            return render_template('register.html')

        ip = get_client_ip(request)
        ua = request.headers.get('User-Agent', '')
        bot_type = detect_client_type(request)

        data = request.get_json(silent=True) if request.is_json else request.form
        if not data:
            data = request.form

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        confirm = data.get('confirm_password', '').strip()
        challenge_id = data.get('captcha_challenge_id')
        user_x = data.get('captcha_user_x')

        captcha_result = 'none'

        if Config.CAPTCHA_ENABLED:
            if not challenge_id or user_x is None or str(user_x).strip() == '':
                log_security_event(
                    ip_address=ip,
                    user_agent=ua,
                    endpoint='/register',
                    captcha_enabled=Config.CAPTCHA_ENABLED,
                    captcha_result='none',
                    status_code=400,
                    action='register_blocked_missing_captcha',
                    bot_type=bot_type
                )
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'Missing CAPTCHA.'}), 400
                flash("Vui lòng kéo thanh trượt CAPTCHA trước khi đăng ký!", "warning")
                return redirect(url_for('register'))

            is_valid, reason = validate_slider_captcha(challenge_id, user_x)
            captcha_result = 'pass' if is_valid else reason.lower()

            if not is_valid:
                log_security_event(
                    ip_address=ip,
                    user_agent=ua,
                    endpoint='/register',
                    captcha_enabled=Config.CAPTCHA_ENABLED,
                    captcha_result=captcha_result,
                    status_code=400,
                    action=f"register_blocked_captcha_{reason.lower()}",
                    bot_type=bot_type
                )
                error_msgs = {
                    "WRONG_POSITION": "Vị trí mảnh ghép chưa chính xác!",
                    "REPLAY_ATTACK": "Phát hiện mã CAPTCHA đã sử dụng (Replay Attack)!",
                    "EXPIRED": "Mã CAPTCHA đã hết hạn!"
                }
                msg = error_msgs.get(reason, "Xác thực CAPTCHA thất bại!")
                if request.is_json:
                    return jsonify({'status': 'error', 'message': msg, 'reason': reason}), 400
                flash(msg, "danger")
                return redirect(url_for('register'))

        if not username or not password:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Missing username or password.'}), 400
            flash("Vui lòng nhập đầy đủ username và mật khẩu.", "warning")
            return redirect(url_for('register'))

        if len(username) < 3:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Username too short.'}), 400
            flash("Username phải có ít nhất 3 ký tự.", "warning")
            return redirect(url_for('register'))

        if len(password) < 6:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Password too short.'}), 400
            flash("Mật khẩu phải có ít nhất 6 ký tự.", "warning")
            return redirect(url_for('register'))

        # Only check confirm password in browser form submits
        if not request.is_json and password != confirm:
            flash("Mật khẩu xác nhận không khớp.", "danger")
            return redirect(url_for('register'))

        if get_user_by_username(username):
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Username exists.'}), 400
            flash("Tên đăng nhập này đã tồn tại, vui lòng chọn tên khác.", "warning")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        success = create_user(username, hashed)

        if success:
            log_security_event(
                ip_address=ip,
                user_agent=ua,
                endpoint='/register',
                captcha_enabled=Config.CAPTCHA_ENABLED,
                captcha_result=captcha_result,
                status_code=200,
                action='register_success',
                bot_type=bot_type
            )
            if request.is_json:
                return jsonify({'status': 'success', 'message': 'Registration successful'}), 200
            flash("Đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay.", "success")
            return redirect(url_for('login'))
        else:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Database error'}), 500
            flash("Đã có lỗi xảy ra khi tạo tài khoản.", "danger")
            return redirect(url_for('register'))

    @app.route('/logout')
    def logout():
        """Clear user session."""
        username = session.pop('username', None)
        flash("Bạn đã đăng xuất an toàn.", "info")
        return redirect(url_for('index'))

    @app.route('/dashboard')
    def dashboard():
        """Security and Bot Forensics Dashboard."""
        logs = get_recent_logs(limit=50)
        stats = get_log_statistics()
        analytics = get_comparative_analytics()
        return render_template('dashboard.html', logs=logs, stats=stats, analytics=analytics)

    @app.route('/toggle-captcha', methods=['POST'])
    def toggle_captcha():
        """Runtime toggle for CAPTCHA_ENABLED during local lab demonstrations."""
        Config.CAPTCHA_ENABLED = not Config.CAPTCHA_ENABLED
        status = "BẬT" if Config.CAPTCHA_ENABLED else "TẮT"
        flash(f"Đã chuyển trạng thái Slider CAPTCHA sang: {status}", "info")
        return redirect(request.referrer or url_for('dashboard'))

    # ================= JSON APIS =================

    @app.route('/api/stats')
    def api_stats():
        """Return live statistics for dashboard polling."""
        stats = get_log_statistics()
        analytics = get_comparative_analytics()
        return jsonify({
            'status': 'success',
            'captcha_enabled': Config.CAPTCHA_ENABLED,
            'stats': stats,
            'analytics': analytics
        })

    @app.route('/api/logs')
    def api_logs():
        """Return recent logs as JSON."""
        logs = get_recent_logs(limit=50)
        return jsonify({
            'status': 'success',
            'logs': logs
        })

    # ================= CAPTCHA APIS =================

    @app.route('/captcha/challenge', methods=['GET'])
    @rate_limited()
    def captcha_challenge():
        """
        Generate and return a new Slider Puzzle CAPTCHA challenge.
        Target_X is saved exclusively on the server (SQLite) and NEVER sent to the client.
        """
        if not Config.CAPTCHA_ENABLED:
            return jsonify({
                'status': 'disabled',
                'message': 'CAPTCHA protection is currently disabled.'
            })

        # Cleanup expired challenges to prevent DB bloat
        cleanup_old_challenges(Config.CAPTCHA_TTL_SECONDS)

        # Generate challenge using Pillow
        challenge = generate_captcha_challenge(
            width=320,
            height=160,
            piece_size=48,
            visual_defense=Config.CAPTCHA_VISUAL_DEFENSE
        )

        # Store challenge securely in SQLite
        save_challenge(challenge['challenge_id'], challenge['target_x'])

        # Return payload without target_x
        return jsonify({
            'status': 'success',
            'challenge_id': challenge['challenge_id'],
            'bg_image': challenge['bg_image'],
            'piece_image': challenge['piece_image'],
            'y': challenge['target_y'],
            'width': challenge['width'],
            'height': challenge['height'],
            'piece_size': challenge['piece_size'],
            'visual_defense': Config.CAPTCHA_VISUAL_DEFENSE
        })

    @app.route('/api/demo/challenge', methods=['GET'])
    @rate_limited()
    def api_demo_challenge():
        """Create a classroom challenge with the optional visual-defense variant."""
        if not Config.CAPTCHA_ENABLED:
            return jsonify({
                'status': 'disabled',
                'message': 'CAPTCHA protection is currently disabled.'
            }), 409

        visual_defense = request.args.get('visual_defense') == '1'
        cleanup_old_challenges(Config.CAPTCHA_TTL_SECONDS)
        challenge = generate_captcha_challenge(
            width=320,
            height=160,
            piece_size=48,
            visual_defense=visual_defense
        )
        save_challenge(challenge['challenge_id'], challenge['target_x'])

        return jsonify({
            'status': 'success',
            'challenge_id': challenge['challenge_id'],
            'bg_image': challenge['bg_image'],
            'piece_image': challenge['piece_image'],
            'y': challenge['target_y'],
            'width': challenge['width'],
            'height': challenge['height'],
            'piece_size': challenge['piece_size'],
            'visual_defense': visual_defense
        })

    @app.route('/captcha/verify', methods=['POST'])
    @rate_limited()
    def captcha_verify():
        """
        Standalone API endpoint to verify a solved Slider CAPTCHA challenge.
        Used for API-level verification testing and unit tests.
        """
        data = request.get_json(silent=True) or request.form
        challenge_id = data.get('challenge_id')
        user_x = data.get('user_x')

        ip = get_client_ip(request)
        ua = request.headers.get('User-Agent', '')
        bot_type = detect_client_type(request)

        is_valid, reason = validate_slider_captcha(challenge_id, user_x)

        status_code = 200 if is_valid else 400
        captcha_res = 'pass' if is_valid else reason.lower()

        log_security_event(
            ip_address=ip,
            user_agent=ua,
            endpoint='/captcha/verify',
            captcha_enabled=Config.CAPTCHA_ENABLED,
            captcha_result=captcha_res,
            status_code=status_code,
            action=f"captcha_verify_{reason.lower()}",
            bot_type=bot_type
        )

        return jsonify({
            'status': 'success' if is_valid else 'error',
            'valid': is_valid,
            'reason': reason
        }), status_code

    @app.route('/clear-logs', methods=['POST'])
    def clear_logs():
        """Clear all audit logs for a fresh demo session."""
        clear_all_security_logs()
        limiter.reset()
        flash("Đã dọn sạch toàn bộ Security Logs và reset Rate Limiter!", "info")
        return redirect(url_for('dashboard'))

    @app.route('/api/demo/cv-solve', methods=['POST'])
    @rate_limited()
    def api_demo_cv_solve():
        """Infer the slider position from rendered CAPTCHA pixels using OpenCV."""
        if not Config.CAPTCHA_ENABLED:
            return jsonify({
                'status': 'error',
                'message': 'Bật CAPTCHA để chạy thử nghiệm Computer Vision.'
            }), 409

        if request.content_length and request.content_length > 2_500_000:
            return jsonify({'status': 'error', 'message': 'Image payload exceeds the size limit.'}), 413

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'A JSON object is required.'}), 400

        try:
            target_y = data.get('y')
            if isinstance(target_y, bool) or not isinstance(target_y, int):
                raise ValueError('The public puzzle row must be an integer.')
            from captcha.cv_solver import solve_slider_images
            match = solve_slider_images(
                data.get('canvas_image'),
                data.get('piece_image'),
                target_y
            )
        except ValueError as error:
            return jsonify({'status': 'error', 'message': str(error)}), 400

        log_security_event(
            ip_address=get_client_ip(request),
            user_agent=request.headers.get('User-Agent', ''),
            endpoint='/api/demo/cv-solve',
            captcha_enabled=Config.CAPTCHA_ENABLED,
            captcha_result='matched',
            status_code=200,
            action='computer_vision_template_match',
            bot_type='cv_bot'
        )

        return jsonify({
            'status': 'success',
            **match,
            'algorithm': 'OpenCV Template Matching'
        })


    # ================= BOT ATTACK SIMULATION APIS =================

    @app.route('/api/bot/http-simulate', methods=['POST'])
    def api_bot_http_simulate():
        """
        Execute automated HTTP Bot dictionary attack simulation on localhost.
        Returns live logs and summary stats to Dashboard GUI.
        """
        data = request.get_json(silent=True) or {}
        req_count = int(data.get('requests', 10))
        req_count = max(1, min(req_count, 30))
        delay = float(data.get('delay', 0.2))
        delay = max(0.05, min(delay, 2.0))
        target_user = str(data.get('username', 'admin')).strip() or 'admin'

        base_url = f"http://127.0.0.1:{Config.PORT}"
        try:
            from bot.http_bot import run_http_bot
            result = run_http_bot(base_url, total_requests=req_count, delay=delay, username=target_user)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'logs': [{'type': 'error', 'message': f'[!] Lỗi thực thi HTTP Bot: {e}'}]
            }), 500

    @app.route('/api/bot/selenium-simulate', methods=['POST'])
    def api_bot_selenium_simulate():
        """
        Execute Selenium browser automation bot simulation on localhost.
        Returns live logs, whether CAPTCHA was detected, and summary to Dashboard GUI.
        """
        data = request.get_json(silent=True) or {}
        target_user = str(data.get('username', 'admin')).strip() or 'admin'
        password = str(data.get('password', 'password123')).strip() or 'password123'
        headless = bool(data.get('headless', False))

        base_url = f"http://127.0.0.1:{Config.PORT}"
        try:
            from bot.selenium_bot import run_selenium_bot
            result = run_selenium_bot(base_url, username=target_user, password=password, headless=headless)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'logs': [{'type': 'error', 'message': f'[!] Lỗi thực thi Selenium Bot: {e}'}]
            }), 500

    return app

if __name__ == '__main__':
    # Strictly Localhost only
    app = create_app()
    print(f"[*] Starting Captcha Security Lab on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
