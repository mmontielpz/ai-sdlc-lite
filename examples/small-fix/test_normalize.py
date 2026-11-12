"""Immutable repair tests expressing the intended normalization behavior."""

import unittest

from normalize import normalize_name


class NormalizeNameTests(unittest.TestCase):
    def test_mixed_case(self):
        self.assertEqual(normalize_name("AlIcE"), "alice")

    def test_surrounding_spaces(self):
        self.assertEqual(normalize_name("  Alice  "), "alice")

    def test_tabs_and_newlines(self):
        self.assertEqual(normalize_name("\tAlice\n"), "alice")

    def test_empty_input(self):
        self.assertEqual(normalize_name(""), "")

    def test_preserved_internal_whitespace(self):
        self.assertEqual(normalize_name("Alice  \tSMITH"), "alice  \tsmith")


if __name__ == "__main__":
    unittest.main()
