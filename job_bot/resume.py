from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from .models import ResumeProfile

KNOWN_SKILLS = {
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


class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(pdf_path: str | Path) -> str:
        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def profile_from_text(text: str, overrides: dict | None = None) -> ResumeProfile:
        lowered = text.lower()
        skills = {skill for skill in KNOWN_SKILLS if skill in lowered}

        years_match = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years", lowered)
        years_experience = max((float(y) for y in years_match), default=0.0)

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        name = text.splitlines()[0].strip() if text.splitlines() else ""

        role_matches = re.findall(
            r"\b(?:software engineer|data scientist|ml engineer|backend engineer|frontend engineer|full stack engineer)\b",
            lowered,
        )

        location_matches = re.findall(r"\b(?:remote|new york|san francisco|london|berlin|india|usa)\b", lowered)

        profile = ResumeProfile(
            name=name,
            email=email_match.group(0) if email_match else "",
            skills=skills,
            years_experience=years_experience,
            roles=sorted(set(role_matches)),
            locations=sorted(set(location_matches)),
            education=[],
            visa_status="",
            work_authorization="",
        )

        if overrides:
            for field, value in overrides.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)

        return profile

    @classmethod
    def parse_pdf(cls, pdf_path: str | Path, overrides: dict | None = None) -> ResumeProfile:
        text = cls.extract_text_from_pdf(pdf_path)
        return cls.profile_from_text(text, overrides=overrides)
