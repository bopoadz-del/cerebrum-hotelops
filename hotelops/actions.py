"""ActionRegistry + audited action_runs (action_contract compatible)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from hotelops.db import get_sessionmaker, init_db
from hotelops.event_bus import HotelEvent, get_bus
from hotelops.models import ActionRun

ActionFn = Callable[[dict[str, Any], str, str], dict[str, Any]]


@dataclass
class ActionSpec:
    action_id: str
    description: str
    surfaces: tuple[str, ...]
    handler: ActionFn
    roles: tuple[str, ...] = ("operator", "reviewer")


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        self._actions[spec.action_id] = spec

    def get(self, action_id: str) -> ActionSpec:
        if action_id not in self._actions:
            raise KeyError(action_id)
        return self._actions[action_id]

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "action_id": s.action_id,
                "description": s.description,
                "surfaces": list(s.surfaces),
                "roles": list(s.roles),
            }
            for s in self._actions.values()
        ]

    def run(self, action_id: str, payload: dict[str, Any], *, actor: str, role: str) -> dict[str, Any]:
        spec = self.get(action_id)
        if role not in spec.roles:
            result = {"status": "refused", "error": f"role {role} cannot run {action_id}"}
            self._audit(action_id, actor, role, payload, result, "refused")
            return result
        try:
            result = spec.handler(payload, actor, role)
            status = result.get("status", "ok")
        except Exception as exc:  # noqa: BLE001 — persist the failure, then re-raise shape
            result = {"status": "error", "error": str(exc)}
            status = "error"
        self._audit(action_id, actor, role, payload, result, status)
        get_bus().publish(
            HotelEvent(
                topic=f"ops.action.{action_id}",
                surface="ops",
                source="action_registry",
                payload={"action_id": action_id, "status": status, "actor": actor},
            )
        )
        return result

    def _audit(
        self,
        action_id: str,
        actor: str,
        role: str,
        payload: dict[str, Any],
        result: dict[str, Any],
        status: str,
    ) -> None:
        init_db()
        session = get_sessionmaker()()
        try:
            session.add(
                ActionRun(
                    action_id=action_id,
                    actor=actor,
                    role=role,
                    status=status,
                    input_json=json.dumps(payload, default=str),
                    output_json=json.dumps(result, default=str),
                )
            )
            session.commit()
        finally:
            session.close()


def build_default_registry() -> ActionRegistry:
    from reasoning.cascade_engine import CascadeEngine
    from reasoning.evidence import classify_evidence
    from reasoning.licensing import LicensingEngine
    from reasoning.ppm_resolver import PPMRefuse, PPMResolver

    registry = ActionRegistry()

    def pre_opening(payload: dict[str, Any], actor: str, role: str) -> dict[str, Any]:
        engine = CascadeEngine()
        result = engine.simulate(payload.get("slips") or {})
        return {"status": "ok", "actor": actor, **result.as_dict()}

    def engineering(payload: dict[str, Any], actor: str, role: str) -> dict[str, Any]:
        judged = classify_evidence(payload)
        return {"status": "ok", **judged.as_dict()}

    def licensing(payload: dict[str, Any], actor: str, role: str) -> dict[str, Any]:
        engine = LicensingEngine()
        return {"status": "ok", **engine.evaluate(payload.get("market", "uae"), payload.get("satisfied"))}

    def ppm(payload: dict[str, Any], actor: str, role: str) -> dict[str, Any]:
        try:
            wo = PPMResolver().resolve(
                market=payload.get("market", "uae"),
                asset_type=payload["asset_type"],
                operator_sop=payload.get("operator_sop"),
                task_id=payload.get("task_id"),
            )
        except PPMRefuse as exc:
            return {"status": "refused", **exc.as_dict()}
        return {"status": "ok", **wo.as_dict()}

    registry.register(ActionSpec("pre_opening.simulate", "Run cascade + LRM", ("ops",), pre_opening))
    registry.register(ActionSpec("engineering.classify", "Classify inheritance evidence", ("ops",), engineering))
    registry.register(ActionSpec("licensing.evaluate", "Evaluate UAE/generic licenses", ("ops",), licensing))
    registry.register(ActionSpec("ppm.resolve", "Issue or refuse a PPM work order", ("ops",), ppm))
    return registry


_REGISTRY: ActionRegistry | None = None


def get_registry() -> ActionRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_default_registry()
    return _REGISTRY
