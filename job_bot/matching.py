from __future__ import annotations

import re

from .models import JobPosting, MatchResult, ResumeProfile, UserFilters, WorkMode


def parse_requirements(job: JobPosting) -> JobPosting:
    text = job.requirements_text.lower()
    vocabulary = {
        "python",
        "java",
        "javascript",
        "typescript",
        "sql",
        "aws",
        "docker",
        "kubernetes",
        "react",
        "node",
        "django",
        "flask",
        "machine learning",
        "llm",
    }
    required = {s for s in vocabulary if re.search(rf"\b{s}\b", text)}

    preferred = set()
    preferred_section = re.findall(r"(?:preferred|nice to have)[:\-]\s*([^\n]+)", text)
    if preferred_section:
        pref_text = " ".join(preferred_section)
        preferred = {s for s in vocabulary if re.search(rf"\b{s}\b", pref_text)}

    years = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years", text)
    job.required_skills = required
    job.preferred_skills = preferred
    job.minimum_years_experience = max((float(y) for y in years), default=0.0)
    return job


class Matcher:
    @staticmethod
    def filter_jobs(jobs: list[JobPosting], filters: UserFilters) -> list[JobPosting]:
        filtered = []
        for job in jobs:
            if filters.work_modes and job.work_mode not in filters.work_modes:
                continue
            if filters.minimum_salary and (job.salary_max or 0) < filters.minimum_salary:
                continue
            if filters.sponsorship_required and not job.sponsorship_available:
                continue
            if filters.preferred_domains and job.domain not in filters.preferred_domains:
                continue
            filtered.append(job)
        return filtered

    @staticmethod
    def evaluate(profile: ResumeProfile, jobs: list[JobPosting]) -> list[MatchResult]:
        results: list[MatchResult] = []
        for job in jobs:
            parse_requirements(job)
            req = job.required_skills
            pref = job.preferred_skills
            strengths: list[str] = []
            gaps: list[str] = []

            matched_req = len(req.intersection(profile.skills))
            total_req = len(req) if req else 1
            required_ratio = matched_req / total_req

            for skill in sorted(req.intersection(profile.skills)):
                strengths.append(f"Has required skill: {skill}")
            for skill in sorted(req.difference(profile.skills)):
                gaps.append(f"Missing required skill: {skill}")

            if profile.years_experience >= job.minimum_years_experience:
                strengths.append(
                    f"Experience requirement met ({profile.years_experience} vs {job.minimum_years_experience} years)"
                )
            else:
                gaps.append(
                    f"Experience below requirement ({profile.years_experience} vs {job.minimum_years_experience} years)"
                )

            pref_matched = len(pref.intersection(profile.skills))
            pref_total = len(pref) if pref else 1
            pref_ratio = pref_matched / pref_total

            score = round((required_ratio * 0.7 + pref_ratio * 0.2 + (0.1 if not gaps else 0.0)) * 100, 2)
            confidence = "high" if score >= 80 else "medium" if score >= 60 else "low"

            standout = (
                profile.years_experience >= (job.minimum_years_experience + 2)
                and required_ratio >= 0.7
                and not gaps
            )
            if standout:
                strengths.append("Standout potential: exceeds baseline requirements")

            results.append(
                MatchResult(
                    job=job,
                    score=score,
                    confidence=confidence,
                    strengths=strengths,
                    gaps=gaps,
                    standout=standout,
                )
            )

        return sorted(results, key=lambda r: (r.standout, r.score), reverse=True)
