"""Queue, VIP opt-in, floor occupancy, FM safety — metadata only."""

from __future__ import annotations

from typing import Any


def interpret(meta: dict[str, Any]) -> dict[str, Any]:
    use = meta.get("use_case")
    if use == "queue":
        wait = int(meta.get("queue_wait_seconds_est") or 0)
        return {
            "use_case": "queue",
            "severity": "alert" if wait >= 300 else "watch",
            "action": "open_additional_desk" if wait >= 300 else "monitor",
        }
    if use == "vip":
        return {
            "use_case": "vip",
            "severity": "info",
            "action": "notify_guest_relations",
            "vip_ids": list(meta.get("opt_in_vip_ids") or []),
        }
    if use == "floor":
        net = int(meta.get("in_count") or 0) - int(meta.get("out_count") or 0)
        return {"use_case": "floor", "net_occupancy": net, "action": "update_hk_forecast"}
    if use == "fm_safety":
        hazard = bool(meta.get("ppe_missing") or meta.get("hazard"))
        return {
            "use_case": "fm_safety",
            "severity": "critical" if hazard else "ok",
            "action": "dispatch_engineering" if hazard else "none",
        }
    return {"use_case": use or "unknown", "action": "ignore"}
