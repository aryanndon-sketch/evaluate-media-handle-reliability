from __future__ import annotations

from .application import ApplicationWorkflow
from .compliance import AuditLogger, ComplianceConfig, ConsentManager
from .job_sources import JobCollector, JobSource
from .matching import Matcher
from .models import MatchResult, ResumeProfile, ScreeningQuestion, UserFilters
from .pipeline import ApplicationPipeline
from .question_planner import QuestionPlanner
from .resume import ResumeParser
from .resume_library import ResumeLibrary


class JobAssistant:
    def __init__(self, compliance_config: ComplianceConfig, audit_log_path: str = "audit.log") -> None:
        self.consent = ConsentManager()
        self.audit = AuditLogger(audit_log_path)
        self.collector = JobCollector(compliance_config)
        self.workflow = ApplicationWorkflow()
        self.resume_library = ResumeLibrary()
        self.question_planner = QuestionPlanner()
        self.pipeline = ApplicationPipeline(self.workflow, self.question_planner)
        self.profile: ResumeProfile | None = None

    def grant_consent(self) -> None:
        self.consent.grant()
        self.audit.log("consent_granted", {"value": True})

    def configure_qa_bank(self, qa_bank: dict[str, str]) -> None:
        self.question_planner.set_bank(qa_bank)
        self.audit.log("qa_bank_configured", {"entries": len(qa_bank)})

    def configure_resume_variants(self, variants) -> None:
        for variant in variants:
            self.resume_library.upsert(variant)
        self.audit.log("resume_variants_configured", {"count": len(self.resume_library.list_variants())})

    def load_resume(self, pdf_path: str, overrides: dict | None = None) -> ResumeProfile:
        self.profile = ResumeParser.parse_pdf(pdf_path, overrides=overrides)
        self.audit.log("resume_loaded", {"path": pdf_path, "skills": len(self.profile.skills)})
        return self.profile

    def collect_jobs(self, sources: list[JobSource], query: str):
        self.consent.require_consent()
        jobs = self.collector.collect(sources, query)
        self.audit.log("jobs_collected", {"count": len(jobs), "query": query})
        return jobs

    def recommend(self, jobs, filters: UserFilters | None = None) -> list[MatchResult]:
        if not self.profile:
            raise RuntimeError("Resume profile must be loaded before recommendations")
        scoped_jobs = Matcher.filter_jobs(jobs, filters) if filters else jobs
        results = Matcher.evaluate(self.profile, scoped_jobs)
        self.audit.log("jobs_ranked", {"count": len(results)})
        return results

    def apply(
        self,
        job,
        required_fields: list[str],
        questions: list[ScreeningQuestion],
        login_required: bool = False,
        captcha_required: bool = False,
        user_approved_submit: bool = False,
    ) -> dict:
        if not self.profile:
            raise RuntimeError("Resume profile must be loaded before apply")
        result = self.pipeline.run(
            job=job,
            profile=self.profile,
            resume_library=self.resume_library,
            required_fields=required_fields,
            questions=questions,
            login_required=login_required,
            captcha_required=captcha_required,
            user_approved_submit=user_approved_submit,
        )
        self.audit.log("application_recorded", {"job_id": job.id, "status": result["status"]})
        return result
