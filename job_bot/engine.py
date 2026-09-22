from __future__ import annotations

from .application import ApplicationWorkflow
from .compliance import AuditLogger, ComplianceConfig, ConsentManager
from .job_sources import JobCollector, JobSource
from .matching import Matcher
from .models import MatchResult, ResumeProfile, UserFilters
from .resume import ResumeParser


class JobAssistant:
    def __init__(self, compliance_config: ComplianceConfig, audit_log_path: str = "audit.log") -> None:
        self.consent = ConsentManager()
        self.audit = AuditLogger(audit_log_path)
        self.collector = JobCollector(compliance_config)
        self.workflow = ApplicationWorkflow()
        self.profile: ResumeProfile | None = None

    def grant_consent(self) -> None:
        self.consent.grant()
        self.audit.log("consent_granted", {"value": True})

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
