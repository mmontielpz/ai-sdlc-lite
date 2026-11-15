"""Tests for the first-five-minutes greeter example."""

import unittest

from src.greeter import greet


class GreeterTests(unittest.TestCase):
    def test_named_greeting(self):
        self.assertEqual(greet("  Ada  "), "Hello, Ada!")

    def test_empty_greeting(self):
        self.assertEqual(greet("   "), "Hello!")


if __name__ == "__main__":
    unittest.main()
