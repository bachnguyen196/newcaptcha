import time
import unittest
import uuid

from config import Config
from database.db import init_db, save_challenge, get_challenge
from captcha.validator import validate_slider_captcha

class TestCaptchaValidator(unittest.TestCase):
    """Unit tests for Server-Side Slider CAPTCHA validation security rules."""

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_valid_exact_coordinate(self):
        """Test validation passes with exact matching coordinate."""
        cid = uuid.uuid4().hex
        target_x = 140
        save_challenge(cid, target_x)

        is_valid, reason = validate_slider_captcha(cid, target_x)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "PASS")

    def test_valid_within_tolerance(self):
        """Test validation passes within Config.CAPTCHA_TOLERANCE margin."""
        cid = uuid.uuid4().hex
        target_x = 150
        save_challenge(cid, target_x)

        # Offset within tolerance (e.g. +3px when tolerance is 5px)
        user_x = target_x + (Config.CAPTCHA_TOLERANCE - 2)
        is_valid, reason = validate_slider_captcha(cid, user_x)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "PASS")

    def test_invalid_outside_tolerance(self):
        """Test validation fails when coordinate is outside tolerance."""
        cid = uuid.uuid4().hex
        target_x = 150
        save_challenge(cid, target_x)

        user_x = target_x + Config.CAPTCHA_TOLERANCE + 15
        is_valid, reason = validate_slider_captcha(cid, user_x)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "WRONG_POSITION")

    def test_anti_replay_attack(self):
        """Test that a challenge CANNOT be reused a second time (Replay Attack defense)."""
        cid = uuid.uuid4().hex
        target_x = 120
        save_challenge(cid, target_x)

        # 1st attempt: Consumes challenge
        ok1, reason1 = validate_slider_captcha(cid, target_x)
        self.assertTrue(ok1)
        self.assertEqual(reason1, "PASS")

        # 2nd attempt with same ID: MUST be rejected as REPLAY_ATTACK
        ok2, reason2 = validate_slider_captcha(cid, target_x)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "REPLAY_ATTACK")

    def test_expired_challenge_ttl(self):
        """Test that a challenge older than Config.CAPTCHA_TTL_SECONDS is rejected."""
        cid = uuid.uuid4().hex
        target_x = 100
        # Simulate challenge created 150 seconds ago (TTL is 120 seconds)
        expired_created_at = time.time() - (Config.CAPTCHA_TTL_SECONDS + 30)
        save_challenge(cid, target_x, created_at=expired_created_at)

        is_valid, reason = validate_slider_captcha(cid, target_x)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "EXPIRED")

    def test_nonexistent_challenge_id(self):
        """Test validation fails when challenge ID does not exist."""
        is_valid, reason = validate_slider_captcha("fake-uuid-not-found", 100)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "INVALID_CHALLENGE")

    def test_malformed_input(self):
        """Test validation fails cleanly when input is malformed or missing."""
        is_valid, reason = validate_slider_captcha("", 100)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "INVALID_INPUT")

        cid = uuid.uuid4().hex
        save_challenge(cid, 100)
        is_valid, reason = validate_slider_captcha(cid, "not-a-number")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "INVALID_INPUT")

if __name__ == '__main__':
    unittest.main()
