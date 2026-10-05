from __future__ import annotations

import copy
import csv
import io
import json
import re
import uuid
from pathlib import Path

from .ai_runtime import NexusAIRuntime
from .engine import NexusAgent, utc_now
from .models import (
    ApprovalSubmission,
    AuditEvent,
    ConstraintSubmission,
    CustomConstraint,
    DocumentRecord,
    EvidenceSubmission,
    Gate,
    GateStatus,
    PlanOverrideSubmission,
    ProfileUpdate,
    SynergyCase,
    EvidenceCandidate,
)


class CaseStore:
    def __init__(self, seed_path: str | Path):
        self.seed_path = Path(seed_path)
        self._seed_data = json.loads(self.seed_path.read_text(encoding="utf-8"))
        self.ai_runtime = NexusAIRuntime()
        self.agent = NexusAgent(self.ai_runtime)
        self._cases: dict[str, SynergyCase] = {}
        self.reset_all()

    def reset_all(self):
        self._cases = {}
        for item in copy.deepcopy(self._seed_data["cases"]):
            case = SynergyCase.model_validate(item)
            self.agent.recompute(case, actor="System")
            self._cases[case.id] = case

    def list(self) -> list[SynergyCase]:
        return list(self._cases.values())

    def get(self, case_id: str) -> SynergyCase:
        if case_id not in self._cases:
            raise KeyError(case_id)
        return self._cases[case_id]

    def submit_evidence(self, case_id: str, payload: EvidenceSubmission) -> SynergyCase:
        case = self.get(case_id)
        candidate = next((c for c in case.candidates if c.id == payload.evidence_id), None)
        if not candidate:
            raise ValueError("Không tìm thấy bước kiểm tra này")
        gate = next(g for g in case.gates if g.id == candidate.gate_id)
        gate.status = GateStatus(payload.outcome)
        gate.evidence_id = payload.evidence_id
        gate.source = payload.source
        gate.note = payload.note
        # Once result arrives, clear a one-time human plan override.
        case.human_override_candidate_id = None
        case.human_override_reason = None
        case.audit.insert(0, AuditEvent(
            ts=utc_now(), actor=payload.submitted_by, event="Bằng chứng mới",
            detail=f"{candidate.label} → {payload.outcome}. Nguồn: {payload.source}",
            severity="critical" if payload.outcome == "STOP" else "info",
        ))
        return self.agent.recompute(case)

    def approve(self, case_id: str, payload: ApprovalSubmission) -> SynergyCase:
        case = self.get(case_id)
        approval = next((a for a in case.approvals if a.role == payload.role), None)
        if not approval:
            raise ValueError("Không tìm thấy vai trò phê duyệt")
        approval.approved = payload.approved
        approval.approved_by = payload.approved_by if payload.approved else None
        approval.note = payload.note
        case.audit.insert(0, AuditEvent(
            ts=utc_now(), actor=payload.approved_by, event="Phê duyệt con người",
            detail=f"{approval.label} → {'Đã xác nhận' if payload.approved else 'Đã thu hồi'}."
        ))
        return self.agent.recompute(case)

    def update_profile(self, case_id: str, payload: ProfileUpdate) -> SynergyCase:
        case = self.get(case_id)
        profile = case.supplier_profile if payload.side == "supplier" else case.receiver_profile
        allowed = set(profile.__class__.model_fields.keys()) - {"facts"}
        if payload.field not in allowed:
            raise ValueError("Trường dữ liệu không được chỉnh từ giao diện demo")
        setattr(profile, payload.field, payload.value)
        case.audit.insert(0, AuditEvent(
            ts=utc_now(), actor=payload.edited_by, event="Con người chỉnh dữ liệu",
            detail=f"{payload.side}.{payload.field} được cập nhật. Lý do: {payload.reason}", severity="warning"
        ))
        return self.agent.recompute(case)

    def override_plan(self, case_id: str, payload: PlanOverrideSubmission) -> SynergyCase:
        case = self.get(case_id)
        if payload.candidate_id is None:
            case.human_override_candidate_id = None
            case.human_override_reason = None
            detail = "Người vận hành yêu cầu AI tự lập lại kế hoạch."
        else:
            candidate = next((c for c in case.candidates if c.id == payload.candidate_id), None)
            if not candidate:
                raise ValueError("Không tìm thấy phương án")
            if not self.agent.candidate_available(case, candidate):
                raise ValueError("Phương án này chưa khả dụng do điều kiện phụ thuộc chưa đạt")
            case.human_override_candidate_id = payload.candidate_id
            case.human_override_reason = payload.reason
            detail = f"Người vận hành chọn '{candidate.label}' thay đề xuất mặc định. Lý do: {payload.reason}"
        case.audit.insert(0, AuditEvent(ts=utc_now(), actor=payload.actor, event="Chỉnh kế hoạch AI", detail=detail, severity="warning"))
        return self.agent.recompute(case, actor="NexusLoop Agent · sau chỉnh sửa của người dùng")

    def add_constraint(self, case_id: str, payload: ConstraintSubmission) -> SynergyCase:
        case = self.get(case_id)
        cid = "custom-" + uuid.uuid4().hex[:8]
        constraint = CustomConstraint(id=cid, label=payload.label, description=payload.description, hard=payload.hard, status=GateStatus.UNKNOWN, added_by=payload.actor)
        case.custom_constraints.append(constraint)
        gate_id = cid
        case.gates.append(Gate(id=gate_id, label=payload.label, domain="custom", status=GateStatus.UNKNOWN, human_required=True, hard_gate=payload.hard))
        case.candidates.append(EvidenceCandidate(
            id="evidence-" + cid,
            label=f"Làm rõ: {payload.label}",
            domain="custom",
            description=payload.description,
            gate_id=gate_id,
            hard_gate=payload.hard,
            downstream_dependencies=1 if not payload.hard else 3,
            uncertainty_level="high",
            cost_index=0.25,
            time_index=0.25,
            cost_label="Chưa xác định",
            time_label="Cần chuyên gia xác nhận",
            source_hint="Người vận hành / chuyên gia",
            action_owner="Người được phân công",
            rationale=["Điều kiện này được người vận hành bổ sung và phải được làm rõ trước khi kết luận hồ sơ."],
            generated_from=["human-added-constraint"],
        ))
        case.audit.insert(0, AuditEvent(ts=utc_now(), actor=payload.actor, event="Thêm điều kiện", detail=f"{payload.label} · {'bắt buộc' if payload.hard else 'mềm'}."))
        return self.agent.recompute(case)

    def ingest_document(self, case_id: str, owner: str, filename: str, content: bytes) -> SynergyCase:
        case = self.get(case_id)
        text = ""
        extracted = []
        suffix = Path(filename).suffix.lower()
        try:
            if suffix == ".json":
                obj = json.loads(content.decode("utf-8"))
                text = json.dumps(obj, ensure_ascii=False, indent=2)
                extracted = self._apply_structured_document(case, owner, obj, filename)
            elif suffix == ".csv":
                text = content.decode("utf-8-sig", errors="ignore")
                rows = list(csv.DictReader(io.StringIO(text)))
                extracted = self._apply_csv(case, owner, rows, filename)
            elif suffix == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join((p.extract_text() or "") for p in reader.pages)
                extracted = self._apply_text(case, owner, text, filename)
            else:
                text = content.decode("utf-8", errors="ignore")
                extracted = self._apply_text(case, owner, text, filename)
        except Exception as exc:
            raise ValueError(f"Không đọc được tài liệu: {exc}") from exc
        analysis_method = "deterministic"
        ai_summary = None
        # For unstructured content, optional LLM extraction augments the transparent parser.
        # Structured JSON/CSV remains deterministic so the demo can always be reproduced.
        if suffix not in {".json", ".csv"} and text.strip() and self.ai_runtime.active:
            ai_result = self.ai_runtime.extract_document(owner=owner, filename=filename, text=text)
            if ai_result:
                ai_extracted = self._apply_ai_extraction(case, owner, ai_result)
                extracted = list(dict.fromkeys(extracted + ai_extracted))
                analysis_method = f"llm-api:{self.ai_runtime.provider}"
                ai_summary = str(ai_result.get("summary") or "").strip() or None
            elif self.ai_runtime.last_error:
                analysis_method = "deterministic-fallback"

        doc = DocumentRecord(
            id="doc-" + uuid.uuid4().hex[:8], filename=filename, owner=owner, kind=suffix.lstrip(".") or "text",
            simulated=True, uploaded_at=utc_now(),
            summary=(ai_summary or (f"Đã đọc và cập nhật {len(extracted)} trường dữ liệu." if extracted else "Đã lưu tài liệu; chưa tự động rút được trường dữ liệu phù hợp.")),
            extracted_fact_keys=extracted, text_excerpt=text[:700] if text else None,
            analysis_method=analysis_method,
            ai_summary=ai_summary,
        )
        case.documents.append(doc)
        case.audit.insert(0, AuditEvent(ts=utc_now(), actor="AI đọc hồ sơ", event="Đọc tài liệu", detail=f"{filename}: {doc.summary}"))
        return self.agent.recompute(case, actor="NexusLoop Agent · sau đọc tài liệu")

    def _profile_updates(self, profile, obj: dict, owner: str) -> list[str]:
        extracted: list[str] = []
        aliases = {
            "company": ["company", "company_name"],
            "resource_name": ["resource_name", "resource"],
            "quantity_per_day": ["quantity_per_day", "flow_m3_day", "available_m3_day"],
            "demand_per_day": ["demand_per_day", "demand_m3_day", "need_m3_day"],
            "schedule": ["schedule", "operating_schedule"],
            "stability": ["stability", "supply_stability"],
            "continuity_requirement": ["continuity_requirement", "required_continuity"],
            "intended_use": ["intended_use", "use"],
            "process_source": ["process_source", "source_process"],
            "current_route": ["current_route", "current_disposal_route"],
            "location": ["location"],
        }
        for field, keys in aliases.items():
            if not hasattr(profile, field):
                continue
            for key in keys:
                if key in obj and obj[key] is not None:
                    setattr(profile, field, obj[key])
                    extracted.append(f"{owner}.{field}")
                    break
        return extracted

    def _apply_structured_document(self, case: SynergyCase, owner: str, obj: dict, filename: str) -> list[str]:
        extracted: list[str] = []

        # Canonical single-file input: contains both A and B.
        if isinstance(obj.get("supplier_profile"), dict) or isinstance(obj.get("receiver_profile"), dict):
            if isinstance(obj.get("supplier_profile"), dict):
                sp = obj["supplier_profile"]
                extracted += self._profile_updates(case.supplier_profile, sp, "supplier")
                quality = sp.get("quality")
                if isinstance(quality, dict):
                    case.supplier_profile.quality.update(quality)
                    extracted += [f"supplier.quality.{k}" for k in quality]
            if isinstance(obj.get("receiver_profile"), dict):
                rp = obj["receiver_profile"]
                extracted += self._profile_updates(case.receiver_profile, rp, "receiver")
                reqs = rp.get("quality_requirements")
                if isinstance(reqs, dict):
                    case.receiver_profile.quality_requirements.update(reqs)
                    extracted += [f"receiver.quality_requirements.{k}" for k in reqs]
            meta = obj.get("case_metadata") or {}
            if isinstance(meta, dict):
                for field in ("title", "location", "description"):
                    if field in meta and meta[field]:
                        setattr(case, field, meta[field])
                        extracted.append(f"case.{field}")
            return extracted

        # Legacy / one-side document.
        if owner == "supplier":
            profile = case.supplier_profile
            extracted += self._profile_updates(profile, obj, "supplier")
            if isinstance(obj.get("quality"), dict):
                profile.quality.update(obj["quality"])
                extracted += [f"supplier.quality.{k}" for k in obj["quality"].keys()]
        elif owner == "receiver":
            profile = case.receiver_profile
            extracted += self._profile_updates(profile, obj, "receiver")
            if isinstance(obj.get("quality_requirements"), dict):
                profile.quality_requirements.update(obj["quality_requirements"])
                extracted += [f"receiver.quality_requirements.{k}" for k in obj["quality_requirements"].keys()]
        return extracted

    def _apply_ai_extraction(self, case: SynergyCase, owner: str, result: dict) -> list[str]:
        extracted: list[str] = []
        supplier_updates = result.get("supplier_updates") or {}
        receiver_updates = result.get("receiver_updates") or {}
        if owner in {"supplier", "shared", "expert"} and isinstance(supplier_updates, dict):
            extracted += self._profile_updates(case.supplier_profile, supplier_updates, "supplier")
        if owner in {"receiver", "shared", "expert"} and isinstance(receiver_updates, dict):
            extracted += self._profile_updates(case.receiver_profile, receiver_updates, "receiver")
        sq = result.get("supplier_quality") or {}
        if owner in {"supplier", "shared", "expert"} and isinstance(sq, dict):
            case.supplier_profile.quality.update(sq)
            extracted += [f"supplier.quality.{k}" for k in sq]
        rq = result.get("receiver_quality_requirements") or {}
        if owner in {"receiver", "shared", "expert"} and isinstance(rq, dict):
            case.receiver_profile.quality_requirements.update(rq)
            extracted += [f"receiver.quality_requirements.{k}" for k in rq]
        return extracted

    def _apply_csv(self, case: SynergyCase, owner: str, rows: list[dict], filename: str) -> list[str]:
        if not rows:
            return []
        # Demo convention: quality CSV has columns parameter,value or parameter,max,min,unit.
        extracted = []
        if owner == "supplier":
            for row in rows:
                param = (row.get("parameter") or row.get("chi_tieu") or "").strip()
                value = row.get("value") or row.get("gia_tri")
                if param and value not in (None, ""):
                    try: value = float(value)
                    except ValueError: pass
                    case.supplier_profile.quality[param] = value
                    extracted.append(f"quality.{param}")
        elif owner == "receiver":
            for row in rows:
                param = (row.get("parameter") or row.get("chi_tieu") or "").strip()
                if not param: continue
                rule = {"unit": row.get("unit") or row.get("don_vi") or ""}
                for key in ("max", "min"):
                    raw = row.get(key)
                    if raw not in (None, ""):
                        try: rule[key] = float(raw)
                        except ValueError: pass
                case.receiver_profile.quality_requirements[param] = rule
                extracted.append(f"quality_requirements.{param}")
        return extracted

    def _apply_text(self, case: SynergyCase, owner: str, text: str, filename: str) -> list[str]:
        extracted = []
        # Narrow, auditable demo extraction patterns instead of opaque free-form guessing.
        patterns = [
            (r"(?:lưu lượng|flow)\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*m3/ngày", "quantity_per_day" if owner == "supplier" else "demand_per_day"),
            (r"(?:nhu cầu|demand)\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*m3/ngày", "demand_per_day"),
        ]
        if owner not in {"supplier", "receiver"}:
            return extracted
        profile = case.supplier_profile if owner == "supplier" else case.receiver_profile
        lower = text.lower().replace("m³", "m3")
        for pattern, field in patterns:
            if hasattr(profile, field):
                m = re.search(pattern, lower)
                if m:
                    setattr(profile, field, float(m.group(1).replace(",", ".")))
                    extracted.append(field)
        return extracted

    def reset(self, case_id: str) -> SynergyCase:
        original = next((c for c in self._seed_data["cases"] if c["id"] == case_id), None)
        if original is None:
            raise KeyError(case_id)
        case = SynergyCase.model_validate(copy.deepcopy(original))
        case.audit.insert(0, AuditEvent(ts=utc_now(), actor="System", event="Đặt lại demo", detail="Hồ sơ trở về trạng thái ban đầu."))
        self.agent.recompute(case, actor="System")
        self._cases[case_id] = case
        return case
