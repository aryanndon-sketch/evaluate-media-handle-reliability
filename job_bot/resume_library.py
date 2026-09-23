from __future__ import annotations

from .models import JobPosting, ResumeVariant


class ResumeLibrary:
    def __init__(self, variants: list[ResumeVariant] | None = None) -> None:
        self._variants: dict[str, ResumeVariant] = {v.id: v for v in (variants or [])}

    def upsert(self, variant: ResumeVariant) -> None:
        self._variants[variant.id] = variant

    def list_variants(self) -> list[ResumeVariant]:
        return list(self._variants.values())

    def choose_best(self, job: JobPosting) -> ResumeVariant | None:
        best: tuple[int, ResumeVariant] | None = None
        bag = f"{job.title} {job.requirements_text} {job.domain}".lower()
        for variant in self._variants.values():
            keyword_hits = sum(1 for k in variant.keywords if k.lower() in bag)
            domain_bonus = 2 if job.domain.lower() in {d.lower() for d in variant.domains} else 0
            score = keyword_hits + domain_bonus
            if not best or score > best[0]:
                best = (score, variant)
        return best[1] if best else None
