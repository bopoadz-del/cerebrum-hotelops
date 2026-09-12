"""License prerequisite evaluation — UAE + generic, three-valued."""

from __future__ import annotations

from typing import Any

from reasoning.evidence import Verdict, combine_verdicts
from reasoning.market_router import MarketRouter
from reasoning.sheet import class_b_meta


class LicensingEngine:
    def __init__(self) -> None:
        self.router = MarketRouter()

    def evaluate(self, market: str, satisfied: dict[str, str] | None = None) -> dict[str, Any]:
        """`satisfied` maps license/prereq id → PASS|FAIL|UNPROVABLE."""
        pack = self.router.licensing_pack(market)
        satisfied = {k: v.upper() for k, v in (satisfied or {}).items()}
        results: list[dict[str, Any]] = []
        mapped = pack.get("prerequisites") or {}
        for lic in pack["licenses"]:
            prereqs = list(lic.get("prerequisites") or [])
            extra = mapped.get(lic["id"], [])
            needed = list(dict.fromkeys(prereqs + extra))
            prereq_verdicts = []
            missing = []
            for item in needed:
                raw = satisfied.get(item)
                if raw is None:
                    prereq_verdicts.append(Verdict.UNPROVABLE)
                    missing.append(item)
                else:
                    prereq_verdicts.append(Verdict(raw))
            if lic["id"] in satisfied:
                own = Verdict(satisfied[lic["id"]])
            elif not needed:
                own = Verdict.UNPROVABLE
            else:
                own = combine_verdicts(prereq_verdicts)
            results.append(
                {
                    "id": lic["id"],
                    "name": lic["name"],
                    "verdict": own.value,
                    "missing_prerequisites": missing,
                    "optional": bool(lic.get("optional")),
                }
            )
        blocking = [r for r in results if r["verdict"] != "PASS" and not r["optional"]]
        overall = combine_verdicts(Verdict(r["verdict"]) for r in results if not r["optional"])
        fire_ids = {"UAE-CD", "GEN-FIRE"}
        fire_rows = [r for r in results if r["id"] in fire_ids]
        pacer = None
        if fire_rows and fire_rows[0]["verdict"] != "PASS":
            pacer = fire_rows[0]["id"]
        elif blocking:
            pacer = max(blocking, key=lambda r: len(r["missing_prerequisites"]))["id"]
        return {
            "market": pack["market"],
            "overall": overall.value,
            "licenses": results,
            "soft_opening_blocked": any(
                r["id"] in {"UAE-CD", "UAE-DTCM", "GEN-FIRE", "GEN-TOURISM"}
                and r["verdict"] != "PASS"
                for r in results
            ),
            "blocking": blocking,
            "master_pacer": {
                "license_id": pacer,
                "kind": "fire_cd" if pacer in fire_ids else "licensing_path",
                "method": "computed_from_prerequisite_graph",
                **class_b_meta(),
            },
            **class_b_meta(),
        }
