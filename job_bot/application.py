from __future__ import annotations

from .models import ApplicationRecord, ApplicationStatus, JobPosting, ResumeProfile


class ApplicationWorkflow:
    def __init__(self) -> None:
        self.records: dict[str, ApplicationRecord] = {}

    def start(self, job: JobPosting) -> ApplicationRecord:
        record = ApplicationRecord(job_id=job.id, status=ApplicationStatus.DRAFTED)
        self.records[job.id] = record
        return record

    def require_login(self, job_id: str) -> str:
        record = self.records[job_id]
        record.status = ApplicationStatus.PENDING_USER_ACTION
        note = "Login required. Please authenticate in-session, then resume."
        record.notes.append(note)
        return note

    def require_captcha(self, job_id: str) -> str:
        record = self.records[job_id]
        record.status = ApplicationStatus.PENDING_USER_ACTION
        note = "CAPTCHA encountered. Please solve manually, then resume."
        record.notes.append(note)
        return note

    def autofill(self, job_id: str, profile: ResumeProfile, required_fields: list[str]) -> dict[str, str]:
        record = self.records[job_id]
        values: dict[str, str] = {}
        mapper = {
            "name": profile.name,
            "email": profile.email,
            "skills": ", ".join(sorted(profile.skills)),
            "years_experience": str(profile.years_experience),
            "locations": ", ".join(profile.locations),
            "roles": ", ".join(profile.roles),
        }
        for field in required_fields:
            values[field] = mapper.get(field, "")
        record.field_values.update(values)
        record.status = ApplicationStatus.READY_TO_SUBMIT
        return values

    def preview(self, job_id: str) -> dict:
        record = self.records[job_id]
        return {
            "job_id": record.job_id,
            "status": record.status.value,
            "field_values": record.field_values,
            "notes": record.notes,
        }

    def finalize(self, job_id: str, user_approved: bool) -> ApplicationStatus:
        record = self.records[job_id]
        if not user_approved:
            record.status = ApplicationStatus.PENDING_USER_ACTION
            record.notes.append("Submission held: user did not confirm")
            return record.status
        record.status = ApplicationStatus.SUBMITTED
        record.notes.append("Submission confirmed by user")
        return record.status
