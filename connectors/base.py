"""Base connector: connect → fetch → normalise → emit. Fixtures unless live env is set."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx

from hotelops.event_bus import HotelEvent, get_bus
from hotelops.settings import get_settings


class ConnectorError(RuntimeError):
    pass


class BaseConnector(ABC):
    name: str
    source: str
    surface: str = "both"
    live_env_keys: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.settings = get_settings()
        self.fixture_dir = Path(self.settings.fixture_root) / "connectors" / self.name
        self._connected = False
        self._mode = "fixture"

    def connect(self) -> dict[str, Any]:
        if self.settings.live_enabled(*self.live_env_keys):
            self._mode = "live"
            self._connected = True
            return {"status": "connected", "mode": "live", "connector": self.name}
        if not self.fixture_dir.is_dir():
            raise ConnectorError(f"No fixture pack for {self.name} at {self.fixture_dir}")
        self._mode = "fixture"
        self._connected = True
        return {"status": "connected", "mode": "fixture", "connector": self.name}

    def fetch(self, resource: str, **params: Any) -> Any:
        if not self._connected:
            self.connect()
        if self._mode == "live":
            return self.fetch_live(resource, **params)
        return self.fetch_fixture(resource, **params)

    def fetch_fixture(self, resource: str, **params: Any) -> Any:
        path = self.fixture_dir / f"{resource}.json"
        if not path.exists():
            raise ConnectorError(f"Fixture {path.name} missing for {self.name}")
        data = json.loads(path.read_text())
        record_id = params.get("id")
        if record_id and isinstance(data, dict) and "records" in data:
            for row in data["records"]:
                if str(row.get("id")) == str(record_id):
                    return row
            raise ConnectorError(f"{resource} id={record_id} not in {self.name} fixtures")
        return data

    def fetch_live(self, resource: str, **params: Any) -> Any:
        url = self.live_url(resource)
        headers = self.live_headers()
        resp = httpx.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def live_url(self, resource: str) -> str:
        raise ConnectorError(f"{self.name} live URL not configured")

    def live_headers(self) -> dict[str, str]:
        return {}

    @abstractmethod
    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        ...

    def emit(self, events: list[HotelEvent]) -> list[dict[str, Any]]:
        bus = get_bus()
        return [bus.publish(event).as_dict() for event in events]

    def ingest(self, resource: str, **params: Any) -> dict[str, Any]:
        raw = self.fetch(resource, **params)
        events = self.normalise(resource, raw)
        published = self.emit(events)
        return {
            "connector": self.name,
            "mode": self._mode,
            "resource": resource,
            "emitted": len(published),
            "events": published,
        }
