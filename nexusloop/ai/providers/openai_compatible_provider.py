from __future__ import annotations

import json
import os
from typing import Any

from ..base import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    """Adapter for services exposing an OpenAI-compatible chat endpoint.

    This is intentionally generic so DeepSeek/Qwen/Mistral/enterprise gateways can
    be connected without changing NexusLoop core code. The user supplies base URL,
    model and API key according to that provider's account/documentation.
    """

    id = "openai_compatible"
    label = "OpenAI-compatible API"

    def __init__(self):
        super().__init__(model=os.getenv("OPENAI_COMPATIBLE_MODEL", ""))
        self.api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "").strip().rstrip("/")
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)
        return self._client

    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        if not self.configured:
            raise RuntimeError("Thiếu OPENAI_COMPATIBLE_API_KEY / BASE_URL / MODEL")
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        if not response.choices:
            return ""
        return response.choices[0].message.content or ""
