"""Pre-opening dependency graph, critical path, cascade simulator, LRM alerts."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from domain_kit.loader import load_kit
from reasoning.sheet import class_b_meta


@dataclass
class MilestoneState:
    milestone_id: str
    duration_days: int
    slip_days: int = 0
    remaining_days: int | None = None
    missing_license: bool = False
    grms_room_map_incomplete: bool = False
    fire_pump_evidence_class: str | None = None


@dataclass
class CascadeResult:
    order: list[str]
    earliest_start: dict[str, int]
    earliest_finish: dict[str, int]
    latest_start: dict[str, int]
    latest_finish: dict[str, int]
    float_days: dict[str, int]
    critical_path: list[str]
    project_days: int
    simulated_finish_days: int
    slipped: dict[str, int]
    lrm_alerts: list[dict[str, Any]] = field(default_factory=list)
    recommended_mitigations: list[dict[str, Any]] = field(default_factory=list)
    master_pacer: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "earliest_start": self.earliest_start,
            "earliest_finish": self.earliest_finish,
            "latest_start": self.latest_start,
            "latest_finish": self.latest_finish,
            "float_days": self.float_days,
            "critical_path": self.critical_path,
            "project_days": self.project_days,
            "simulated_finish_days": self.simulated_finish_days,
            "slipped": self.slipped,
            "lrm_alerts": self.lrm_alerts,
            "recommended_mitigations": self.recommended_mitigations,
            "master_pacer": self.master_pacer,
            **class_b_meta(),
        }


class CascadeEngine:
    def __init__(self) -> None:
        kit = load_kit()
        self.milestones = {m["id"]: m for m in kit.pre_opening_milestones["milestones"]}
        self.edges = kit.pre_opening_cascade["edges"]
        self.slip_multipliers = kit.pre_opening_cascade["slip_multipliers"]
        self.lrm = kit.pre_opening_lrm
        self.cascade_rules = kit.pre_opening_cascade_rules
        self.mitigations = {m["id"]: m for m in kit.pre_opening_mitigations["library"]}
        self.mitigations_by_programme: dict[str, list[dict[str, Any]]] = {}
        for m in kit.pre_opening_mitigations["library"]:
            self.mitigations_by_programme.setdefault(m.get("programme_milestone") or m.get("milestone"), []).append(m)
        self.successors: dict[str, list[tuple[str, int, bool]]] = defaultdict(list)
        self.predecessors: dict[str, list[tuple[str, int, bool]]] = defaultdict(list)
        for edge in self.edges:
            self.successors[edge["from"]].append((edge["to"], int(edge.get("lag_days", 0)), bool(edge.get("critical"))))
            self.predecessors[edge["to"]].append((edge["from"], int(edge.get("lag_days", 0)), bool(edge.get("critical"))))

    def topological_order(self) -> list[str]:
        indeg = {mid: 0 for mid in self.milestones}
        for src, dests in self.successors.items():
            for dest, _, _ in dests:
                indeg[dest] = indeg.get(dest, 0) + 1
                indeg.setdefault(src, 0)
        queue = deque(sorted(m for m, d in indeg.items() if d == 0))
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for dest, _, _ in self.successors.get(node, []):
                indeg[dest] -= 1
                if indeg[dest] == 0:
                    queue.append(dest)
        if len(order) != len(self.milestones):
            raise ValueError("pre-opening graph has a cycle")
        return order

    def compute_critical_path(self, states: dict[str, MilestoneState] | None = None) -> CascadeResult:
        states = states or {
            mid: MilestoneState(mid, int(m["duration_days"])) for mid, m in self.milestones.items()
        }
        order = self.topological_order()
        es: dict[str, int] = {mid: 0 for mid in self.milestones}
        ef: dict[str, int] = {}
        for mid in order:
            duration = states[mid].duration_days + states[mid].slip_days
            ef[mid] = es[mid] + duration
            for dest, lag, _ in self.successors.get(mid, []):
                es[dest] = max(es[dest], ef[mid] + lag)

        project = max(ef.values())
        lf: dict[str, int] = {mid: project for mid in self.milestones}
        ls: dict[str, int] = {}
        for mid in reversed(order):
            duration = states[mid].duration_days + states[mid].slip_days
            if self.successors.get(mid):
                lf[mid] = min(ls[dest] - lag for dest, lag, _ in self.successors[mid])
            ls[mid] = lf[mid] - duration

        float_days = {mid: ls[mid] - es[mid] for mid in self.milestones}
        critical = [mid for mid in order if float_days[mid] == 0]
        result = CascadeResult(
            order=order,
            earliest_start=es,
            earliest_finish=ef,
            latest_start=ls,
            latest_finish=lf,
            float_days=float_days,
            critical_path=critical,
            project_days=project,
            simulated_finish_days=project,
            slipped={mid: s.slip_days for mid, s in states.items() if s.slip_days},
        )
        result.master_pacer = self.compute_master_pacer(result)
        return result

    def compute_master_pacer(self, schedule: CascadeResult) -> dict[str, Any]:
        """Last approval on the licensing path — computed, not a constant.

        Sheet §1.2: occupancy is hit by whichever licensing-path node has the
        greatest earliest_finish. Fire/CD usually wins because it sits
        downstream of commissioning, not because we hardcoded a month count.
        """
        rules = self.cascade_rules
        path = list(rules.get("licensing_path_milestones") or [])
        opening = rules.get("opening_milestone", "M14")
        scored = [(schedule.earliest_finish.get(mid, -1), mid) for mid in path if mid in schedule.earliest_finish]
        scored.sort()
        winner = scored[-1][1] if scored else None
        fire_nodes = set(rules.get("fire_cd_milestones") or [])
        kind = "fire_cd" if winner in fire_nodes else "licensing_path"
        return {
            "milestone": winner,
            "kind": kind,
            "earliest_finish": schedule.earliest_finish.get(winner) if winner else None,
            "computed_from": path,
            "method": "max_earliest_finish_on_licensing_path",
            "hits_opening_directly": winner in fire_nodes or winner == opening,
            "mechanism": (rules.get("mechanism") or {}).get("summary"),
            **class_b_meta(),
        }

    def simulate(self, slips: dict[str, int] | None = None, states: dict[str, MilestoneState] | None = None) -> CascadeResult:
        """Apply slips (with compounding multipliers) and emit LRM alerts."""
        states = {
            mid: MilestoneState(mid, int(m["duration_days"])) for mid, m in self.milestones.items()
        } if states is None else {k: MilestoneState(**{**v.__dict__}) if not isinstance(v, MilestoneState) else v for k, v in states.items()}
        slips = slips or {}
        extra_finish = 0
        for mid, days in slips.items():
            states[mid].slip_days += int(days)
            mult = float(self.slip_multipliers.get(mid, {}).get("downstream_days_per_day", 1.0))
            extra_finish += int(round(days * (mult - 1.0)))
            for dest, _, critical in self.successors.get(mid, []):
                if critical:
                    states[dest].slip_days += int(round(days * max(0.0, mult - 1.0)))

        result = self.compute_critical_path(states)
        result.simulated_finish_days = result.project_days + extra_finish
        result.lrm_alerts = self.lrm_alerts(states, result)
        rec: list[dict[str, Any]] = []
        for mid in result.critical_path:
            if states[mid].slip_days:
                rec.extend(self.mitigations_by_programme.get(mid, []))
        if result.master_pacer.get("kind") == "fire_cd":
            rec.extend(self.mitigations_by_programme.get("M13", []))
        # de-dupe by mitigation id
        seen: set[str] = set()
        uniq = []
        for row in rec:
            if row["id"] not in seen:
                seen.add(row["id"])
                uniq.append(row)
        result.recommended_mitigations = uniq
        return result

    def lrm_alerts(self, states: dict[str, MilestoneState], schedule: CascadeResult) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for mid, fl in schedule.float_days.items():
            if fl < 0:
                alerts.append(
                    {
                        "id": "LRM-01",
                        "milestone": mid,
                        "severity": "critical",
                        "action": "resequence_critical_path",
                        "detail": f"{mid} has {fl} days of float.",
                    }
                )
        m07 = states.get("M07")
        if m07 and m07.slip_days >= 7:
            alerts.append(
                {
                    "id": "LRM-02",
                    "milestone": "M07",
                    "severity": "alert",
                    "action": "stand_up_cx_war_room",
                    "detail": f"M07 slipped {m07.slip_days} days.",
                }
            )
        m13 = states.get("M13")
        if m13 and m13.missing_license:
            alerts.append(
                {
                    "id": "LRM-03",
                    "milestone": "M13",
                    "severity": "critical",
                    "action": "block_soft_opening",
                    "detail": "Licensing incomplete — soft opening is blocked.",
                }
            )
        m12 = states.get("M12")
        if m12 and m12.grms_room_map_incomplete:
            alerts.append(
                {
                    "id": "LRM-04",
                    "milestone": "M12",
                    "severity": "alert",
                    "action": "refuse_guest_room_handover",
                    "detail": "GRMS room map is incomplete.",
                }
            )
        for mid, state in states.items():
            klass = state.fire_pump_evidence_class
            if klass in {"C", "D", "Unprovable"}:
                alerts.append(
                    {
                        "id": "LRM-05",
                        "milestone": mid,
                        "severity": "critical",
                        "action": "invalidate_civil_defense_pack",
                        "detail": f"Fire pump evidence class {klass} is not statutory-grade.",
                        **class_b_meta(),
                    }
                )
        if schedule.master_pacer.get("kind") == "fire_cd":
            alerts.append(
                {
                    "id": "LRM-CD-PACER",
                    "milestone": schedule.master_pacer.get("milestone"),
                    "severity": "alert",
                    "action": "treat_fire_cd_as_opening_pacer",
                    "detail": "Computed master pacer is fire/CD (last approval on the licensing path).",
                    **class_b_meta(),
                }
            )
        return alerts
