from __future__ import annotations

import json
import os
from typing import Any

import httpx

from ..base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    id = "anthropic"
    label = "Anthropic Claude"

    def __init__(self):
        super().__init__(model=os.getenv("ANTHROPIC_MODEL", ""))
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        if not self.configured:
            raise RuntimeError("Thiếu ANTHROPIC_API_KEY hoặc ANTHROPIC_MODEL")
        body = {
            "model": self.model,
            "max_tokens": 1400,
            "temperature": 0,
            "system": instructions,
            "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        }
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
            res.raise_for_status()
            data = res.json()
        parts = data.get("content") or []
        return "\n".join(str(p.get("text") or "") for p in parts if isinstance(p, dict) and p.get("type") == "text")
