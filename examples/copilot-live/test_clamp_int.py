"""Tests for the isolated Copilot CLI clamp example."""

import unittest

from clamp_int import clamp_int


class ClampIntTests(unittest.TestCase):
    def test_below_range(self):
        self.assertEqual(clamp_int(2, 3, 8), 3)

    def test_at_lower_bound(self):
        self.assertEqual(clamp_int(3, 3, 8), 3)

    def test_inside_range(self):
        self.assertEqual(clamp_int(5, 3, 8), 5)

    def test_at_upper_bound(self):
        self.assertEqual(clamp_int(8, 3, 8), 8)

    def test_above_range(self):
        self.assertEqual(clamp_int(10, 3, 8), 8)

    def test_negative_range(self):
        self.assertEqual(clamp_int(-9, -6, -2), -6)


if __name__ == "__main__":
    unittest.main()
