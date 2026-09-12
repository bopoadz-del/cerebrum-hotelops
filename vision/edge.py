"""Load synthetic edge metadata. Jetson live path only when env is set."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hotelops.event_bus import HotelEvent, get_bus
from hotelops.settings import get_settings
from vision.privacy_guard import guard_frame
from vision.use_cases import interpret


def load_meta(name: str) -> dict[str, Any]:
    path = Path(get_settings().fixture_root) / "vision" / f"{name}.json"
    return json.loads(path.read_text())


def ingest(name: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.jetson_gateway_url and settings.jetson_device_token and not settings.fixture_mode:
        import httpx

        resp = httpx.get(
            f"{settings.jetson_gateway_url.rstrip('/')}/frames/{name}",
            headers={"Authorization": f"Bearer {settings.jetson_device_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        meta = resp.json()
        source = "jetson"
    else:
        meta = load_meta(name)
        source = "fixture"
    privacy = guard_frame(meta)
    interpretation = interpret(meta)
    event = get_bus().publish(
        HotelEvent(
            topic=f"ops.vision.{meta.get('use_case', name)}",
            surface="ops",
            source=source,
            payload={**meta, **interpretation, **privacy},
        )
    )
    return {"status": "ok", "source": source, "event": event.as_dict(), "interpretation": interpretation}
