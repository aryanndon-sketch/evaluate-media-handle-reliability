import unittest

from job_bot.resume import ResumeParser


class ResumeTests(unittest.TestCase):
    def test_profile_overrides_applied(self):
        text = "Jane Doe\nEmail: jane@example.com\n6 years python sql aws"
        profile = ResumeParser.profile_from_text(text, overrides={"visa_status": "H1B", "work_authorization": "US"})
        self.assertIn("python", profile.skills)
        self.assertEqual(profile.years_experience, 6.0)
        self.assertEqual(profile.visa_status, "H1B")
        self.assertEqual(profile.work_authorization, "US")


if __name__ == "__main__":
    unittest.main()
