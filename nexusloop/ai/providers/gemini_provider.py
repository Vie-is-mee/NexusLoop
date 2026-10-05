from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote

import httpx

from ..base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    id = "gemini"
    label = "Google Gemini"

    def __init__(self):
        super().__init__(model=os.getenv("GEMINI_MODEL", ""))
        self.api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        self.base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        if not self.configured:
            raise RuntimeError("Thiếu GEMINI_API_KEY/GOOGLE_API_KEY hoặc GEMINI_MODEL")
        prompt = f"{instructions}\n\nINPUT JSON:\n{json.dumps(payload, ensure_ascii=False)}"
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        url = f"{self.base_url}/v1beta/models/{quote(self.model, safe='')}:generateContent?key={quote(self.api_key, safe='')}"
        with httpx.Client(timeout=30.0) as client:
            res = client.post(url, json=body)
            res.raise_for_status()
            data = res.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
        return "\n".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
