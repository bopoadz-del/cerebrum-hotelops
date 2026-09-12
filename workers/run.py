"""Fixture ingest worker. Safe offline; live connectors only when env is set."""

from __future__ import annotations

import time

from connectors import get_connector
from hotelops.db import init_db
from hotelops.event_bus import get_bus
from vision.edge import ingest as vision_ingest

PACKS = [
    ("opera", "reservations"),
    ("opera", "in_house"),
    ("micros", "checks"),
    ("loyalty_lms", "profiles"),
    ("grms", "config"),
    ("maximo", "assets"),
    ("gaming_cms", "players"),
]


def tick() -> dict:
    init_db()
    emitted = 0
    for name, resource in PACKS:
        result = get_connector(name).ingest(resource)
        emitted += int(result.get("emitted") or 0)
    for vision_name in ("queue_lobby", "vip_opt_in", "floor_occupancy", "fm_safety"):
        vision_ingest(vision_name)
    return {"emitted": emitted, "bus": len(get_bus().history())}


def main() -> None:
    while True:
        print(tick(), flush=True)
        time.sleep(30)


if __name__ == "__main__":
    main()
