from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class GateStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    PASS = "PASS"
    HOLD = "HOLD"
    STOP = "STOP"


class CaseStatus(str, Enum):
    INTAKE = "INTAKE"
    INVESTIGATING = "INVESTIGATING"
    WAITING_HUMAN = "WAITING_HUMAN"
    PILOT_READY = "PILOT_READY"
    HOLD = "HOLD"
    STOP = "STOP"


class FitStatus(str, Enum):
    MATCH = "MATCH"
    GAP = "GAP"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class Fact(BaseModel):
    key: str
    label: str
    value: Any | None = None
    unit: str | None = None
    source: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"
    confirmed_by_human: bool = False
    note: str | None = None


class DocumentRecord(BaseModel):
    id: str
    filename: str
    owner: Literal["supplier", "receiver", "shared", "expert"]
    kind: str
    simulated: bool = True
    uploaded_at: str
    summary: str
    extracted_fact_keys: list[str] = []
    text_excerpt: str | None = None
    analysis_method: str = "deterministic"
    ai_summary: str | None = None


class ResourceProfile(BaseModel):
    company: str
    resource_name: str
    process_source: str
    quantity_per_day: float | None = None
    quantity_unit: str = "m³/ngày"
    schedule: str = "Chưa rõ"
    stability: str = "Chưa rõ"
    current_route: str = "Chưa rõ"
    location: str = ""
    quality: dict[str, float | str | None] = {}
    facts: list[Fact] = []


class RequirementProfile(BaseModel):
    company: str
    intended_use: str
    demand_per_day: float | None = None
    demand_unit: str = "m³/ngày"
    schedule: str = "Chưa rõ"
    continuity_requirement: str = "Chưa rõ"
    location: str = ""
    quality_requirements: dict[str, dict[str, Any]] = {}
    facts: list[Fact] = []


class CompatibilityItem(BaseModel):
    id: str
    label: str
    status: FitStatus
    supplier_value: str
    receiver_requirement: str
    explanation: str
    missing_evidence: str | None = None
    evidence_refs: list[str] = []


class EvidenceCandidate(BaseModel):
    id: str
    label: str
    domain: Literal["legal", "quality", "continuity", "engineering", "economics", "data", "custom"]
    description: str
    gate_id: str
    prerequisites: list[str] = []
    hard_gate: bool = False
    downstream_dependencies: int = Field(default=0, ge=0)
    uncertainty_level: Literal["low", "medium", "high"] = "medium"
    cost_index: float = Field(default=0.5, ge=0, le=1)
    time_index: float = Field(default=0.5, ge=0, le=1)
    cost_label: str
    time_label: str
    source_hint: str
    action_owner: str
    rationale: list[str] = []
    generated_from: list[str] = []


class CandidateAssessment(BaseModel):
    candidate_id: str
    label: str
    available: bool
    selected: bool = False
    priority_band: Literal["Rất cao", "Cao", "Trung bình", "Thấp"]
    score: float
    factors: dict[str, str]
    why_selected: list[str] = []
    why_not_selected: list[str] = []


class Gate(BaseModel):
    id: str
    label: str
    domain: str
    status: GateStatus = GateStatus.UNKNOWN
    evidence_id: str | None = None
    source: str | None = None
    note: str | None = None
    human_required: bool = False
    hard_gate: bool = False
    source_document_id: str | None = None


class HumanApproval(BaseModel):
    role: str
    label: str
    required: bool = True
    approved: bool = False
    approved_by: str | None = None
    note: str | None = None


class CustomConstraint(BaseModel):
    id: str
    label: str
    description: str
    hard: bool = False
    status: GateStatus = GateStatus.UNKNOWN
    added_by: str = "Người vận hành"


class AuditEvent(BaseModel):
    ts: str
    actor: str
    event: str
    detail: str
    severity: Literal["info", "warning", "critical"] = "info"


class TraceStep(BaseModel):
    id: str
    label: str
    status: Literal["done", "active", "waiting", "blocked"]
    summary: str
    details: list[str] = []


class AgentDecision(BaseModel):
    status: CaseStatus
    next_evidence_id: str | None = None
    next_evidence_label: str | None = None
    priority_band: str | None = None
    rationale: list[str] = []
    rejected_alternatives: list[str] = []
    blocked_reason: str | None = None
    human_action: str | None = None
    candidate_assessments: list[CandidateAssessment] = []
    trace: list[TraceStep] = []
    human_override_active: bool = False
    override_reason: str | None = None
    planner_mode: str = "deterministic-fallback"
    planner_provider: str | None = None
    planner_model: str | None = None
    planner_note: str | None = None


class DecisionPack(BaseModel):
    decision: str
    headline: str
    summary: str
    supplier_available_per_day: float | None = None
    receiver_demand_per_day: float | None = None
    matched_volume_per_day: float | None = None
    supplier_utilization_pct: float | None = None
    receiver_coverage_pct: float | None = None
    compatibility_summary: dict[str, int] = {}
    verified_conditions: str
    evidence_count: int
    open_risks: list[str] = []
    conditions_for_pilot: list[str] = []
    receiver_output: list[str] = []
    potential_impact: list[str] = []
    economics: list[str] = []
    alternative_paths: list[str] = []
    disclaimer: str


class SynergyCase(BaseModel):
    id: str
    title: str
    short_title: str
    resource: str
    supplier: str
    receiver: str
    location: str
    scenario_label: str
    synthetic: bool = True
    description: str
    supplier_profile: ResourceProfile
    receiver_profile: RequirementProfile
    documents: list[DocumentRecord] = []
    compatibility: list[CompatibilityItem] = []
    gates: list[Gate]
    candidates: list[EvidenceCandidate]
    approvals: list[HumanApproval]
    custom_constraints: list[CustomConstraint] = []
    audit: list[AuditEvent] = []
    agent: AgentDecision | None = None
    decision_pack: DecisionPack | None = None
    human_override_candidate_id: str | None = None
    human_override_reason: str | None = None
    expected_resource_impact: str = ""
    preliminary_value: str = ""


class EvidenceSubmission(BaseModel):
    evidence_id: str
    outcome: Literal["PASS", "HOLD", "STOP"]
    source: str = "Tài liệu demo"
    note: str = ""
    submitted_by: str = "Người vận hành demo"


class ApprovalSubmission(BaseModel):
    role: str
    approved: bool
    approved_by: str = "Người duyệt demo"
    note: str = ""


class ProfileUpdate(BaseModel):
    side: Literal["supplier", "receiver"]
    field: str
    value: Any
    edited_by: str = "Người vận hành"
    reason: str = "Điều chỉnh sau khi kiểm tra dữ liệu"


class PlanOverrideSubmission(BaseModel):
    candidate_id: str | None = None
    reason: str
    actor: str = "Người vận hành"


class ConstraintSubmission(BaseModel):
    label: str
    description: str
    hard: bool = False
    actor: str = "Người vận hành"
