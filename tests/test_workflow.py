import unittest

from job_bot.application import ApplicationWorkflow
from job_bot.models import ApplicationStatus, JobPosting, ResumeProfile


class WorkflowTests(unittest.TestCase):
    def test_requires_confirmation_before_submit(self):
        workflow = ApplicationWorkflow()
        job = JobPosting(id="x", title="Role", company="C", requirements_text="")
        workflow.start(job)
        profile = ResumeProfile(name="Dev", email="dev@example.com", skills={"python"}, years_experience=4)
        workflow.autofill(job.id, profile, ["name", "email", "skills"])

        status = workflow.finalize(job.id, user_approved=False)
        self.assertEqual(status, ApplicationStatus.PENDING_USER_ACTION)

        status = workflow.finalize(job.id, user_approved=True)
        self.assertEqual(status, ApplicationStatus.SUBMITTED)

    def test_login_and_captcha_pause(self):
        workflow = ApplicationWorkflow()
        job = JobPosting(id="y", title="Role", company="D", requirements_text="")
        workflow.start(job)
        workflow.require_login(job.id)
        self.assertEqual(workflow.records[job.id].status, ApplicationStatus.PENDING_USER_ACTION)
        workflow.require_captcha(job.id)
        self.assertEqual(workflow.records[job.id].status, ApplicationStatus.PENDING_USER_ACTION)


if __name__ == "__main__":
    unittest.main()
