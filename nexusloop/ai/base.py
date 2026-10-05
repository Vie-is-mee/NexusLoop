from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderStatus:
    id: str
    label: str
    configured: bool
    available: bool
    model: str
    note: str
    error: str | None = None


class BaseLLMProvider(ABC):
    """Small provider contract used by NexusLoop.

    Providers only turn a prompt + structured payload into text. Validation,
    safety gates, candidate filtering and fallback remain outside the provider.
    """

    id = "base"
    label = "Base provider"

    def __init__(self, *, model: str = ""):
        self.model = (model or "").strip()
        self.last_error: str | None = None

    @property
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @property
    def available(self) -> bool:
        return self.configured

    @property
    def note(self) -> str:
        return "LLM chỉ hỗ trợ đọc tài liệu và lập kế hoạch trong tập phương án đã qua kiểm tra an toàn."

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            id=self.id,
            label=self.label,
            configured=self.configured,
            available=self.available,
            model=self.model,
            note=self.note,
            error=self.last_error,
        )

    @abstractmethod
    def generate_text(self, *, instructions: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError
