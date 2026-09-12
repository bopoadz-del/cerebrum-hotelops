"""PPM resolver — refuse unless statutory row and operator SOP are present."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reasoning.market_router import MarketRouter


class PPMRefuse(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "code": self.code, "message": self.message}


@dataclass
class PPMWorkOrder:
    task_id: str
    asset_type: str
    cadence_days: int
    market: str
    sop_present: bool
    authority: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "asset_type": self.asset_type,
            "cadence_days": self.cadence_days,
            "market": self.market,
            "sop_present": self.sop_present,
            "authority": self.authority,
            "status": "issued",
        }


class PPMResolver:
    def __init__(self) -> None:
        self.router = MarketRouter()

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
        tasks = pack.get("tasks") or []
        match = None
        for row in tasks:
            if task_id and row["id"] == task_id:
                match = row
                break
            if row["asset_type"] == asset_type:
                match = row
                break

        if code == "uae" and match is None:
            raise PPMRefuse(
                "statutory_missing",
                f"No UAE statutory PPM row for asset_type={asset_type!r} task_id={task_id!r}.",
            )
        if code == "generic" and match is None:
            if not (operator_sop and operator_sop.strip()):
                raise PPMRefuse(
                    "sop_missing",
                    "Generic market has no statutory table; operator SOP is required.",
                )
            return PPMWorkOrder(
                task_id=task_id or f"PPM-GEN-{asset_type.upper()}",
                asset_type=asset_type,
                cadence_days=30,
                market=code,
                sop_present=True,
                authority="operator_sop",
            )

        assert match is not None
        if match.get("require_sop") and not (operator_sop and operator_sop.strip()):
            raise PPMRefuse(
                "sop_missing",
                f"PPM {match['id']} requires an operator SOP body. "
                "See domain_kit/ppm/operator_sop/README.md — empty mounts are refused.",
            )
        return PPMWorkOrder(
            task_id=match["id"],
            asset_type=match["asset_type"],
            cadence_days=int(match["cadence_days"]),
            market=code,
            sop_present=True,
            authority=match["authority"],
        )
