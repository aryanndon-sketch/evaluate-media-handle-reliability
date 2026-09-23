import unittest

from job_bot.application import ApplicationWorkflow
from job_bot.models import JobPosting, ResumeProfile, ResumeVariant, ScreeningQuestion
from job_bot.pipeline import ApplicationPipeline
from job_bot.question_planner import QuestionPlanner
from job_bot.resume_library import ResumeLibrary


class PipelineTests(unittest.TestCase):
    def test_selects_best_resume_and_blocks_for_review(self):
        workflow = ApplicationWorkflow()
        planner = QuestionPlanner({"are you authorized to work in this country?": "Yes"})
        pipeline = ApplicationPipeline(workflow, planner)
        library = ResumeLibrary(
            [
                ResumeVariant(id="general", file_path="general.pdf", keywords={"backend", "python"}),
                ResumeVariant(id="ml", file_path="ml.pdf", keywords={"machine learning"}, domains={"ai"}),
            ]
        )
        profile = ResumeProfile(
            name="Jane",
            email="jane@example.com",
            skills={"python", "machine learning"},
            years_experience=5,
            work_authorization="US",
        )
        job = JobPosting(
            id="job1",
            title="ML Engineer",
            company="Beta",
            requirements_text="3 years python machine learning",
            domain="ai",
        )

        record = pipeline.run(
            job=job,
            profile=profile,
            resume_library=library,
            required_fields=["name", "email", "work_authorization"],
            questions=[
                ScreeningQuestion(prompt="Are you authorized to work in this country?"),
                ScreeningQuestion(prompt="What is your notice period?"),
            ],
            user_approved_submit=True,
        )

        self.assertEqual(record["resume_variant_id"], "ml")
        self.assertEqual(record["status"], "pending_user_action")
        self.assertIn("What is your notice period?", record["question_answers"])

    def test_retry_then_fail_when_required_field_missing(self):
        workflow = ApplicationWorkflow()
        planner = QuestionPlanner()
        pipeline = ApplicationPipeline(workflow, planner, max_retries=1)
        library = ResumeLibrary([ResumeVariant(id="general", file_path="general.pdf")])
        profile = ResumeProfile(name="", email="jane@example.com", skills={"python"}, years_experience=3)
        job = JobPosting(id="job2", title="Backend", company="Acme", requirements_text="python")

        record = pipeline.run(
            job=job,
            profile=profile,
            resume_library=library,
            required_fields=["name", "email"],
            questions=[],
            user_approved_submit=False,
        )

        self.assertEqual(record["status"], "failed")
        self.assertGreaterEqual(record["attempts"], 1)


if __name__ == "__main__":
    unittest.main()
