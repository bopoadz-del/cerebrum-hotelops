"""Two-layer PPM — statutory floor + named operator SOP. Never estimate frequency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reasoning.market_router import MarketRouter
from reasoning.sheet import class_b_meta


class PPMRefuse(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "code": self.code, "message": self.message, **class_b_meta()}


@dataclass
class PPMWorkOrder:
    task_id: str
    asset_type: str
    market: str
    sop_present: bool
    authority: str
    statutory_duty: str | None = None
    cadence_days: int | None = None
    cadence_authoritative: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "asset_type": self.asset_type,
            "cadence_days": self.cadence_days,
            "cadence_authoritative": False,
            "cadence_note": "Frequency is not estimated. Refer to the named operator SOP and the statute.",
            "market": self.market,
            "sop_present": self.sop_present,
            "authority": self.authority,
            "statutory_duty": self.statutory_duty,
            "status": "issued",
            **class_b_meta(),
        }


class PPMResolver:
    def __init__(self) -> None:
        self.router = MarketRouter()

    def _duty_for(self, pack: dict[str, Any], asset_type: str) -> dict[str, Any] | None:
        for duty in pack.get("duties") or []:
            if asset_type in (duty.get("asset_types") or []):
                return duty
        return None

    def resolve(
        self,
        *,
        market: str,
        asset_type: str,
        operator_sop: str | None,
        task_id: str | None = None,
    ) -> PPMWorkOrder:
        pack = self.router.ppm_pack(market)
        code = self.router.normalize(market)
        if pack.get("authoritative_frequencies"):
            raise PPMRefuse(
                "generic_frequency_refused",
                "A generic frequency table cannot be treated as authoritative.",
            )

        tasks = pack.get("tasks") or []
        match = None
        for row in tasks:
            if task_id and row["id"] == task_id:
                match = row
                break
            if row.get("asset_type") == asset_type:
                match = row
                break
        duty = self._duty_for(pack, asset_type)

        if match is None and duty is None and code == "uae":
            raise PPMRefuse(
                "statutory_missing",
                f"No statutory-floor duty for asset_type={asset_type!r} in UAE (fire/lift/pressure/water).",
            )

        named = operator_sop and operator_sop.strip() and len(operator_sop.strip()) > 8
        if not named:
            raise PPMRefuse(
                "sop_missing",
                "Named operator SOP is required. See domain_kit/ppm/operator_sop/README.md. "
                "Frequencies are never estimated from the sheet.",
            )

        if match:
            return PPMWorkOrder(
                task_id=match["id"],
                asset_type=match.get("asset_type", asset_type),
                market=code,
                sop_present=True,
                authority=match.get("authority", "operator_sop"),
                statutory_duty=match.get("statutory_duty") or (duty or {}).get("id"),
            )
        return PPMWorkOrder(
            task_id=task_id or (duty or {}).get("legacy_task_id") or f"PPM-{asset_type.upper()}",
            asset_type=asset_type,
            market=code,
            sop_present=True,
            authority=(duty or {}).get("authority", "operator_sop"),
            statutory_duty=(duty or {}).get("id"),
        )
