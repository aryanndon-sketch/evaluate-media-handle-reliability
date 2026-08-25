from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OpenSourceBioIdentityModel:
    model_name: str = "facebook/bart-large-mnli"
    confidence_threshold: float = 0.65

    def __post_init__(self) -> None:
        self._classifier = None

    def _load(self) -> None:
        if self._classifier is not None:
            return
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "transformers is required for --use-open-source-bio-model. "
                "Install with: python -m pip install transformers torch"
            ) from exc

        self._classifier = pipeline("zero-shot-classification", model=self.model_name)

    def predict_identity_clear(self, bio_text: Optional[str]) -> Optional[bool]:
        if not bio_text:
            return None

        self._load()
        assert self._classifier is not None

        labels = ["clear official identity", "unclear anonymous identity"]
        result = self._classifier(bio_text, candidate_labels=labels, multi_label=False)
        scores = dict(zip(result["labels"], result["scores"]))

        clear = float(scores.get("clear official identity", 0.0))
        unclear = float(scores.get("unclear anonymous identity", 0.0))

        if max(clear, unclear) < self.confidence_threshold:
            return None
        return clear >= unclear
