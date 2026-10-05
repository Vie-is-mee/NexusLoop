from __future__ import annotations

import json
import os
from typing import Any

import httpx

from ..base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    id = "ollama"
    label = "Ollama / mô hình cục bộ"

    def __init__(self):
        super().__init__(model=os.getenv("OLLAMA_MODEL", ""))
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.model and self.base_url)

    @property
    def note(self) -> str:
        return "Mô hình chạy cục bộ qua Ollama; dữ liệu không cần gửi tới nhà cung cấp đám mây nếu hạ tầng local được kiểm soát."

    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        if not self.configured:
            raise RuntimeError("Thiếu OLLAMA_MODEL")
        body = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "options": {"temperature": 0},
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(f"{self.base_url}/api/chat", json=body)
            res.raise_for_status()
            data = res.json()
        return str(((data.get("message") or {}).get("content")) or "")
