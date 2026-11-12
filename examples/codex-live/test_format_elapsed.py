"""Acceptance tests for the bounded elapsed-time formatting slice."""

import unittest

from format_elapsed import format_elapsed


class FormatElapsedTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_elapsed(0), "0:00")

    def test_single_digit_seconds(self):
        self.assertEqual(format_elapsed(9), "0:09")

    def test_last_second_before_minute(self):
        self.assertEqual(format_elapsed(59), "0:59")

    def test_exact_minute(self):
        self.assertEqual(format_elapsed(60), "1:00")

    def test_minute_and_second(self):
        self.assertEqual(format_elapsed(61), "1:01")

    def test_minutes_beyond_fifty_nine(self):
        self.assertEqual(format_elapsed(3600), "60:00")


if __name__ == "__main__":
    unittest.main()
