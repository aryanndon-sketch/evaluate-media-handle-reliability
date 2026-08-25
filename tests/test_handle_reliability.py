import unittest
from datetime import datetime, timezone

from handle_reliability import (
    LABEL_NEUTRAL,
    LABEL_RELIABLE,
    LABEL_UNRELIABLE,
    clean_cell,
    handle_key,
    normalize_domain,
    normalize_handle,
    score_handle,
    should_refresh,
)


class HandleReliabilityTests(unittest.TestCase):
    def test_clean_cell_handles_nan_and_empty_string(self):
        self.assertIsNone(clean_cell(float("nan")))
        self.assertIsNone(clean_cell("   "))
        self.assertEqual(clean_cell("  abc "), "abc")

    def test_normalization_helpers(self):
        self.assertEqual(normalize_handle("@BBCWorld"), "bbcworld")
        self.assertEqual(normalize_domain("https://www.Reuters.com/world"), "reuters.com")
        self.assertEqual(handle_key("X", "@BBCWorld"), "x:bbcworld")

    def test_missing_data_defaults_to_neutral_with_review(self):
        result = score_handle(
            row={"handle": "@unknown", "platform": "x"},
            credible_domains=set(),
            low_credibility_domains=set(),
            factcheck_failed_handles=set(),
        )
        self.assertEqual(result.label, LABEL_NEUTRAL)
        self.assertTrue(result.needs_review)
        self.assertIn("Insufficient signals", result.reasons)

    def test_reliable_and_unreliable_thresholds(self):
        reliable = score_handle(
            row={
                "handle": "@bbcworld",
                "platform": "x",
                "manual_identity_clear": "yes",
                "manual_verified": "yes",
                "manual_account_age_bucket": "2yr_plus",
                "linked_domain": "bbc.com",
            },
            credible_domains={"bbc.com"},
            low_credibility_domains=set(),
            factcheck_failed_handles=set(),
        )
        self.assertEqual(reliable.label, LABEL_RELIABLE)

        unreliable = score_handle(
            row={
                "handle": "@badactor",
                "platform": "x",
                "manual_identity_clear": "no",
                "manual_impersonation_flag": "yes",
                "manual_parody_labeled": "no",
                "linked_domain": "infowars.com",
            },
            credible_domains=set(),
            low_credibility_domains={"infowars.com"},
            factcheck_failed_handles={"@badactor"},
        )
        self.assertEqual(unreliable.label, LABEL_UNRELIABLE)

    def test_should_refresh(self):
        now = datetime(2026, 8, 25, tzinfo=timezone.utc)
        self.assertTrue(should_refresh(None, now))
        self.assertFalse(should_refresh("2026-08-10T00:00:00+00:00", now, ttl_days=30))
        self.assertTrue(should_refresh("2026-06-01T00:00:00+00:00", now, ttl_days=30))
        self.assertFalse(should_refresh("2026-08-10T00:00:00", now, ttl_days=30))


if __name__ == "__main__":
    unittest.main()
