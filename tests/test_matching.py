import unittest

from job_bot.matching import Matcher
from job_bot.models import JobPosting, ResumeProfile, WorkMode


class MatchingTests(unittest.TestCase):
    def test_ranks_standout_candidate_first(self):
        profile = ResumeProfile(skills={"python", "sql", "aws", "docker"}, years_experience=8)
        jobs = [
            JobPosting(
                id="a",
                title="Backend",
                company="A",
                requirements_text="5 years python sql aws. Preferred: docker",
                work_mode=WorkMode.REMOTE,
            ),
            JobPosting(
                id="b",
                title="Frontend",
                company="B",
                requirements_text="4 years javascript react",
                work_mode=WorkMode.REMOTE,
            ),
        ]
        ranked = Matcher.evaluate(profile, jobs)
        self.assertEqual(ranked[0].job.id, "a")
        self.assertTrue(ranked[0].standout)


if __name__ == "__main__":
    unittest.main()
