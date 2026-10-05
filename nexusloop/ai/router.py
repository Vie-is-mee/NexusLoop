from __future__ import annotations

import os
from dataclasses import asdict
from typing import Iterable

from .base import BaseLLMProvider, ProviderStatus
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
)


PROVIDER_FACTORIES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "ollama": OllamaProvider,
}

DEFAULT_PRIORITY = ["openai", "anthropic", "gemini", "openai_compatible", "ollama"]


class LLMRouter:
    """Select one configured LLM provider without leaking provider logic into core.

    NEXUSLOOP_AI_PROVIDER may be a concrete provider id or `auto`.
    `auto` selects the first configured provider from NEXUSLOOP_PROVIDER_PRIORITY.
    """

    def __init__(self):
        self.requested_provider = (os.getenv("NEXUSLOOP_AI_PROVIDER", "auto") or "auto").strip().lower()
        self.mode = (os.getenv("NEXUSLOOP_AI_MODE", "auto") or "auto").strip().lower()
        priority_env = os.getenv("NEXUSLOOP_PROVIDER_PRIORITY", "")
        self.priority = [x.strip().lower() for x in priority_env.split(",") if x.strip()] or list(DEFAULT_PRIORITY)
        self.providers: dict[str, BaseLLMProvider] = {pid: factory() for pid, factory in PROVIDER_FACTORIES.items()}
        self.failover_enabled = (os.getenv("NEXUSLOOP_LLM_FAILOVER", "true") or "true").strip().lower() not in {"0", "false", "no", "off"}
        self.last_failures: list[str] = []
        self.current: BaseLLMProvider | None = self._select()

    def _select(self) -> BaseLLMProvider | None:
        if self.mode == "fallback":
            return None
        if self.requested_provider == "auto":
            for pid in self.priority:
                provider = self.providers.get(pid)
                if provider and provider.configured:
                    return provider
            return None
        provider = self.providers.get(self.requested_provider)
        if provider and provider.configured:
            return provider
        return None

    @property
    def active(self) -> bool:
        return bool(self.current is not None and self.mode != "fallback")

    @property
    def provider_id(self) -> str:
        return self.current.id if self.current else (self.requested_provider if self.requested_provider != "auto" else "fallback")

    @property
    def provider_label(self) -> str:
        return self.current.label if self.current else "Cơ chế dự phòng"

    @property
    def model(self) -> str:
        return self.current.model if self.current else ""

    def provider_statuses(self) -> list[dict]:
        return [asdict(p.status()) for p in self.providers.values()]

    def generate_text(self, *, instructions: str, payload: dict) -> str:
        if not self.current:
            raise RuntimeError("Không có LLM provider đang hoạt động")

        ordered: list[BaseLLMProvider] = [self.current]
        if self.failover_enabled:
            for pid in self.priority:
                provider = self.providers.get(pid)
                if provider and provider.configured and provider is not self.current:
                    ordered.append(provider)

        self.last_failures = []
        last_exc: Exception | None = None
        for provider in ordered:
            try:
                text = provider.generate_text(instructions=instructions, payload=payload)
                self.current = provider
                return text
            except Exception as exc:
                provider.last_error = f"{type(exc).__name__}: {exc}"
                self.last_failures.append(f"{provider.label}: {provider.last_error}")
                last_exc = exc
                if not self.failover_enabled:
                    break
        if last_exc:
            raise RuntimeError("; ".join(self.last_failures)) from last_exc
        raise RuntimeError("Không có LLM provider khả dụng")
