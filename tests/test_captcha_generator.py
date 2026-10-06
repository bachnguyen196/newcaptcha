import unittest
from captcha.generator import generate_captcha_challenge, create_jigsaw_mask

class TestCaptchaGenerator(unittest.TestCase):
    """Unit tests for procedural background and jigsaw puzzle generation."""

    def test_challenge_payload_structure(self):
        """Verify that generated challenge contains all required parameters."""
        challenge = generate_captcha_challenge(width=320, height=160, piece_size=48)

        self.assertIn('challenge_id', challenge)
        self.assertIn('target_x', challenge)
        self.assertIn('target_y', challenge)
        self.assertIn('bg_image', challenge)
        self.assertIn('piece_image', challenge)

        # Check types
        self.assertIsInstance(challenge['challenge_id'], str)
        self.assertEqual(len(challenge['challenge_id']), 32)  # UUID4 hex
        self.assertIsInstance(challenge['target_x'], int)
        self.assertIsInstance(challenge['target_y'], int)

    def test_coordinate_boundaries(self):
        """Verify that target coordinates stay well within image bounds."""
        width, height, piece_size = 320, 160, 48

        for _ in range(10):
            ch = generate_captcha_challenge(width=width, height=height, piece_size=piece_size)
            x, y = ch['target_x'], ch['target_y']

            # Target_X must leave room on the left (slider start) and right
            self.assertGreaterEqual(x, 60)
            self.assertLessEqual(x, width - piece_size - 15)

            # Target_Y must stay within top and bottom borders
            self.assertGreaterEqual(y, 15)
            self.assertLessEqual(y, height - piece_size - 15)

    def test_image_data_uri_format(self):
        """Verify that returned images are valid base64 data URIs."""
        ch = generate_captcha_challenge()
        self.assertTrue(ch['bg_image'].startswith('data:image/jpeg;base64,') or ch['bg_image'].startswith('data:image/png;base64,'))
        self.assertTrue(ch['piece_image'].startswith('data:image/png;base64,'))

    def test_jigsaw_mask_dimensions(self):
        """Verify jigsaw mask dimensions match specified piece size."""
        size = 48
        mask = create_jigsaw_mask(size=size)
        self.assertEqual(mask.size, (size, size))
        self.assertEqual(mask.mode, 'L')

if __name__ == '__main__':
    unittest.main()
