from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings, get_settings


class TextProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    def generate(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError


class MockTextProvider(TextProvider):
    name = "mock"
    model_name = "mock-deepseek"

    def generate(self, messages: list[dict[str, str]]) -> str:
        latest = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )
        return f"已收到问题：{latest}\n\n受控工具运行完成，以下结论仅基于结构化结果。"


class DeepSeekProvider(TextProvider):
    name = "deepseek"

    def __init__(self, settings: Settings):
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required when Mock mode is disabled")
        self.model_name = settings.deepseek_model
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.api_key = settings.deepseek_api_key
        self.timeout = settings.provider_timeout_seconds

    def generate(self, messages: list[dict[str, str]]) -> str:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model_name, "messages": messages, "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
        return str(payload["choices"][0]["message"]["content"])


def get_text_provider() -> TextProvider:
    settings = get_settings()
    return MockTextProvider() if settings.mock_mode else DeepSeekProvider(settings)
