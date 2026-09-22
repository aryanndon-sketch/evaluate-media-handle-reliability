from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ComplianceConfig:
    allowed_sources: set[str]
    requests_per_minute_per_source: int = 30


class ConsentError(PermissionError):
    pass


class ConsentManager:
    def __init__(self) -> None:
        self._consent_given = False

    def grant(self) -> None:
        self._consent_given = True

    def require_consent(self) -> None:
        if not self._consent_given:
            raise ConsentError("User consent is required before automation actions")


class SourceRateLimiter:
    def __init__(self, per_minute_limit: int) -> None:
        self.per_minute_limit = per_minute_limit
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, source: str) -> bool:
        now = time.time()
        events = self._events[source]
        while events and now - events[0] > 60:
            events.popleft()
        if len(events) >= self.per_minute_limit:
            return False
        events.append(now)
        return True


class AuditLogger:
    def __init__(self, path: str | Path = "audit.log") -> None:
        self.path = Path(path)

    def log(self, event: str, details: dict[str, str | int | float | bool]) -> None:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "details": details,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
