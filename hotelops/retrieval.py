"""Hybrid retrieval: lexical overlap + structured kit chunks. No remote embedder."""

from __future__ import annotations

import math
import re
from typing import Any

from domain_kit.loader import load_kit

_TOKEN = re.compile(r"[a-z0-9_]{3,}")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def _chunks() -> list[dict[str, Any]]:
    kit = load_kit()
    rows: list[dict[str, Any]] = []
    for m in kit.pre_opening_milestones["milestones"]:
        rows.append(
            {
                "id": m["id"],
                "source": "pre_opening",
                "text": f"{m['id']} {m['name']} gate={m['gate']} deliverables={' '.join(m['deliverables'])}",
            }
        )
    for case in kit.evidence_invalidity_cases["cases"]:
        rows.append(
            {
                "id": case["id"],
                "source": "engineering",
                "text": f"{case['id']} {case['title']} {case['effect']} {case['required_remediation']}",
            }
        )
    for lic in kit.licensing_uae["licenses"] + kit.licensing_generic["licenses"]:
        rows.append(
            {
                "id": lic["id"],
                "source": "licensing",
                "text": f"{lic['id']} {lic['name']} {lic.get('class_b_note', '')} prereq={' '.join(lic.get('prerequisites') or [])}",
            }
        )
    for task in kit.ppm_uae_statutory.get("tasks") or []:
        rows.append(
            {
                "id": task["id"],
                "source": "ppm",
                "text": f"{task['id']} {task.get('asset_type')} statutory={task.get('statutory_duty')} {task.get('authority')} sop_required frequency_not_estimated",
            }
        )
    # KSA packs are stripped — do not index licensing_ksa.
    for stage in kit.booking_funnel["stages"]:
        rows.append(
            {
                "id": stage["id"],
                "source": "guest",
                "text": f"funnel {stage['id']} signals={' '.join(stage['signals'])}",
            }
        )
    return rows


def retrieve(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    q = _tokens(query)
    scored: list[dict[str, Any]] = []
    for chunk in _chunks():
        tokens = _tokens(chunk["text"])
        if not tokens:
            continue
        overlap = len(q & tokens)
        lexical = overlap / math.sqrt(len(tokens))
        if overlap == 0:
            continue
        scored.append({**chunk, "score": round(lexical, 4), "overlap": overlap})
    scored.sort(key=lambda r: (-r["score"], r["id"]))
    return scored[:limit]
