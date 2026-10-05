from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

from .ai import LLMRouter

load_dotenv()


def _json_from_text(text: str) -> dict[str, Any]:
    """Parse a JSON object from provider text without trusting markdown fences."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(raw[start:end + 1])
                return obj if isinstance(obj, dict) else {}
            except Exception:
                return {}
    return {}


@dataclass
class AIStatus:
    configured: bool
    active: bool
    provider: str
    provider_label: str
    requested_provider: str
    model: str
    mode: str
    label: str
    note: str
    last_error: str | None = None
    supported_providers: list[str] | None = None
    providers: list[dict[str, Any]] | None = None


class NexusAIRuntime:
    """Model-agnostic LLM layer with deterministic fallback.

    LLM providers are optional and replaceable. Safety-critical gates, dependency
    checks, state transitions, audit logs and the fallback planner remain in
    deterministic NexusLoop core code.
    """

    def __init__(self):
        self.mode = os.getenv("NEXUSLOOP_AI_MODE", "auto").strip().lower() or "auto"
        self.router = LLMRouter()
        self.last_error: str | None = None
        self._plan_cache: dict[str, dict[str, Any]] = {}

    # Backward-compatible hooks used by a few existing tests/tools.
    @property
    def provider(self) -> str:
        return self.router.provider_id

    @property
    def model(self) -> str:
        return self.router.model

    @property
    def active(self) -> bool:
        return self.router.active and self.mode != "fallback"

    def status(self) -> AIStatus:
        if self.active:
            label = f"AI qua {self.router.provider_label}"
            note = (
                "LLM đang hỗ trợ đọc tài liệu và chọn/giải thích bước kiểm tra trong tập phương án đã được "
                "NexusLoop Core kiểm tra. Điều kiện bắt buộc, quyền con người và fallback không phụ thuộc model."
            )
        else:
            label = "Chế độ dự phòng minh bạch"
            note = (
                "Chưa có LLM provider hợp lệ, đang ép fallback, hoặc provider tạm lỗi; hệ thống vẫn chạy bằng "
                "bộ trích xuất và xếp hạng xác định để demo không bị gián đoạn."
            )
        statuses = self.router.provider_statuses()
        configured = any(bool(x.get("configured")) for x in statuses)
        return AIStatus(
            configured=configured,
            active=self.active,
            provider=self.router.provider_id,
            provider_label=self.router.provider_label,
            requested_provider=self.router.requested_provider,
            model=self.model,
            mode=self.mode,
            label=label,
            note=note,
            last_error=self.last_error,
            supported_providers=list(self.router.providers.keys()),
            providers=statuses,
        )

    def _call_json(self, *, instructions: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.active:
            return None
        try:
            text = self.router.generate_text(instructions=instructions, payload=payload)
            result = _json_from_text(text)
            if not result:
                raise ValueError("Mô hình không trả về JSON hợp lệ")
            self.last_error = None
            return result
        except Exception as exc:
            self.last_error = (
                f"{self.router.provider_label} tạm không dùng được; đã chuyển sang dự phòng: "
                f"{type(exc).__name__}: {exc}"
            )
            return None

    def extract_document(self, *, owner: str, filename: str, text: str) -> dict[str, Any] | None:
        if not text.strip() or not self.active:
            return None
        instructions = """
Bạn là lớp đọc hồ sơ của NexusLoop. Chỉ trích xuất dữ kiện được nêu rõ trong tài liệu; không suy đoán số liệu còn thiếu.
Trả về DUY NHẤT một JSON object hợp lệ, không markdown, theo schema:
{
  "summary": "tóm tắt ngắn bằng tiếng Việt",
  "supplier_updates": {"resource_name"?: str, "process_source"?: str, "quantity_per_day"?: number, "schedule"?: str, "stability"?: str, "current_route"?: str, "location"?: str},
  "receiver_updates": {"intended_use"?: str, "demand_per_day"?: number, "schedule"?: str, "continuity_requirement"?: str, "location"?: str},
  "supplier_quality": {"<parameter>": number|string|null},
  "receiver_quality_requirements": {"<parameter>": {"min"?: number, "max"?: number, "unit"?: str}},
  "warnings": ["bất kỳ mâu thuẫn/thiếu chắc chắn nào"]
}
Nếu tài liệu chỉ thuộc A thì để receiver_updates rỗng; nếu chỉ thuộc B thì để supplier_updates rỗng. Không kết luận pháp lý/an toàn.
""".strip()
        return self._call_json(
            instructions=instructions,
            payload={"owner": owner, "filename": filename, "document_text": text[:18000]},
        )

    def choose_candidate(self, *, case_payload: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Ask the selected LLM to choose only among candidates already allowed by deterministic gates."""
        if not self.active or not candidates:
            return None
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "provider": self.provider,
                    "model": self.model,
                    "case": case_payload,
                    "candidates": candidates,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        if fingerprint in self._plan_cache:
            return self._plan_cache[fingerprint]

        instructions = """
Bạn là bộ lập kế hoạch bằng chứng của NexusLoop. Hệ thống quy tắc đã loại mọi phương án không an toàn/không khả dụng.
Bạn CHỈ được chọn đúng một candidate_id có trong danh sách candidates. Không được tạo candidate mới, không được đổi trạng thái pháp lý/kỹ thuật, không được bịa dữ liệu.
Mục tiêu: chọn bằng chứng nên lấy tiếp theo để giảm bất định quyết định với chi phí/thời gian hợp lý, ưu tiên khả năng loại trừ dự án sớm và số bước phụ thuộc phía sau.
Trả về DUY NHẤT JSON object hợp lệ:
{
  "candidate_id": "id",
  "why_selected": ["2-4 lý do ngắn, cụ thể"],
  "rejected_alternatives": ["Tên phương án: lý do chưa chọn"],
  "decision_note": "một câu mô tả cách AI ra quyết định"
}
""".strip()
        result = self._call_json(instructions=instructions, payload={"case": case_payload, "candidates": candidates})
        if result:
            allowed = {c["candidate_id"] for c in candidates}
            if result.get("candidate_id") not in allowed:
                self.last_error = "LLM trả về phương án ngoài tập cho phép; đã dùng bộ dự phòng."
                return None
            self._plan_cache[fingerprint] = result
        return result
