"""Offline tests (no API calls). Run:  python -m unittest discover tests"""

import unittest

from src.pipeline import decide_recommendation
from src.quotes import check_quotes, quote_in_source

SOURCE = "Students learn “dynamic programming” and graph algorithms.\nThe course   covers sorting—in depth."


class QuoteTests(unittest.TestCase):
    def test_exact_quote(self):
        self.assertTrue(quote_in_source("graph algorithms", SOURCE))

    def test_whitespace_and_typography_ignored(self):
        self.assertTrue(quote_in_source('learn "dynamic programming" and graph', SOURCE))
        self.assertTrue(quote_in_source("covers sorting-in depth", SOURCE))

    def test_reworded_quote_rejected(self):
        self.assertFalse(quote_in_source("students study dynamic programming", SOURCE))

    def test_ellipsis_quote_rejected(self):
        self.assertFalse(quote_in_source("Students learn ... graph algorithms", SOURCE))

    def test_case_matters(self):
        self.assertFalse(quote_in_source("GRAPH ALGORITHMS", SOURCE))

    def test_empty_quote_rejected(self):
        self.assertFalse(quote_in_source("   ", SOURCE))

    def test_check_quotes_list(self):
        self.assertEqual(check_quotes(["sorting", "made up"], SOURCE), [True, False])


class RecommendationRuleTests(unittest.TestCase):
    def test_all_full(self):
        self.assertEqual(decide_recommendation(["full", "full"]), "recognize")

    def test_none_covered(self):
        self.assertEqual(decide_recommendation(["none", "none"]), "reject")

    def test_mixed(self):
        self.assertEqual(decide_recommendation(["full", "partial", "none"]), "partial")
        self.assertEqual(decide_recommendation(["full", "none"]), "partial")

    def test_no_outcomes(self):
        self.assertEqual(decide_recommendation([]), "not_enough_information")

    def test_mostly_unverified(self):
        self.assertEqual(decide_recommendation(["unverified", "unverified", "full"]), "not_enough_information")

    def test_minority_unverified_counts_as_gap(self):
        self.assertEqual(decide_recommendation(["full", "full", "unverified"]), "partial")


if __name__ == "__main__":
    unittest.main()
