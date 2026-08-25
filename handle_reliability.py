from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isnan
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


SCORING_VERSION = "1.0.0"
LABEL_RELIABLE = "reliable"
LABEL_UNRELIABLE = "unreliable"
LABEL_NEUTRAL = "neutral"


YES = {"yes", "true", "1", "y"}
NO = {"no", "false", "0", "n"}


@dataclass(frozen=True)
class ScoreResult:
    label: str
    score: int
    confidence: float
    needs_review: bool
    reasons: List[str]
    scoring_version: str = SCORING_VERSION


def clean_cell(value: Any) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, float) and isnan(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def as_bool(value: Any) -> Optional[bool]:
    value = clean_cell(value)
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in YES:
        return True
    if normalized in NO:
        return False
    return None


def normalize_handle(handle: Any) -> Optional[str]:
    handle = clean_cell(handle)
    if handle is None:
        return None
    normalized = str(handle).strip().lower()
    if normalized.startswith("@"):
        normalized = normalized[1:]
    return normalized or None


def normalize_platform(platform: Any) -> Optional[str]:
    platform = clean_cell(platform)
    return str(platform).strip().lower() if platform is not None else None


def normalize_domain(url_or_domain: Any) -> Optional[str]:
    value = clean_cell(url_or_domain)
    if value is None:
        return None
    raw = str(value).strip().lower()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    domain = parsed.netloc or parsed.path
    domain = domain.split("/")[0].strip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or None


def handle_key(platform: Any, handle: Any, domain: Any = None) -> Optional[str]:
    p = normalize_platform(platform)
    h = normalize_handle(handle)
    d = normalize_domain(domain)
    if p is None:
        return None
    if h:
        return f"{p}:{h}"
    if d:
        return f"{p}:domain:{d}"
    return None


def should_refresh(last_enriched_at: Optional[str], now: datetime, ttl_days: int = 30) -> bool:
    if not last_enriched_at:
        return True
    try:
        when = datetime.fromisoformat(last_enriched_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_days = (now - when).days
    return age_days >= ttl_days


def _bucket_score(value: Any) -> Tuple[int, Optional[str]]:
    bucket = clean_cell(value)
    if bucket is None:
        return 0, None
    bucket = str(bucket).lower()
    if bucket == "2yr_plus":
        return 1, None
    if bucket == "under_3_months":
        return -1, "Very new account"
    return 0, None


def score_handle(
    row: Dict[str, Any],
    credible_domains: Iterable[str],
    low_credibility_domains: Iterable[str],
    factcheck_failed_handles: Iterable[str],
) -> ScoreResult:
    def _normalized_domain_set(values: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for value in values:
            normalized = normalize_domain(value)
            if normalized:
                out.add(normalized)
        return out

    def _normalized_handle_set(values: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for value in values:
            normalized = normalize_handle(value)
            if normalized:
                out.add(normalized)
        return out

    credible_domain_set = _normalized_domain_set(credible_domains)
    low_cred_domain_set = _normalized_domain_set(low_credibility_domains)
    failed_handle_set = _normalized_handle_set(factcheck_failed_handles)

    score = 0
    reasons: List[str] = []
    evidence_points = 0

    identity_clear = as_bool(row.get("manual_identity_clear"))
    verified = as_bool(row.get("manual_verified"))
    impersonation = as_bool(row.get("manual_impersonation_flag"))
    parody_labeled = as_bool(row.get("manual_parody_labeled"))
    account_age_bucket = row.get("manual_account_age_bucket")

    if identity_clear is True:
        score += 2
        evidence_points += 1
    elif identity_clear is False:
        score -= 1
        evidence_points += 1
        reasons.append("Unclear identity")

    if verified is True:
        score += 1
        evidence_points += 1

    age_score, age_reason = _bucket_score(account_age_bucket)
    score += age_score
    if age_score != 0:
        evidence_points += 1
    if age_reason:
        reasons.append(age_reason)

    domain = normalize_domain(row.get("linked_domain") or row.get("url"))
    if domain:
        credible = domain in credible_domain_set
        low_cred = domain in low_cred_domain_set
        if credible:
            score += 3
            evidence_points += 1
        elif low_cred:
            score -= 3
            evidence_points += 1
            reasons.append("Linked domain is low credibility")

    normalized_handle = normalize_handle(row.get("handle"))
    if normalized_handle and normalized_handle in failed_handle_set:
        score -= 4
        evidence_points += 1
        reasons.append("Fact-check failures")

    if impersonation is True:
        score -= 4
        evidence_points += 1
        reasons.append("Likely impersonation")

    if parody_labeled is False:
        score -= 3
        evidence_points += 1
        reasons.append("Parody/satire appears unlabeled")

    if score >= 5:
        label = LABEL_RELIABLE
    elif score <= -5:
        label = LABEL_UNRELIABLE
    else:
        label = LABEL_NEUTRAL

    confidence = min(abs(score) / 10.0, 1.0)
    needs_review = label == LABEL_NEUTRAL or evidence_points < 2 or confidence < 0.5
    if evidence_points == 0:
        reasons.append("Insufficient signals")

    return ScoreResult(
        label=label,
        score=score,
        confidence=round(confidence, 3),
        needs_review=needs_review,
        reasons=reasons,
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
