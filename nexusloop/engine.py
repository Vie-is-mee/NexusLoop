from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite

from .ai_runtime import NexusAIRuntime
from .models import (
    AgentDecision,
    AuditEvent,
    CandidateAssessment,
    CaseStatus,
    CompatibilityItem,
    DecisionPack,
    EvidenceCandidate,
    FitStatus,
    GateStatus,
    SynergyCase,
    TraceStep,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class NexusAgent:
    """Hybrid, auditable decision agent used in the competition demo.

    The agent is deliberately split into transparent layers:
    1) normalize input profiles,
    2) compare supplier output with receiver requirements,
    3) apply hard rules,
    4) rank unresolved evidence actions,
    5) allow human plan intervention,
    6) re-plan after every new piece of evidence.

    The agent never decides legal or engineering truth. Those truths enter as
    sourced evidence or human approvals. This keeps the demo reproducible and
    makes the decision logic inspectable.
    """

    UNCERTAINTY_WEIGHT = {"low": 0.35, "medium": 0.65, "high": 1.0}

    def __init__(self, ai_runtime: NexusAIRuntime | None = None):
        self.ai_runtime = ai_runtime or NexusAIRuntime()

    def gate_map(self, case: SynergyCase):
        return {g.id: g for g in case.gates}

    def _fmt(self, value, unit="") -> str:
        if value is None:
            return "Chưa có dữ liệu"
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return f"{value}{(' ' + unit) if unit else ''}"

    def build_compatibility(self, case: SynergyCase) -> list[CompatibilityItem]:
        s = case.supplier_profile
        r = case.receiver_profile
        gates = self.gate_map(case)
        out: list[CompatibilityItem] = []

        # 1. Resource identity / intended use.
        resource_ok = bool(s.resource_name and r.intended_use)
        out.append(CompatibilityItem(
            id="resource_type",
            label="Loại tài nguyên & mục đích sử dụng",
            status=FitStatus.MATCH if resource_ok else FitStatus.UNKNOWN,
            supplier_value=s.resource_name or "Chưa khai báo",
            receiver_requirement=r.intended_use or "Chưa khai báo",
            explanation=("Đã xác định được loại tài nguyên của bên A và mục đích sử dụng của bên B."
                         if resource_ok else "Thiếu mô tả đầu ra của A hoặc mục đích sử dụng của B."),
            missing_evidence=None if resource_ok else "Bổ sung mô tả quy trình và mục đích sử dụng.",
        ))

        # 2. Quantity.
        if s.quantity_per_day is None or r.demand_per_day is None:
            q_status = FitStatus.UNKNOWN
            q_expl = "Chưa đủ số liệu để so sánh khả năng cung ứng và nhu cầu."
            q_missing = "Cần lưu lượng trung bình của A và nhu cầu/ngày của B."
        elif s.quantity_per_day >= r.demand_per_day:
            q_status = FitStatus.MATCH
            q_expl = f"Nguồn A có thể đáp ứng tối đa nhu cầu khai báo của B ({self._fmt(r.demand_per_day, r.demand_unit)})."
            q_missing = None
        else:
            q_status = FitStatus.GAP
            q_expl = f"Nguồn A chỉ đáp ứng khoảng {round(100*s.quantity_per_day/r.demand_per_day)}% nhu cầu của B; cần phương án bù nguồn hoặc giảm phạm vi pilot."
            q_missing = "Xác nhận mức nhu cầu tối thiểu chấp nhận được của B."
        out.append(CompatibilityItem(
            id="quantity", label="Số lượng / lưu lượng", status=q_status,
            supplier_value=self._fmt(s.quantity_per_day, s.quantity_unit),
            receiver_requirement=self._fmt(r.demand_per_day, r.demand_unit),
            explanation=q_expl, missing_evidence=q_missing,
        ))

        # 3. Quality requirements.
        known = 0
        matched = 0
        conflicts = []
        missing = []
        for param, rule in r.quality_requirements.items():
            val = s.quality.get(param)
            if val is None:
                missing.append(param)
                continue
            known += 1
            try:
                num = float(val)
                ok = True
                if rule.get("max") is not None:
                    ok = ok and num <= float(rule["max"])
                if rule.get("min") is not None:
                    ok = ok and num >= float(rule["min"])
                if ok:
                    matched += 1
                else:
                    conflicts.append(param)
            except (TypeError, ValueError):
                missing.append(param)
        if conflicts:
            qual_status = FitStatus.CONFLICT
            qual_expl = "Một hoặc nhiều chỉ tiêu đã biết không đáp ứng yêu cầu B: " + ", ".join(conflicts) + "."
            qual_missing = "Cần chuyên gia xác nhận khả năng xử lý bổ sung hoặc chọn mục đích sử dụng khác."
        elif missing:
            qual_status = FitStatus.GAP
            qual_expl = f"Đã có {known}/{len(r.quality_requirements)} chỉ tiêu cần thiết; còn thiếu: {', '.join(missing)}."
            qual_missing = "Bổ sung kết quả xét nghiệm cho các chỉ tiêu còn thiếu."
        elif r.quality_requirements:
            qual_status = FitStatus.MATCH
            qual_expl = f"Các {matched}/{len(r.quality_requirements)} chỉ tiêu đã khai báo đều nằm trong ngưỡng mô phỏng của B."
            qual_missing = None
        else:
            qual_status = FitStatus.UNKNOWN
            qual_expl = "B chưa khai báo yêu cầu chất lượng chi tiết."
            qual_missing = "Bổ sung tiêu chuẩn đầu vào hoặc SOP sử dụng."
        quality_gate = gates.get("quality")
        if quality_gate and quality_gate.status == GateStatus.PASS:
            qual_status = FitStatus.MATCH
            qual_expl = quality_gate.note or "Kết quả xét nghiệm đã được ghi nhận là đạt yêu cầu mục tiêu trong phạm vi demo."
            qual_missing = None
        elif quality_gate and quality_gate.status == GateStatus.HOLD:
            qual_status = FitStatus.GAP
            qual_expl = quality_gate.note or "Kết quả chất lượng cần được làm rõ."
        elif quality_gate and quality_gate.status == GateStatus.STOP:
            qual_status = FitStatus.CONFLICT
            qual_expl = quality_gate.note or "Kết quả chất lượng không đáp ứng yêu cầu mục tiêu."
        out.append(CompatibilityItem(
            id="quality", label="Chất lượng", status=qual_status,
            supplier_value=(f"{known}/{len(r.quality_requirements)} chỉ tiêu đã có trong hồ sơ cấu trúc" if r.quality_requirements else "Chưa chuẩn hóa"),
            receiver_requirement=(f"{len(r.quality_requirements)} chỉ tiêu yêu cầu" if r.quality_requirements else "Chưa khai báo"),
            explanation=qual_expl, missing_evidence=qual_missing,
        ))

        # 4. Schedule/continuity.
        schedule_known = s.schedule not in {"", "Chưa rõ"} and r.schedule not in {"", "Chưa rõ"}
        if not schedule_known:
            st_status = FitStatus.UNKNOWN
            st_expl = "Thiếu lịch phát sinh của A hoặc lịch nhu cầu của B."
            st_missing = "Cần nhật ký lưu lượng/lịch vận hành của hai bên."
        elif "liên tục" in s.stability.lower() and "liên tục" in r.continuity_requirement.lower():
            st_status = FitStatus.MATCH
            st_expl = "Nguồn A được mô tả là liên tục và phù hợp yêu cầu ổn định của B ở mức sơ bộ."
            st_missing = None
        else:
            st_status = FitStatus.GAP
            st_expl = "Lịch vận hành có thể phù hợp nhưng độ ổn định nguồn chưa đủ bằng chứng để B phụ thuộc trực tiếp."
            st_missing = "Cần dữ liệu biến động lưu lượng và phương án dự phòng."
        continuity_gate = gates.get("continuity")
        if continuity_gate and continuity_gate.status == GateStatus.PASS:
            st_status = FitStatus.MATCH
            st_expl = continuity_gate.note or "Dữ liệu lưu lượng/lịch vận hành đã được ghi nhận là đủ cho phạm vi pilot mô phỏng."
            st_missing = None
        elif continuity_gate and continuity_gate.status == GateStatus.HOLD:
            st_status = FitStatus.GAP
            st_expl = continuity_gate.note or "Độ ổn định nguồn cần làm rõ."
        elif continuity_gate and continuity_gate.status == GateStatus.STOP:
            st_status = FitStatus.CONFLICT
            st_expl = continuity_gate.note or "Nguồn cung không đáp ứng yêu cầu ổn định."
        out.append(CompatibilityItem(
            id="continuity", label="Thời gian & độ ổn định", status=st_status,
            supplier_value=f"{s.schedule}; {s.stability}",
            receiver_requirement=f"{r.schedule}; {r.continuity_requirement}",
            explanation=st_expl, missing_evidence=st_missing,
        ))

        # 5. Infrastructure is governed by current gate evidence.
        infra = gates.get("infrastructure")
        infra_status = FitStatus.UNKNOWN
        infra_expl = "Chưa có đánh giá hạ tầng."
        if infra:
            if infra.status == GateStatus.PASS:
                infra_status = FitStatus.MATCH
                infra_expl = infra.note or "Khoảng cách và điểm đấu nối sơ bộ cho phép tiếp tục khảo sát."
            elif infra.status == GateStatus.STOP:
                infra_status = FitStatus.CONFLICT
                infra_expl = infra.note or "Hạ tầng hiện tại chặn phương án."
            elif infra.status == GateStatus.HOLD:
                infra_status = FitStatus.GAP
                infra_expl = infra.note or "Hạ tầng cần làm rõ."
        out.append(CompatibilityItem(
            id="infrastructure", label="Hạ tầng & kết nối", status=infra_status,
            supplier_value=s.location or case.location,
            receiver_requirement=r.location or case.location,
            explanation=infra_expl,
            missing_evidence=None if infra_status == FitStatus.MATCH else "Khảo sát tuyến kết nối, bể chứa, bơm/đường ống và điểm đấu nối.",
        ))

        # 6. Legal / regulatory path from gate.
        legal = gates.get("legal")
        legal_status = FitStatus.UNKNOWN
        legal_expl = "Chưa có bằng chứng xác minh đường pháp lý cho mục đích sử dụng này."
        if legal:
            if legal.status == GateStatus.PASS:
                legal_status = FitStatus.MATCH
                legal_expl = legal.note or "Đường triển khai không bị chặn theo bằng chứng hiện có."
            elif legal.status == GateStatus.HOLD:
                legal_status = FitStatus.GAP
                legal_expl = legal.note or "Cần chuyên gia/cơ quan có thẩm quyền làm rõ."
            elif legal.status == GateStatus.STOP:
                legal_status = FitStatus.CONFLICT
                legal_expl = legal.note or "Đường triển khai hiện tại bị chặn."
        out.append(CompatibilityItem(
            id="legal", label="Điều kiện pháp lý", status=legal_status,
            supplier_value="Hồ sơ bên A + mục đích chuyển giao",
            receiver_requirement="Được phép nhận và sử dụng cho mục đích đã khai báo",
            explanation=legal_expl,
            missing_evidence=None if legal_status == FitStatus.MATCH else "Cần memo/xác nhận từ cán bộ môi trường hoặc nguồn quy định đã kiểm tra.",
        ))

        # 7. Economics from gate.
        eco = gates.get("economics")
        eco_status = FitStatus.UNKNOWN
        eco_expl = "Chưa có business case."
        if eco:
            if eco.status == GateStatus.PASS:
                eco_status = FitStatus.MATCH
                eco_expl = eco.note or "Giá trị sơ bộ dương, cần cập nhật sau báo giá kỹ thuật."
            elif eco.status == GateStatus.HOLD:
                eco_status = FitStatus.GAP
                eco_expl = eco.note or "Hiệu quả kinh tế cần làm rõ."
            elif eco.status == GateStatus.STOP:
                eco_status = FitStatus.CONFLICT
                eco_expl = eco.note or "Business case hiện âm."
        out.append(CompatibilityItem(
            id="economics", label="Hiệu quả kinh tế", status=eco_status,
            supplier_value="Chi phí tuyến hiện tại / giá trị tránh được",
            receiver_requirement="Tổng chi phí sau xử lý + vận chuyển phải hợp lý",
            explanation=eco_expl,
            missing_evidence=None if eco_status == FitStatus.MATCH else "Cập nhật CAPEX/OPEX và giá trị tránh được.",
        ))
        return out

    def candidate_score(self, candidate: EvidenceCandidate) -> float:
        uncertainty = self.UNCERTAINTY_WEIGHT[candidate.uncertainty_level]
        dependency = min(candidate.downstream_dependencies / 4.0, 1.0)
        hard = 1.0 if candidate.hard_gate else 0.45
        benefit = 0.35 * uncertainty + 0.30 * dependency + 0.35 * hard
        burden = 0.55 + 0.25 * candidate.cost_index + 0.20 * candidate.time_index
        score = benefit / burden
        return round(score, 3) if isfinite(score) else 0.0

    def priority_band(self, score: float) -> str:
        if score >= 1.15:
            return "Rất cao"
        if score >= 0.85:
            return "Cao"
        if score >= 0.55:
            return "Trung bình"
        return "Thấp"

    def candidate_available(self, case: SynergyCase, candidate: EvidenceCandidate) -> bool:
        gates = self.gate_map(case)
        target = gates.get(candidate.gate_id)
        if target is None or target.status != GateStatus.UNKNOWN:
            return False
        return all(gates.get(p) and gates[p].status == GateStatus.PASS for p in candidate.prerequisites)

    def assessments(self, case: SynergyCase) -> list[CandidateAssessment]:
        scored = []
        gates = self.gate_map(case)
        for c in case.candidates:
            score = self.candidate_score(c)
            available = self.candidate_available(case, c)
            prereq_missing = [p for p in c.prerequisites if gates.get(p) and gates[p].status != GateStatus.PASS]
            why_not = []
            if gates.get(c.gate_id) and gates[c.gate_id].status != GateStatus.UNKNOWN:
                why_not.append("Điều kiện này đã có kết quả nên không cần thu lại bằng chứng.")
            if prereq_missing:
                why_not.append("Chưa mở vì còn phụ thuộc: " + ", ".join(gates[p].label for p in prereq_missing) + ".")
            scored.append(CandidateAssessment(
                candidate_id=c.id,
                label=c.label,
                available=available,
                priority_band=self.priority_band(score),
                score=score,
                factors={
                    "Khả năng thay đổi quyết định": "Rất cao" if c.hard_gate else ("Cao" if c.uncertainty_level == "high" else "Trung bình"),
                    "Số bước phụ thuộc phía sau": str(c.downstream_dependencies),
                    "Mức độ bắt buộc": "Bắt buộc" if c.hard_gate else "Không phải điều kiện chặn",
                    "Chi phí thu bằng chứng": c.cost_label,
                    "Thời gian dự kiến": c.time_label,
                },
                why_not_selected=why_not,
            ))
        return scored

    def _trace(self, case: SynergyCase, assessments: list[CandidateAssessment], selected_id: str | None, blocked: str | None = None) -> list[TraceStep]:
        compat = case.compatibility
        missing = [x for x in compat if x.status in {FitStatus.GAP, FitStatus.UNKNOWN, FitStatus.CONFLICT}]
        available = [a for a in assessments if a.available]
        selected = next((a for a in assessments if a.candidate_id == selected_id), None)
        return [
            TraceStep(id="ingest", label="Đọc hồ sơ A và B", status="done", summary=f"Đã có {len(case.documents)} tài liệu và hai hồ sơ đã chuẩn hóa.", details=[d.filename for d in case.documents[:4]]),
            TraceStep(id="compare", label="Đối chiếu đầu ra A với nhu cầu B", status="done", summary=f"Đã kiểm tra {len(compat)} nhóm điều kiện; {len(missing)} nhóm còn thiếu/xung đột.", details=[f"{x.label}: {x.status.value}" for x in compat]),
            TraceStep(id="rules", label="Kiểm tra điều kiện bắt buộc", status="blocked" if blocked else "done", summary=blocked or "Không có điều kiện bắt buộc đã xác minh là STOP.", details=[]),
            TraceStep(id="options", label="Tạo các việc có thể làm tiếp", status="done", summary=f"Có {len(available)} hành động hiện khả dụng trong {len(assessments)} hành động đang theo dõi.", details=[a.label for a in available]),
            TraceStep(id="rank", label="So sánh giá trị từng bằng chứng", status="done" if available else "waiting", summary=(f"Đã xếp hạng theo mức chặn, số bước phụ thuộc, chi phí và thời gian." if available else "Chưa có hành động khả dụng."), details=[f"{a.label}: {a.priority_band}" for a in sorted(available, key=lambda x:x.score, reverse=True)]),
            TraceStep(id="decide", label="Chọn bước tiếp theo", status="active" if selected else ("blocked" if blocked else "waiting"), summary=(selected.label if selected else blocked or "Chờ dữ liệu/phê duyệt"), details=[]),
            TraceStep(id="act", label="Tạo nhiệm vụ & chờ bằng chứng", status="active" if selected else "waiting", summary=("NexusLoop tạo yêu cầu cho người phụ trách; khi kết quả quay về, hệ thống sẽ tính lại toàn bộ nhánh phụ thuộc." if selected else "Không tạo nhiệm vụ mới."), details=[]),
        ]

    def select_next(self, case: SynergyCase) -> AgentDecision:
        case.compatibility = self.build_compatibility(case)
        gates = self.gate_map(case)

        # Hard constraints and hard gates dominate planning.
        custom_stops = [c for c in case.custom_constraints if c.hard and c.status == GateStatus.STOP]
        hard_stops = [g for g in case.gates if g.hard_gate and g.status == GateStatus.STOP]
        if hard_stops or custom_stops:
            label = hard_stops[0].label if hard_stops else custom_stops[0].label
            blocked = f"Điều kiện bắt buộc ‘{label}’ đã được xác minh là không đạt."
            assessments = self.assessments(case)
            return AgentDecision(
                status=CaseStatus.STOP,
                blocked_reason=blocked,
                rationale=[
                    "AI không được phép ghi đè một điều kiện bắt buộc đã có bằng chứng.",
                    "Dừng đường hiện tại giúp tránh tiếp tục phát sinh xét nghiệm, khảo sát hoặc đầu tư không cần thiết.",
                ],
                human_action="Muốn mở lại đường này phải bổ sung bằng chứng mới hoặc yêu cầu người có thẩm quyền xem xét; không có nút override trực tiếp.",
                candidate_assessments=assessments,
                trace=self._trace(case, assessments, None, blocked),
                planner_mode="rules-only",
                planner_note="Điều kiện bắt buộc được xử lý bằng quy tắc cứng; LLM không có quyền ghi đè.",
            )

        holds = [g for g in case.gates if g.status == GateStatus.HOLD]
        if holds:
            assessments = self.assessments(case)
            blocked = f"‘{holds[0].label}’ đang cần làm rõ."
            return AgentDecision(
                status=CaseStatus.HOLD,
                blocked_reason=blocked,
                rationale=["Kết quả hiện tại chưa đủ chắc chắn để tiếp tục tự động sang nhánh sau."],
                human_action="Bổ sung tài liệu, sửa dữ liệu đã trích hoặc yêu cầu chuyên gia xác nhận.",
                candidate_assessments=assessments,
                trace=self._trace(case, assessments, None, blocked),
                planner_mode="rules-only",
                planner_note="Hệ thống tạm giữ vì bằng chứng chưa đủ; LLM không tự điền dữ liệu thiếu.",
            )

        assessments = self.assessments(case)
        available = [a for a in assessments if a.available]
        selected: CandidateAssessment | None = None
        override_active = False

        if case.human_override_candidate_id:
            override = next((a for a in available if a.candidate_id == case.human_override_candidate_id), None)
            if override:
                selected = override
                override_active = True

        planner_mode = "human-override" if override_active else "deterministic-fallback"
        planner_provider = None
        planner_model = None
        planner_note = None
        llm_plan = None

        if selected is None and available and self.ai_runtime.active:
            candidate_payloads = []
            for a in available:
                c = next(c for c in case.candidates if c.id == a.candidate_id)
                candidate_payloads.append({
                    "candidate_id": c.id,
                    "label": c.label,
                    "description": c.description,
                    "hard_gate": c.hard_gate,
                    "downstream_dependencies": c.downstream_dependencies,
                    "uncertainty_level": c.uncertainty_level,
                    "cost_label": c.cost_label,
                    "time_label": c.time_label,
                    "fallback_priority": a.priority_band,
                    "fallback_score": a.score,
                })
            case_payload = {
                "supplier": {
                    "resource": case.supplier_profile.resource_name,
                    "quantity_per_day": case.supplier_profile.quantity_per_day,
                    "quality": case.supplier_profile.quality,
                    "schedule": case.supplier_profile.schedule,
                    "stability": case.supplier_profile.stability,
                },
                "receiver": {
                    "intended_use": case.receiver_profile.intended_use,
                    "demand_per_day": case.receiver_profile.demand_per_day,
                    "quality_requirements": case.receiver_profile.quality_requirements,
                    "schedule": case.receiver_profile.schedule,
                    "continuity_requirement": case.receiver_profile.continuity_requirement,
                },
                "compatibility": [x.model_dump(mode="json") for x in case.compatibility],
                "gates": [g.model_dump(mode="json") for g in case.gates],
            }
            llm_plan = self.ai_runtime.choose_candidate(case_payload=case_payload, candidates=candidate_payloads)
            if llm_plan:
                selected = next((a for a in available if a.candidate_id == llm_plan.get("candidate_id")), None)
                if selected:
                    planner_mode = "llm-api"
                    planner_provider = self.ai_runtime.status().provider_label
                    planner_model = self.ai_runtime.model
                    planner_note = llm_plan.get("decision_note") or "LLM chọn trong tập phương án đã qua kiểm tra an toàn."

        if selected is None and available:
            selected = max(available, key=lambda a: a.score)
            planner_note = self.ai_runtime.last_error or self.ai_runtime.status().note

        if selected:
            for a in assessments:
                a.selected = a.candidate_id == selected.candidate_id
                if a.selected:
                    c = next(c for c in case.candidates if c.id == a.candidate_id)
                    if llm_plan and not override_active:
                        reasons = llm_plan.get("why_selected") or []
                        a.why_selected = [str(x) for x in reasons[:4]] or list(c.rationale)
                    else:
                        a.why_selected = list(c.rationale) + [
                            f"Bước này ảnh hưởng {c.downstream_dependencies} bước phụ thuộc phía sau.",
                            f"Chi phí {c.cost_label.lower()} và thời gian {c.time_label.lower()} so với rủi ro có thể loại trừ.",
                        ]
                elif a.available:
                    a.why_not_selected.append(f"Ưu tiên thấp hơn phương án được chọn ({a.priority_band} so với {selected.priority_band}).")
            candidate = next(c for c in case.candidates if c.id == selected.candidate_id)
            if llm_plan and not override_active:
                rejected = [str(x) for x in (llm_plan.get("rejected_alternatives") or [])]
                if not rejected:
                    rejected = [f"{a.label}: ưu tiên thấp hơn theo đánh giá AI trong tập phương án an toàn." for a in assessments if a.available and not a.selected]
            else:
                rejected = [f"{a.label}: " + (a.why_not_selected[0] if a.why_not_selected else "ưu tiên thấp hơn") for a in assessments if a.available and not a.selected]
            rationale = list(selected.why_selected)
            if override_active:
                rationale.insert(0, "Người vận hành đã chủ động chọn bước này thay cho đề xuất mặc định của AI.")
            return AgentDecision(
                status=CaseStatus.INVESTIGATING,
                next_evidence_id=selected.candidate_id,
                next_evidence_label=selected.label,
                priority_band=selected.priority_band,
                rationale=rationale,
                rejected_alternatives=rejected,
                candidate_assessments=assessments,
                trace=self._trace(case, assessments, selected.candidate_id),
                human_override_active=override_active,
                override_reason=case.human_override_reason if override_active else None,
                planner_mode=planner_mode,
                planner_provider=planner_provider,
                planner_model=planner_model,
                planner_note=planner_note,
            )

        unresolved = [g for g in case.gates if g.status == GateStatus.UNKNOWN]
        if unresolved:
            return AgentDecision(
                status=CaseStatus.HOLD,
                blocked_reason="Còn điều kiện chưa rõ nhưng chưa có hành động khả dụng theo dependency hiện tại.",
                rationale=["AI không tự bịa dữ liệu để lấp khoảng trống."],
                human_action="Con người có thể sửa dữ liệu, bổ sung constraint hoặc yêu cầu lập kế hoạch lại.",
                candidate_assessments=assessments,
                trace=self._trace(case, assessments, None),
                planner_mode="deterministic-fallback",
                planner_note="Không có hành động khả dụng theo dependency hiện tại.",
            )

        missing_approvals = [a for a in case.approvals if a.required and not a.approved]
        if missing_approvals:
            return AgentDecision(
                status=CaseStatus.WAITING_HUMAN,
                rationale=["Các điều kiện đã có kết quả, nhưng quyết định pilot vẫn cần người có chuyên môn xác nhận."],
                human_action="Cần xác nhận: " + ", ".join(a.label for a in missing_approvals),
                candidate_assessments=assessments,
                trace=self._trace(case, assessments, None),
                planner_mode="human-gate",
                planner_note="AI đã hoàn tất phần lập kế hoạch; quyết định pilot đang chờ người có chuyên môn.",
            )

        return AgentDecision(
            status=CaseStatus.PILOT_READY,
            rationale=[
                "Các điều kiện bắt buộc đã đạt theo bằng chứng hiện có.",
                "Các phê duyệt bắt buộc của con người đã hoàn tất.",
                "‘Sẵn sàng thử nghiệm’ chỉ là trạng thái nội bộ của hồ sơ demo, không phải giấy phép hay chứng nhận pháp lý/kỹ thuật.",
            ],
            candidate_assessments=assessments,
            trace=self._trace(case, assessments, None),
            planner_mode="human-gate",
            planner_note="Trạng thái chỉ được mở sau khi các điều kiện và phê duyệt bắt buộc đều hoàn tất.",
        )

    def build_decision_pack(self, case: SynergyCase) -> DecisionPack:
        s = case.supplier_profile
        r = case.receiver_profile
        matched = None
        if s.quantity_per_day is not None and r.demand_per_day is not None:
            matched = min(s.quantity_per_day, r.demand_per_day)
        supplier_util = round(100 * matched / s.quantity_per_day, 1) if matched is not None and s.quantity_per_day else None
        receiver_cov = round(100 * matched / r.demand_per_day, 1) if matched is not None and r.demand_per_day else None
        counts = {status.value: 0 for status in FitStatus}
        for x in case.compatibility:
            counts[x.status.value] = counts.get(x.status.value, 0) + 1
        open_risks = [x.label + ": " + x.explanation for x in case.compatibility if x.status in {FitStatus.GAP, FitStatus.CONFLICT, FitStatus.UNKNOWN}]
        verified = sum(1 for g in case.gates if g.status == GateStatus.PASS)
        total = len(case.gates)
        evidence_count = sum(1 for g in case.gates if g.evidence_id or g.source) + len(case.documents)
        status = case.agent.status if case.agent else CaseStatus.INTAKE
        if status == CaseStatus.PILOT_READY:
            decision = "PILOT READY"
            headline = "Có thể chuyển sang pilot có kiểm soát"
            summary = "Hồ sơ demo đã làm rõ các điều kiện theo phạm vi mô phỏng và hoàn tất phê duyệt con người."
        elif status == CaseStatus.STOP:
            decision = "STOP"
            headline = "Dừng đường triển khai hiện tại"
            summary = case.agent.blocked_reason or "Có điều kiện bắt buộc không đạt."
        elif status == CaseStatus.HOLD:
            decision = "HOLD"
            headline = "Tạm giữ để làm rõ bằng chứng"
            summary = case.agent.blocked_reason or "Bằng chứng chưa đủ."
        elif status == CaseStatus.WAITING_HUMAN:
            decision = "WAITING HUMAN"
            headline = "Chờ phê duyệt chuyên môn"
            summary = case.agent.human_action or "Cần phê duyệt con người."
        else:
            decision = "INVESTIGATING"
            headline = "Đang thu bằng chứng quyết định"
            summary = f"Bước tiếp theo: {case.agent.next_evidence_label}" if case.agent and case.agent.next_evidence_label else "Đang phân tích."

        receiver_output = []
        if matched is not None:
            receiver_output.append(f"Bên B có thể nhận tối đa {matched:g} {r.demand_unit} trong phạm vi dữ liệu mô phỏng hiện tại.")
        receiver_output += [
            "Thông số chất lượng phải bám theo yêu cầu đầu vào của B và chỉ được xác nhận bằng kết quả xét nghiệm/nguồn có thẩm quyền.",
            "Điểm đấu nối, lưu trữ và phương án dự phòng phải được kỹ sư quy trình phê duyệt trước pilot.",
        ]
        impact = []
        if matched is not None:
            impact = [
                f"Tiềm năng thay thế tối đa {matched:g} m³/ngày nước đầu vào kỹ thuật của B trong kịch bản mô phỏng.",
                f"Tương đương {receiver_cov:g}% nhu cầu mô phỏng của B và sử dụng {supplier_util:g}% nguồn A.",
            ]
        economics = [
            "Business case hiện chỉ ở mức sơ bộ; CAPEX/OPEX phải được cập nhật bằng báo giá kỹ thuật.",
            "Không công bố số tiền tiết kiệm thực tế trước khi có pilot và dữ liệu vận hành.",
        ]
        conditions = [g.label for g in case.gates if g.status != GateStatus.PASS]
        if not conditions:
            conditions = ["Duy trì các điều kiện đã xác minh trong suốt pilot", "Theo dõi chất lượng và lưu lượng trong pilot", "Ghi lại mọi thay đổi so với hồ sơ được duyệt"]
        alternatives = []
        if status in {CaseStatus.STOP, CaseStatus.HOLD}:
            alternatives = [
                "Bổ sung bằng chứng mới nếu nguyên nhân chặn xuất phát từ dữ liệu chưa đủ hoặc đã thay đổi.",
                "Thu hẹp quy mô pilot hoặc điều chỉnh mục đích sử dụng nếu phù hợp với chuyên gia và quy định.",
                "Đánh giá một tuyến sử dụng khác thay vì cố ghi đè điều kiện bắt buộc hiện tại.",
            ]
        return DecisionPack(
            decision=decision,
            headline=headline,
            summary=summary,
            supplier_available_per_day=s.quantity_per_day,
            receiver_demand_per_day=r.demand_per_day,
            matched_volume_per_day=matched,
            supplier_utilization_pct=supplier_util,
            receiver_coverage_pct=receiver_cov,
            compatibility_summary=counts,
            verified_conditions=f"{verified}/{total}",
            evidence_count=evidence_count,
            open_risks=open_risks,
            conditions_for_pilot=conditions,
            receiver_output=receiver_output,
            potential_impact=impact,
            economics=economics,
            alternative_paths=alternatives,
            disclaimer="Dữ liệu và chỉ số trong demo là mô phỏng. NexusLoop không thay thế cơ quan quản lý, phòng thử nghiệm, luật sư hay kỹ sư chuyên môn.",
        )

    def recompute(self, case: SynergyCase, actor: str = "NexusLoop Agent") -> SynergyCase:
        previous = case.agent.model_dump() if case.agent else None
        case.agent = self.select_next(case)
        case.decision_pack = self.build_decision_pack(case)
        current = case.agent.model_dump()
        if previous != current:
            case.audit.insert(0, AuditEvent(
                ts=utc_now(),
                actor=actor,
                event="AI lập lại kế hoạch",
                detail=self.decision_summary(case.agent),
                severity="critical" if case.agent.status == CaseStatus.STOP else "info",
            ))
        return case

    def decision_summary(self, decision: AgentDecision) -> str:
        if decision.status == CaseStatus.INVESTIGATING:
            prefix = "Kế hoạch do người vận hành chọn" if decision.human_override_active else "AI chọn bước tiếp theo"
            return f"{prefix}: {decision.next_evidence_label} · mức ưu tiên {decision.priority_band}."
        if decision.status == CaseStatus.WAITING_HUMAN:
            return decision.human_action or "Chờ phê duyệt con người."
        if decision.status in {CaseStatus.HOLD, CaseStatus.STOP}:
            return decision.blocked_reason or decision.status.value
        return "Hồ sơ đạt trạng thái sẵn sàng thử nghiệm trong phạm vi demo."
