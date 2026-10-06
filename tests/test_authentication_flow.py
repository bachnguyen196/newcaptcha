import unittest
from app import create_app
from config import Config
from database.db import get_challenge, create_user
from werkzeug.security import generate_password_hash
from security.rate_limiter import limiter

class TestAuthenticationFlow(unittest.TestCase):
    """End-to-End API test cases for Authentication Flow and CAPTCHA defense."""

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        limiter.reset()
        self.original_visual_defense = Config.CAPTCHA_VISUAL_DEFENSE
        Config.CAPTCHA_VISUAL_DEFENSE = False
        Config.CAPTCHA_ENABLED = True

    def tearDown(self):
        Config.CAPTCHA_VISUAL_DEFENSE = self.original_visual_defense

    def test_login_missing_captcha_blocked(self):
        """Verify login is blocked (HTTP 400) if CAPTCHA is missing when enabled."""
        res = self.client.post('/login', json={'username': 'admin', 'password': 'password123'})
        self.assertEqual(res.status_code, 400)
        self.assertIn('Missing CAPTCHA', res.get_json()['message'])

    def test_login_wrong_captcha_blocked(self):
        """Verify login is blocked (HTTP 400) if CAPTCHA coordinate is incorrect."""
        ch = self.client.get('/captcha/challenge').get_json()
        cid = ch['challenge_id']

        res = self.client.post('/login', json={
            'username': 'admin',
            'password': 'password123',
            'captcha_challenge_id': cid,
            'captcha_user_x': 999  # deliberate wrong coordinate
        })
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()['reason'], 'WRONG_POSITION')

    def test_login_success_with_valid_captcha(self):
        """Verify login succeeds (HTTP 200) with valid CAPTCHA and credentials."""
        ch = self.client.get('/captcha/challenge').get_json()
        cid = ch['challenge_id']
        target_x = get_challenge(cid)['target_x']

        res = self.client.post('/login', json={
            'username': 'admin',
            'password': 'password123',
            'captcha_challenge_id': cid,
            'captcha_user_x': target_x
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Welcome admin', res.get_json()['message'])

    def test_login_bad_credentials_with_valid_captcha(self):
        """Verify HTTP 401 when CAPTCHA is solved correctly but password is wrong."""
        ch = self.client.get('/captcha/challenge').get_json()
        cid = ch['challenge_id']
        target_x = get_challenge(cid)['target_x']

        res = self.client.post('/login', json={
            'username': 'admin',
            'password': 'incorrect_password_xyz',
            'captcha_challenge_id': cid,
            'captcha_user_x': target_x
        })
        self.assertEqual(res.status_code, 401)

    def test_vulnerable_mode_captcha_disabled(self):
        """Verify that when CAPTCHA_ENABLED is False, login succeeds without challenge."""
        Config.CAPTCHA_ENABLED = False
        try:
            res = self.client.post('/login', json={'username': 'admin', 'password': 'password123'})
            self.assertEqual(res.status_code, 200)
        finally:
            Config.CAPTCHA_ENABLED = True

    def test_registration_endpoint_still_blocks_missing_captcha(self):
        res = self.client.post('/register', json={
            'username': 'captcha_demo_user',
            'password': 'secure-password'
        })

        self.assertEqual(res.status_code, 400)
        self.assertIn('Missing CAPTCHA', res.get_json()['message'])

    def test_dashboard_does_not_render_replaced_empty_session_demo(self):
        res = self.client.get('/dashboard')

        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertNotIn('Mô phỏng CAPTCHA rỗng trong Session', content)

    def test_classroom_demo_renders_interactive_lab(self):
        res = self.client.get('/demo')

        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn('AI Solver nhận dạng Slider CAPTCHA', content)
        self.assertIn('cv-capture-canvas', content)
        self.assertIn('OpenCV Solver', content)
        self.assertIn('Template Matching', content)
        self.assertIn('Chuỗi sự cố CAPTCHA và SQLi', content)
        self.assertIn('scenario-mode', content)
        self.assertIn('scenario-split', content)
        self.assertIn('scenario-progress', content)
        self.assertIn('scenario-db-rows', content)
        self.assertIn('scenario-counter', content)
        self.assertIn('scenario-feedback-submit', content)
        self.assertIn('scenario-fuzz-stream', content)
        self.assertIn('scenario-replay-log', content)
        self.assertIn('aria-relevant="additions"', content)
        self.assertIn('security-scenario.js', content)
        self.assertNotIn('Mô phỏng CAPTCHA rỗng trong Session', content)

    def test_cv_solver_finds_slot_without_target_in_challenge_payload(self):
        import base64
        import io
        from PIL import Image

        challenge = self.client.get('/captcha/challenge').get_json()
        self.assertNotIn('target_x', challenge)
        expected_x = get_challenge(challenge['challenge_id'])['target_x']

        background = Image.open(
            io.BytesIO(base64.b64decode(challenge['bg_image'].split(',', 1)[1]))
        ).convert('RGBA')
        piece = Image.open(
            io.BytesIO(base64.b64decode(challenge['piece_image'].split(',', 1)[1]))
        ).convert('RGBA')
        background.alpha_composite(piece, (0, challenge['y']))
        snapshot = io.BytesIO()
        background.convert('RGB').save(snapshot, format='PNG')
        canvas_image = 'data:image/png;base64,' + base64.b64encode(
            snapshot.getvalue()
        ).decode('ascii')

        solve = self.client.post('/api/demo/cv-solve', json={
            'canvas_image': canvas_image,
            'piece_image': challenge['piece_image'],
            'y': challenge['y']
        })

        self.assertEqual(solve.status_code, 200)
        result = solve.get_json()
        self.assertEqual(result['algorithm'], 'OpenCV Template Matching')
        self.assertLessEqual(abs(result['x'] - expected_x), Config.CAPTCHA_TOLERANCE)

        verify = self.client.post('/captcha/verify', json={
            'challenge_id': challenge['challenge_id'],
            'user_x': result['x']
        }, headers={'X-Bot-Type': 'computer_vision'})
        self.assertEqual(verify.status_code, 200)

    def test_cv_solver_rejects_invalid_image_payload(self):
        res = self.client.post('/api/demo/cv-solve', json={
            'canvas_image': 'not-an-image',
            'piece_image': 'not-an-image',
            'y': 20
        })

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()['status'], 'error')

    def test_visual_defense_breaks_fixed_color_solver_but_preserves_server_verification(self):
        import base64
        import io
        from PIL import Image

        challenge_response = self.client.get(
            '/api/demo/challenge?visual_defense=1'
        )
        self.assertEqual(challenge_response.status_code, 200)
        challenge = challenge_response.get_json()
        self.assertTrue(challenge['visual_defense'])
        self.assertNotIn('target_x', challenge)

        background = Image.open(
            io.BytesIO(base64.b64decode(challenge['bg_image'].split(',', 1)[1]))
        ).convert('RGBA')
        piece = Image.open(
            io.BytesIO(base64.b64decode(challenge['piece_image'].split(',', 1)[1]))
        ).convert('RGBA')
        background.alpha_composite(piece, (0, challenge['y']))
        snapshot = io.BytesIO()
        background.convert('RGB').save(snapshot, format='PNG')
        canvas_image = 'data:image/png;base64,' + base64.b64encode(
            snapshot.getvalue()
        ).decode('ascii')

        solve = self.client.post('/api/demo/cv-solve', json={
            'canvas_image': canvas_image,
            'piece_image': challenge['piece_image'],
            'y': challenge['y']
        })
        if solve.status_code == 200:
            predicted_x = solve.get_json()['x']
            target_x = get_challenge(challenge['challenge_id'])['target_x']
            self.assertGreater(
                abs(predicted_x - target_x),
                Config.CAPTCHA_TOLERANCE
            )
        else:
            self.assertEqual(solve.status_code, 400)
            self.assertEqual(solve.get_json()['status'], 'error')

        target_x = get_challenge(challenge['challenge_id'])['target_x']
        verify = self.client.post('/captcha/verify', json={
            'challenge_id': challenge['challenge_id'],
            'user_x': target_x
        })
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.get_json()['valid'])

    def test_visual_defense_can_be_enabled_for_regular_captcha_challenges(self):
        Config.CAPTCHA_VISUAL_DEFENSE = True

        response = self.client.get('/captcha/challenge')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['visual_defense'])
        self.assertNotIn('target_x', response.get_json())

if __name__ == '__main__':
    unittest.main()
