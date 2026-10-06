import unittest
from security.rate_limiter import SlidingWindowRateLimiter

class TestRateLimiter(unittest.TestCase):
    """Unit tests for the Sliding Window Rate Limiter algorithm."""

    def setUp(self):
        # Create a test limiter: 5 requests per 2 seconds
        self.limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=2)

    def test_requests_within_limit(self):
        """Verify that requests below threshold are permitted."""
        ip = "192.168.1.100"
        for i in range(5):
            allowed, remaining, retry_after = self.limiter.is_allowed(ip)
            self.assertTrue(allowed)
            self.assertEqual(remaining, 5 - (i + 1))
            self.assertEqual(retry_after, 0)

    def test_rate_limit_exceeded(self):
        """Verify that request exceeding threshold is denied."""
        ip = "192.168.1.100"
        # Exhaust allowed quota
        for _ in range(5):
            self.limiter.is_allowed(ip)

        # 6th request must be blocked
        allowed, remaining, retry_after = self.limiter.is_allowed(ip)
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(retry_after, 0)

    def test_independent_ip_tracking(self):
        """Verify that different IP addresses have independent rate limits."""
        ip_a = "10.0.0.1"
        ip_b = "10.0.0.2"

        # Exhaust IP A
        for _ in range(5):
            self.limiter.is_allowed(ip_a)

        # IP A is blocked
        allowed_a, _, _ = self.limiter.is_allowed(ip_a)
        self.assertFalse(allowed_a)

        # IP B must still be permitted!
        allowed_b, remaining_b, _ = self.limiter.is_allowed(ip_b)
        self.assertTrue(allowed_b)
        self.assertEqual(remaining_b, 4)

    def test_reset_limiter(self):
        """Verify reset clears tracked IP quotas."""
        ip = "192.168.1.100"
        for _ in range(5):
            self.limiter.is_allowed(ip)

        # Confirm blocked
        self.assertFalse(self.limiter.is_allowed(ip)[0])

        # Reset
        self.limiter.reset()

        # Should be permitted again
        self.assertTrue(self.limiter.is_allowed(ip)[0])

if __name__ == '__main__':
    unittest.main()
