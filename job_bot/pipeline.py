from __future__ import annotations

from .application import ApplicationWorkflow
from .models import ApplicationStatus, JobPosting, ResumeProfile, ScreeningQuestion
from .question_planner import QuestionPlanner
from .resume_library import ResumeLibrary


class ApplicationPipeline:
    def __init__(self, workflow: ApplicationWorkflow, question_planner: QuestionPlanner, max_retries: int = 2) -> None:
        self.workflow = workflow
        self.question_planner = question_planner
        self.max_retries = max_retries

    def run(
        self,
        job: JobPosting,
        profile: ResumeProfile,
        resume_library: ResumeLibrary,
        required_fields: list[str],
        questions: list[ScreeningQuestion],
        login_required: bool = False,
        captcha_required: bool = False,
        user_approved_submit: bool = False,
    ) -> dict:
        variant = resume_library.choose_best(job)
        record = self.workflow.start(job, resume_variant_id=variant.id if variant else "")

        if login_required:
            self.workflow.require_login(job.id)
        if captcha_required:
            self.workflow.require_captcha(job.id)

        attempts = 0
        while attempts <= self.max_retries:
            attempts += 1
            values = self.workflow.autofill(job.id, profile, required_fields)
            missing = [k for k, v in values.items() if not v]
            if not missing:
                break
            if attempts > self.max_retries:
                self.workflow.mark_failed(job.id, f"Missing required values: {', '.join(missing)}")
                return self.workflow.preview(job.id)
            self.workflow.mark_retry(job.id, f"Missing fields: {', '.join(missing)}")

        answers, review_required = self.question_planner.answer(profile, questions)
        self.workflow.attach_answers(job.id, answers)
        if review_required:
            self.workflow.records[job.id].notes.append(
                f"Manual review required for {len(review_required)} screening answers"
            )

        status = self.workflow.finalize(job.id, user_approved_submit and not review_required)
        if status == ApplicationStatus.PENDING_USER_ACTION and user_approved_submit and review_required:
            self.workflow.records[job.id].notes.append("Submit blocked pending answer review")

        return self.workflow.preview(job.id)
