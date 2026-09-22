from __future__ import annotations

import argparse
from pathlib import Path

from .compliance import ComplianceConfig
from .engine import JobAssistant
from .job_sources import StaticJobSource
from .models import UserFilters, WorkMode


def build_demo_source() -> StaticJobSource:
    return StaticJobSource(
        [
            {
                "id": "1",
                "title": "Backend Engineer",
                "company": "Acme",
                "requirements": "5 years Python SQL AWS. Preferred: docker kubernetes",
                "location": "Remote",
                "work_mode": "remote",
                "salary_min": 120000,
                "salary_max": 150000,
                "sponsorship_available": True,
                "domain": "saas",
                "application_url": "https://example.com/jobs/1",
            },
            {
                "id": "2",
                "title": "ML Engineer",
                "company": "BetaAI",
                "requirements": "3 years Python machine learning llm",
                "location": "Hybrid - London",
                "work_mode": "hybrid",
                "salary_min": 100000,
                "salary_max": 130000,
                "sponsorship_available": False,
                "domain": "ai",
                "application_url": "https://example.com/jobs/2",
            },
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume-based compliant job matching assistant")
    parser.add_argument("resume_pdf", type=Path, help="Path to resume PDF")
    parser.add_argument("--query", default="software engineer", help="Search query")
    parser.add_argument("--min-salary", type=int, default=None)
    args = parser.parse_args()

    assistant = JobAssistant(ComplianceConfig(allowed_sources={"static"}))
    assistant.grant_consent()
    profile = assistant.load_resume(str(args.resume_pdf))

    jobs = assistant.collect_jobs([build_demo_source()], args.query)
    filters = UserFilters(
        work_modes={WorkMode.REMOTE, WorkMode.HYBRID},
        minimum_salary=args.min_salary,
    )
    recommendations = assistant.recommend(jobs, filters)

    print(f"Profile skills: {', '.join(sorted(profile.skills)) or 'None detected'}")
    print("Top recommendations:")
    for idx, result in enumerate(recommendations[:5], start=1):
        print(f"{idx}. {result.job.title} @ {result.job.company} [{result.score} | {result.confidence}]")
        if result.strengths:
            print(f"   strengths: {', '.join(result.strengths[:2])}")
        if result.gaps:
            print(f"   gaps: {', '.join(result.gaps[:2])}")


if __name__ == "__main__":
    main()
