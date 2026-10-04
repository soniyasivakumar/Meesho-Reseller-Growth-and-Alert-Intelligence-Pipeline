"""Given-When-Then tests for growth_engine.

Run from the repo root:   python -m unittest discover -s part2_engine -v
(pytest works too if you have it, but nothing beyond the standard library is needed.)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from growth_engine import is_flagged, mom_growth, validate_feed  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


class TestRequiredCases(unittest.TestCase):
    def test_1_ethnic_wear_april_to_may_is_flagged(self):
        # GIVEN Ethnic Wear revenue moves from 104520.77 (April) to 185107.61 (May)
        previous, current = 104520.77, 185107.61
        # WHEN mom_growth and then is_flagged run
        pct = mom_growth(previous, current)
        decision = is_flagged(pct)
        # THEN growth is 77.1 and the category is flagged
        self.assertEqual(pct, 77.1)
        self.assertEqual(decision, "flagged")

    def test_2_beauty_may_to_june_is_not_flagged(self):
        # GIVEN Beauty & Personal Care moves from 35542.11 to 37559.07
        pct = mom_growth(35542.11, 37559.07)
        decision = is_flagged(pct)
        # THEN growth is 5.67 and it is not flagged
        self.assertEqual(pct, 5.67)
        self.assertEqual(decision, "not_flagged")

    def test_3_exact_boundary_is_escalated_not_decided(self):
        # GIVEN a synthetic pair sitting exactly on the 8% threshold
        pct = mom_growth(100000, 108000)
        decision = is_flagged(pct)
        # THEN growth is exactly 8.0 and the answer is the escalation string,
        # not "flagged" and not "not_flagged"
        self.assertEqual(pct, 8.0)
        self.assertEqual(decision, "escalate_exact_boundary")
        self.assertNotIn(decision, ("flagged", "not_flagged"))

    def test_4_corrupted_feed_yields_three_ordered_errors(self):
        # GIVEN the corrupted feed fixture
        path = os.path.join(FIXTURES, "corrupted_feed.csv")
        # WHEN validate_feed runs on it
        ok, errors = validate_feed(path)
        # THEN it fails with exactly the three expected errors, in file order
        self.assertFalse(ok)
        self.assertEqual(len(errors), 3)
        self.assertEqual(errors, [
            "line 3: negative revenue (-4200.0) for category=Western Wear",
            "line 4: missing category (month=July)",
            "line 6: missing revenue (category=Home & Kitchen)",
        ])


class TestAcceptanceTables(unittest.TestCase):
    CAT_ORDER = ["Ethnic Wear", "Western Wear", "Kids Wear", "Home & Kitchen", "Beauty & Personal Care"]
    REVENUE = {
        "April": [104520.77, 113866.15, 59847.27, 100446.23, 40737.01],
        "May": [185107.61, 86998.18, 45793.78, 91152.57, 35542.11],
        "June": [76371.53, 97415.64, 56737.78, 129971.22, 37559.07],
    }

    def _table(self, prev_month, cur_month):
        out = {}
        for cat, p, c in zip(self.CAT_ORDER, self.REVENUE[prev_month], self.REVENUE[cur_month]):
            pct = mom_growth(p, c)
            out[cat] = (pct, is_flagged(pct))
        return out

    def test_may_vs_april_every_category_flagged(self):
        # GIVEN April and May category revenue WHEN MoM is computed THEN all five are flagged
        self.assertEqual(self._table("April", "May"), {
            "Ethnic Wear": (77.1, "flagged"),
            "Western Wear": (-23.6, "flagged"),
            "Kids Wear": (-23.48, "flagged"),
            "Home & Kitchen": (-9.25, "flagged"),
            "Beauty & Personal Care": (-12.75, "flagged"),
        })

    def test_june_vs_may_four_of_five_flagged(self):
        # GIVEN May and June category revenue WHEN MoM is computed THEN Beauty is the only one not flagged
        self.assertEqual(self._table("May", "June"), {
            "Ethnic Wear": (-58.74, "flagged"),
            "Western Wear": (11.97, "flagged"),
            "Kids Wear": (23.9, "flagged"),
            "Home & Kitchen": (42.59, "flagged"),
            "Beauty & Personal Care": (5.67, "not_flagged"),
        })


class TestValidFeedAndEdges(unittest.TestCase):
    def test_part1_output_passes_validation(self):
        # GIVEN the validated Part 1 CSV WHEN validate_feed runs THEN (True, [])
        path = os.path.join(FIXTURES, "monthly_category_revenue.csv")
        self.assertEqual(validate_feed(path), (True, []))

    def test_non_numeric_revenue_is_reported_with_repr(self):
        # GIVEN a feed with revenue "abc" WHEN validated THEN the raw text is quoted in the error
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("month,category,revenue,n_orders\nJuly,Kids Wear,abc,3\n")
        ok, errors = validate_feed(f.name)
        os.remove(f.name)
        self.assertFalse(ok)
        self.assertEqual(errors, ["line 2: revenue not numeric: 'abc'"])

    def test_zero_previous_revenue_raises(self):
        # GIVEN previous revenue of 0 WHEN mom_growth runs THEN it refuses instead of returning inf
        with self.assertRaises(ValueError):
            mom_growth(0, 500)

    def test_negative_boundary_is_also_escalated(self):
        # GIVEN a drop of exactly 8% WHEN evaluated THEN it is escalated like the +8% case
        self.assertEqual(is_flagged(mom_growth(100000, 92000)), "escalate_exact_boundary")


if __name__ == "__main__":
    unittest.main()
