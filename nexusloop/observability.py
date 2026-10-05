from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
import itertools

from .models import FitStatus, GateStatus, SynergyCase


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> int:
    return int(round(max(low, min(high, value))))


def _pct(num: int, den: int) -> int:
    return 100 if den == 0 else clamp(100 * num / den)


def case_metrics(case: SynergyCase) -> dict[str, Any]:
    compat = case.compatibility or []
    gates = case.gates or []
    approvals = [a for a in case.approvals if a.required]

    matches = sum(1 for x in compat if x.status == FitStatus.MATCH)
    unresolved_compat = sum(1 for x in compat if x.status in {FitStatus.GAP, FitStatus.UNKNOWN})
    conflicts = sum(1 for x in compat if x.status == FitStatus.CONFLICT)
    known_gates = sum(1 for g in gates if g.status != GateStatus.UNKNOWN)
    passed_gates = sum(1 for g in gates if g.status == GateStatus.PASS)
    stopped_gates = sum(1 for g in gates if g.status == GateStatus.STOP)
    approved = sum(1 for a in approvals if a.approved)

    fact_values = []
    for f in case.supplier_profile.facts + case.receiver_profile.facts:
        fact_values.append(f.value is not None)
    quality_values = [v is not None for v in case.supplier_profile.quality.values()]
    required_quality = len(case.receiver_profile.quality_requirements)
    known_quality = sum(1 for v in case.supplier_profile.quality.values() if v is not None)
    structured_fields = [
        case.supplier_profile.quantity_per_day,
        case.receiver_profile.demand_per_day,
        case.supplier_profile.schedule,
        case.receiver_profile.schedule,
        case.supplier_profile.location,
        case.receiver_profile.location,
    ]
    structured_complete = sum(1 for value in structured_fields if value not in (None, "", "Chưa rõ"))
    completeness = _pct(structured_complete + sum(fact_values) + known_quality, len(structured_fields) + len(fact_values) + max(required_quality, len(quality_values)))

    evidence_total = max(1, len(case.candidates))
    evidence_resolved = sum(1 for c in case.candidates for g in gates if g.id == c.gate_id and g.status != GateStatus.UNKNOWN)
    evidence_score = _pct(evidence_resolved, evidence_total)
    compatibility_score = _pct(matches, len(compat))
    gate_score = _pct(passed_gates, len(gates))
    approval_score = _pct(approved, len(approvals))

    # Readiness intentionally comes only from inspectable state; no opaque AI score.
    readiness = clamp(0.32 * compatibility_score + 0.28 * evidence_score + 0.25 * gate_score + 0.15 * approval_score)
    if conflicts or stopped_gates:
        readiness = min(readiness, 25)

    decision = case.decision_pack.decision if case.decision_pack else (case.agent.status.value if case.agent else "INTAKE")
    return {
        "readiness": readiness,
        "compatibility": compatibility_score,
        "evidence": evidence_score,
        "gates": gate_score,
        "approvals": approval_score,
        "data_completeness": completeness,
        "matches": matches,
        "unresolved_compatibility": unresolved_compat,
        "conflicts": conflicts,
        "passed_gates": passed_gates,
        "known_gates": known_gates,
        "stopped_gates": stopped_gates,
        "approved": approved,
        "required_approvals": len(approvals),
        "documents": len(case.documents),
        "decision": decision,
    }


def provenance(case: SynergyCase) -> list[dict[str, Any]]:
    pack = case.decision_pack
    if not pack:
        return []
    supplier = case.supplier_profile.quantity_per_day
    receiver = case.receiver_profile.demand_per_day
    matched = pack.matched_volume_per_day
    return [
        {
            "id": "matched-volume",
            "label": "Lưu lượng có thể ghép",
            "value": matched,
            "unit": case.supplier_profile.quantity_unit,
            "formula": "min(lưu lượng bên A, nhu cầu bên B)",
            "sources": [
                {"label": "Lưu lượng bên A", "value": supplier, "source": "supplier_profile.quantity_per_day"},
                {"label": "Nhu cầu bên B", "value": receiver, "source": "receiver_profile.demand_per_day"},
            ],
        },
        {
            "id": "supplier-utilization",
            "label": "Tỷ lệ sử dụng nguồn A",
            "value": pack.supplier_utilization_pct,
            "unit": "%",
            "formula": "matched_volume / supplier_available × 100",
            "sources": [{"label": "Matched volume", "value": matched, "source": "decision_pack.matched_volume_per_day"}],
        },
        {
            "id": "receiver-coverage",
            "label": "Tỷ lệ đáp ứng nhu cầu B",
            "value": pack.receiver_coverage_pct,
            "unit": "%",
            "formula": "matched_volume / receiver_demand × 100",
            "sources": [{"label": "Matched volume", "value": matched, "source": "decision_pack.matched_volume_per_day"}],
        },
    ]


def live_flow(case: SynergyCase, ai_status: Any) -> list[dict[str, Any]]:
    trace = list(case.agent.trace if case.agent else [])
    steps: list[dict[str, Any]] = []
    for step in trace[:2]:
        steps.append({"id": step.id, "label": step.label, "status": step.status, "summary": step.summary, "details": step.details, "layer": "data"})

    planner_mode = case.agent.planner_mode if case.agent else "deterministic-fallback"
    ai_active = bool(getattr(ai_status, "active", False))
    ai_label = getattr(ai_status, "provider_label", None) or "Deterministic planner"
    ai_model = getattr(ai_status, "model", None) or "rule-based fallback"
    ai_error = getattr(ai_status, "last_error", None)
    steps.append({
        "id": "ai",
        "label": "AI evidence planner",
        "status": "done" if (planner_mode == "llm-api" or not ai_error) else "blocked",
        "summary": f"{ai_label} · {ai_model}" if ai_active else "Chạy bằng bộ lập kế hoạch xác định, có thể kiểm toán.",
        "details": [f"Planner mode: {planner_mode}"] + ([f"Lỗi provider: {ai_error}"] if ai_error else []),
        "layer": "ai",
    })
    for step in trace[2:]:
        steps.append({"id": step.id, "label": step.label, "status": step.status, "summary": step.summary, "details": step.details, "layer": "decision"})
    steps.append({
        "id": "pack",
        "label": "Sinh Decision Pack",
        "status": "done" if case.decision_pack else "waiting",
        "summary": case.decision_pack.headline if case.decision_pack else "Chưa có báo cáo quyết định.",
        "details": case.decision_pack.open_risks[:4] if case.decision_pack else [],
        "layer": "output",
    })
    return steps


@dataclass
class RunRecord:
    id: str
    case_id: str
    action: str
    label: str
    status: str = "running"
    started_at: str = field(default_factory=now_iso)
    ended_at: str | None = None
    duration_ms: int | None = None
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: dict[str, Any] | None = None
    actor: str = "Người vận hành"


class RunTracker:
    """Small in-memory execution history for the demo UI.

    It never changes decision logic. It snapshots inspectable before/after state
    around real domain actions so the UI can replay what actually happened.
    """

    def __init__(self, max_runs: int = 80):
        self.max_runs = max_runs
        self._runs: list[RunRecord] = []
        self._counter = itertools.count(1)
        self._timers: dict[str, float] = {}

    def start(self, case: SynergyCase, action: str, label: str, actor: str = "Người vận hành") -> RunRecord:
        rid = f"NL-{datetime.now(timezone.utc).strftime('%m%d%H%M%S')}-{next(self._counter):03d}"
        run = RunRecord(id=rid, case_id=case.id, action=action, label=label, before=case_metrics(case), actor=actor)
        self._runs.insert(0, run)
        self._runs = self._runs[: self.max_runs]
        self._timers[rid] = perf_counter()
        return run

    def complete(self, run: RunRecord, case: SynergyCase, ai_status: Any) -> RunRecord:
        start = self._timers.pop(run.id, perf_counter())
        run.status = "completed"
        run.ended_at = now_iso()
        run.duration_ms = max(0, int((perf_counter() - start) * 1000))
        run.after = case_metrics(case)
        run.steps = live_flow(case, ai_status)
        return run

    def fail(self, run: RunRecord, exc: Exception, component: str = "NexusLoop Core") -> RunRecord:
        start = self._timers.pop(run.id, perf_counter())
        run.status = "failed"
        run.ended_at = now_iso()
        run.duration_ms = max(0, int((perf_counter() - start) * 1000))
        run.error = {
            "component": component,
            "message": str(exc),
            "recoverable": True,
            "suggested_actions": ["Kiểm tra dữ liệu đầu vào", "Mở chi tiết bước lỗi", "Sửa dữ liệu rồi chạy lại bước này"],
        }
        return run

    def list(self, case_id: str | None = None) -> list[dict[str, Any]]:
        runs = [r for r in self._runs if case_id is None or r.case_id == case_id]
        return [asdict(r) for r in runs]

    def get(self, run_id: str) -> dict[str, Any] | None:
        run = next((r for r in self._runs if r.id == run_id), None)
        return asdict(run) if run else None

    def clear_case(self, case_id: str) -> None:
        self._runs = [r for r in self._runs if r.case_id != case_id]
