"""Normalised event bus shared by the ops reasoner and guest intelligence."""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

SURFACES = {"ops", "guest", "both"}


@dataclass
class HotelEvent:
    topic: str
    surface: str
    source: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_class: str | None = None
    verdict: str | None = None

    def __post_init__(self) -> None:
        if self.surface not in SURFACES:
            raise ValueError(f"surface must be ops|guest|both, got {self.surface!r}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "ts": self.ts,
            "topic": self.topic,
            "surface": self.surface,
            "source": self.source,
            "payload": self.payload,
            "evidence_class": self.evidence_class,
            "verdict": self.verdict,
        }


Handler = Callable[[HotelEvent], None]


class EventBus:
    """In-process bus with wildcard subscribe. Redis is optional at deploy time."""

    def __init__(self) -> None:
        self._subs: dict[str, list[Handler]] = defaultdict(list)
        self._history: list[HotelEvent] = []
        self._lock = threading.Lock()

    def publish(self, event: HotelEvent | dict[str, Any]) -> HotelEvent:
        if isinstance(event, dict):
            event = HotelEvent(**{k: v for k, v in event.items() if k in HotelEvent.__dataclass_fields__})
        with self._lock:
            self._history.append(event)
            handlers = list(self._subs.get(event.topic, []))
            for pattern, hs in self._subs.items():
                if pattern.endswith("*") and event.topic.startswith(pattern[:-1]):
                    handlers.extend(hs)
                if pattern == "*" or pattern == event.surface + ".*":
                    handlers.extend(hs)
        for handler in handlers:
            handler(event)
        return event

    def subscribe(self, topic: str, handler: Handler) -> None:
        with self._lock:
            self._subs[topic].append(handler)

    def history(
        self,
        *,
        surface: str | None = None,
        topic_prefix: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._history)
        if surface:
            rows = [e for e in rows if e.surface in {surface, "both"}]
        if topic_prefix:
            rows = [e for e in rows if e.topic.startswith(topic_prefix)]
        return [e.as_dict() for e in rows[-limit:]]

    def clear(self) -> None:
        with self._lock:
            self._history.clear()


_BUS: EventBus | None = None


def get_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS


def reset_bus() -> EventBus:
    global _BUS
    _BUS = EventBus()
    return _BUS
