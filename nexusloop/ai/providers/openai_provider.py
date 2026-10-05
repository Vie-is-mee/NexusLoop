from __future__ import annotations

import json
import os
from typing import Any

from ..base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    id = "openai"
    label = "OpenAI"

    def __init__(self):
        super().__init__(model=os.getenv("OPENAI_MODEL", ""))
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, timeout=30.0)
        return self._client

    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        if not self.configured:
            raise RuntimeError("Thiếu OPENAI_API_KEY hoặc OPENAI_MODEL")
        client = self._get_client()
        response = client.responses.create(
            model=self.model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
        )
        return getattr(response, "output_text", "") or ""
