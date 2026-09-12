"""IBM Maximo CMMS — structured asset ingest only (no Aconex/Procore/BIM)."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector, ConnectorError
from hotelops.event_bus import HotelEvent
from reasoning.guard import guard_request


class MaximoConnector(BaseConnector):
    name = "maximo"
    source = "maximo_cmms"
    live_env_keys = ("maximo_base_url", "maximo_api_key")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.maximo_base_url.rstrip('/')}/os/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"apikey": self.settings.maximo_api_key}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        if resource == "assets":
            guard_request(source_system="maximo")
            records = raw.get("records", raw if isinstance(raw, list) else [raw])
            for row in records:
                src = (row.get("source_system") or "maximo").lower()
                if src in {"aconex", "procore", "bim", "bim_ifc"}:
                    raise ConnectorError(f"Asset {row.get('asset_id')} source {src} is out of scope")
            return [
                HotelEvent(
                    topic="ops.engineering.asset",
                    surface="ops",
                    source=self.source,
                    payload={
                        "asset_id": row.get("asset_id") or row.get("id"),
                        "asset_type": row.get("asset_type"),
                        "serial_number": row.get("serial_number"),
                        "location": row.get("location"),
                        "evidence_class": row.get("evidence_class"),
                        "statutory_flag": row.get("statutory_flag", False),
                        "source_system": row.get("source_system", "maximo"),
                    },
                    evidence_class=row.get("evidence_class"),
                )
                for row in records
            ]
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        return [
            HotelEvent(
                topic="ops.cmms.workorder",
                surface="ops",
                source=self.source,
                payload={"wo": row.get("wo") or row.get("id"), "asset_id": row.get("asset_id"), "status": row.get("status")},
            )
            for row in records
        ]
