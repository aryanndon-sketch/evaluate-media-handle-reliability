from __future__ import annotations

from dataclasses import asdict

from .compliance import ComplianceConfig, SourceRateLimiter
from .models import JobPosting, WorkMode


class JobSourceError(RuntimeError):
    pass


class JobSource:
    source_name = "base"

    def fetch_jobs(self, query: str) -> list[dict]:
        raise NotImplementedError


class StaticJobSource(JobSource):
    source_name = "static"

    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs

    def fetch_jobs(self, query: str) -> list[dict]:
        _ = query
        return self.jobs


class JobCollector:
    def __init__(self, config: ComplianceConfig) -> None:
        self.config = config
        self.rate_limiter = SourceRateLimiter(config.requests_per_minute_per_source)

    def _normalize(self, raw: dict, source: str) -> JobPosting:
        return JobPosting(
            id=str(raw.get("id") or raw.get("job_id") or f"{source}-{raw.get('title', 'job')}") ,
            title=raw.get("title", ""),
            company=raw.get("company", ""),
            requirements_text=raw.get("requirements", ""),
            location=raw.get("location", ""),
            work_mode=WorkMode(raw.get("work_mode", WorkMode.REMOTE.value)),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            sponsorship_available=bool(raw.get("sponsorship_available", False)),
            domain=raw.get("domain", "general"),
            application_url=raw.get("application_url", ""),
            source=source,
        )

    def collect(self, sources: list[JobSource], query: str) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for source in sources:
            if source.source_name not in self.config.allowed_sources:
                raise JobSourceError(f"Source '{source.source_name}' is not approved for automation")
            if not self.rate_limiter.allow(source.source_name):
                raise JobSourceError(f"Rate limit reached for source '{source.source_name}'")
            for raw in source.fetch_jobs(query):
                jobs.append(self._normalize(raw, source.source_name))
        return jobs

    @staticmethod
    def as_dicts(jobs: list[JobPosting]) -> list[dict]:
        return [asdict(j) for j in jobs]
