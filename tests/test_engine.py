from pathlib import Path

from nexusloop.models import ApprovalSubmission, CaseStatus, EvidenceSubmission, PlanOverrideSubmission, ProfileUpdate
from nexusloop.store import CaseStore

SEED = Path(__file__).resolve().parents[1] / "data" / "demo_cases.json"


def test_input_profiles_produce_compatibility_matrix():
    store = CaseStore(SEED)
    case = store.get("water-reuse-ab")
    ids = {x.id for x in case.compatibility}
    assert {"quantity", "quality", "continuity", "legal", "economics"}.issubset(ids)
    quantity = next(x for x in case.compatibility if x.id == "quantity")
    assert quantity.status.value == "MATCH"
    quality = next(x for x in case.compatibility if x.id == "quality")
    assert quality.status.value == "GAP"


def test_hard_gate_cannot_be_overridden():
    store = CaseStore(SEED)
    case = store.get("safety-stop-demo")
    assert case.agent.status == CaseStatus.STOP
    assert case.agent.next_evidence_id is None
    assert "ghi đè" in " ".join(case.agent.rationale).lower()


def test_agent_selects_legal_first_and_explains_alternatives():
    store = CaseStore(SEED)
    case = store.get("water-reuse-ab")
    assert case.agent.next_evidence_id == "legal-review"
    selected = next(x for x in case.agent.candidate_assessments if x.selected)
    assert selected.priority_band in {"Rất cao", "Cao"}
    assert selected.why_selected
    assert any(x.why_not_selected for x in case.agent.candidate_assessments if not x.selected)


def test_replanning_moves_from_legal_to_quality():
    store = CaseStore(SEED)
    case = store.submit_evidence(
        "water-reuse-ab",
        EvidenceSubmission(evidence_id="legal-review", outcome="PASS", source="Demo legal memo", submitted_by="Environmental Officer"),
    )
    assert case.agent.status == CaseStatus.INVESTIGATING
    assert case.agent.next_evidence_id == "water-lab"


def test_human_can_change_available_plan_and_audit_it():
    store = CaseStore(SEED)
    # At seed only legal is available. Make legal & quality pass so continuity is available.
    store.submit_evidence("water-reuse-ab", EvidenceSubmission(evidence_id="legal-review", outcome="PASS"))
    store.submit_evidence("water-reuse-ab", EvidenceSubmission(evidence_id="water-lab", outcome="PASS"))
    case = store.get("water-reuse-ab")
    assert case.agent.next_evidence_id == "continuity-check"
    # Human selecting the same available action still records an explicit override.
    case = store.override_plan("water-reuse-ab", PlanOverrideSubmission(candidate_id="continuity-check", reason="Ưu tiên vì lịch sản xuất tuần tới thay đổi"))
    assert case.agent.human_override_active is True
    assert "người vận hành" in case.audit[0].detail.lower() or "người" in case.audit[0].detail.lower()


def test_human_profile_edit_recomputes_output():
    store = CaseStore(SEED)
    case = store.update_profile("water-reuse-ab", ProfileUpdate(side="receiver", field="demand_per_day", value=380, reason="Kế hoạch ca mới"))
    assert case.receiver_profile.demand_per_day == 380
    assert case.decision_pack.matched_volume_per_day == 380
    assert case.decision_pack.receiver_coverage_pct == 100.0


def test_full_path_requires_human_approval_before_ready():
    store = CaseStore(SEED)
    for evidence_id in ["legal-review", "water-lab", "continuity-check", "engineering-survey"]:
        case = store.submit_evidence("water-reuse-ab", EvidenceSubmission(evidence_id=evidence_id, outcome="PASS", source="Synthetic test"))
    assert case.agent.status == CaseStatus.WAITING_HUMAN
    for role in ["environmental_officer", "process_engineer"]:
        case = store.approve("water-reuse-ab", ApprovalSubmission(role=role, approved=True, approved_by="Reviewer"))
    assert case.agent.status == CaseStatus.PILOT_READY
    assert case.decision_pack.decision == "PILOT READY"


def test_stop_evidence_stops_case_and_keeps_alternative_paths():
    store = CaseStore(SEED)
    case = store.submit_evidence("water-reuse-ab", EvidenceSubmission(evidence_id="legal-review", outcome="STOP", source="Synthetic blocking rule"))
    assert case.agent.status == CaseStatus.STOP
    assert case.agent.next_evidence_id is None
    assert case.decision_pack.alternative_paths


def test_llm_planner_can_select_only_from_safe_available_candidates(monkeypatch):
    store = CaseStore(SEED)
    # Pretend a model-agnostic provider is active without making a network request.
    class FakeProvider:
        id = 'fake'
        label = 'Fake LLM'
        model = 'fake-model'
    store.ai_runtime.router.current = FakeProvider()
    monkeypatch.setattr(store.ai_runtime, 'choose_candidate', lambda **kwargs: {
        'candidate_id': 'water-lab',
        'why_selected': ['Kiểm tra chất lượng có giá trị quyết định cao trong tình huống giả lập.'],
        'rejected_alternatives': ['Xác minh pháp lý: tạm chưa chọn trong test mô phỏng.'],
        'decision_note': 'Kết quả test của lớp AI tùy chọn.'
    })
    case = store.get('water-reuse-ab')
    store.agent.recompute(case)
    assert case.agent.next_evidence_id == 'water-lab'
    assert case.agent.planner_mode == 'llm-api'
    assert case.agent.planner_provider == 'Fake LLM'
    assert case.agent.planner_model
