from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkMode(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ApplicationStatus(str, Enum):
    DRAFTED = "drafted"
    PENDING_USER_ACTION = "pending_user_action"
    READY_TO_SUBMIT = "ready_to_submit"
    SUBMITTED = "submitted"
    FAILED = "failed"


@dataclass(slots=True)
class ResumeProfile:
    name: str = ""
    email: str = ""
    skills: set[str] = field(default_factory=set)
    years_experience: float = 0.0
    roles: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    visa_status: str = ""
    work_authorization: str = ""


@dataclass(slots=True)
class JobPosting:
    id: str
    title: str
    company: str
    requirements_text: str
    required_skills: set[str] = field(default_factory=set)
    preferred_skills: set[str] = field(default_factory=set)
    minimum_years_experience: float = 0.0
    location: str = ""
    work_mode: WorkMode = WorkMode.REMOTE
    salary_min: int | None = None
    salary_max: int | None = None
    sponsorship_available: bool = False
    domain: str = "general"
    application_url: str = ""
    source: str = ""


@dataclass(slots=True)
class MatchResult:
    job: JobPosting
    score: float
    confidence: str
    strengths: list[str]
    gaps: list[str]
    standout: bool


@dataclass(slots=True)
class UserFilters:
    work_modes: set[WorkMode] | None = None
    minimum_salary: int | None = None
    sponsorship_required: bool = False
    preferred_domains: set[str] | None = None


@dataclass(slots=True)
class ApplicationRecord:
    job_id: str
    status: ApplicationStatus
    field_values: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
