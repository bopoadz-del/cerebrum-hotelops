"""LLM providers. Default is deterministic fake. Kimi/Azure skip if secrets missing."""

from __future__ import annotations

from typing import Any

from hotelops.settings import get_settings


class LLMSkip(RuntimeError):
    """Raised when an optional live provider is requested without secrets."""


class FakeLLM:
    provider = "fake"

    def complete(self, prompt: str, **_: Any) -> str:
        compact = " ".join(prompt.split())
        if "guest" in compact.lower():
            return "GUEST: route loyalty + booking funnel on fixture profiles; do not invent live PMS ids."
        if "license" in compact.lower():
            return "OPS: evaluate UAE/generic prerequisites; UNPROVABLE if a row is missing."
        if "fire" in compact.lower() or "pump" in compact.lower():
            return "OPS: covers/clips hide the nameplate — Class A is invalid."
        return f"FAKE_LLM: {compact[:240]}"


class LiveLLM:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def complete(self, prompt: str, **kwargs: Any) -> str:
        settings = get_settings()
        if self.provider == "kimi":
            if not settings.kimi_api_key:
                raise LLMSkip("KIMI_API_KEY is not set — live Kimi call skipped.")
            import httpx

            resp = httpx.post(
                f"{settings.kimi_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.kimi_api_key}"},
                json={
                    "model": kwargs.get("model", "moonshot-v1-8k"),
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        if self.provider == "azure":
            if not (settings.azure_openai_api_key and settings.azure_openai_endpoint and settings.azure_openai_deployment):
                raise LLMSkip("Azure OpenAI secrets are not set — live Azure call skipped.")
            import httpx

            url = (
                f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/"
                f"{settings.azure_openai_deployment}/chat/completions?api-version=2024-06-01"
            )
            resp = httpx.post(
                url,
                headers={"api-key": settings.azure_openai_api_key},
                json={"messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        raise LLMSkip(f"Unknown provider {self.provider}")


def get_llm():
    settings = get_settings()
    if settings.llm_provider in {"", "fake"}:
        return FakeLLM()
    return LiveLLM(settings.llm_provider)
