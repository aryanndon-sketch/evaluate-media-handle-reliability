from __future__ import annotations

from .models import ResumeProfile, ScreeningQuestion


class QuestionPlanner:
    def __init__(self, qa_bank: dict[str, str] | None = None) -> None:
        self.qa_bank = {k.lower(): v for k, v in (qa_bank or {}).items()}

    def set_bank(self, qa_bank: dict[str, str]) -> None:
        self.qa_bank = {k.lower(): v for k, v in qa_bank.items()}

    def answer(self, profile: ResumeProfile, questions: list[ScreeningQuestion]) -> tuple[dict[str, str], list[str]]:
        answers: dict[str, str] = {}
        review_required: list[str] = []

        for question in questions:
            key = question.prompt.lower()
            if key in self.qa_bank:
                answers[question.prompt] = self.qa_bank[key]
                continue

            if "sponsorship" in key:
                value = "Yes" if "need" in profile.visa_status.lower() else "No"
                answers[question.prompt] = value
                continue

            if "authorized" in key or "work authorization" in key:
                answers[question.prompt] = profile.work_authorization or "Needs review"
                if not profile.work_authorization:
                    review_required.append(question.prompt)
                continue

            if "years" in key and "experience" in key:
                answers[question.prompt] = str(profile.years_experience)
                continue

            if question.target_field == "locations":
                answers[question.prompt] = ", ".join(profile.locations)
                continue

            answers[question.prompt] = "Needs review"
            review_required.append(question.prompt)

        return answers, review_required
