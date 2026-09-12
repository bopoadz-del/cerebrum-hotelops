"""Runtime settings. Secrets come from env; fixture mode is the CI default."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    env: str = Field(default="pilot", validation_alias=AliasChoices("HOTELOPS_ENV", "env"))
    market: str = Field(default="uae", validation_alias=AliasChoices("HOTELOPS_MARKET", "market"))
    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("HOTELOPS_HOST", "host"))
    port: int = Field(default=43180, validation_alias=AliasChoices("HOTELOPS_PORT", "port"))
    log_level: str = Field(default="info", validation_alias=AliasChoices("HOTELOPS_LOG_LEVEL", "log_level"))
    fixture_mode: bool = Field(default=True, validation_alias=AliasChoices("HOTELOPS_FIXTURE_MODE", "fixture_mode"))

    operator_token: str = Field(
        default="operator-pilot",
        validation_alias=AliasChoices("HOTELOPS_OPERATOR_TOKEN", "operator_token"),
    )
    reviewer_token: str = Field(
        default="reviewer-pilot",
        validation_alias=AliasChoices("HOTELOPS_REVIEWER_TOKEN", "reviewer_token"),
    )

    database_url: str = "sqlite+pysqlite:///./data/local/hotelops.db"
    redis_url: str = "redis://127.0.0.1:56379/0"

    llm_provider: str = Field(default="fake", validation_alias=AliasChoices("HOTELOPS_LLM_PROVIDER", "llm_provider"))
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""

    opera_base_url: str = ""
    opera_client_id: str = ""
    opera_client_secret: str = ""
    micros_base_url: str = ""
    micros_api_key: str = ""
    loyalty_lms_base_url: str = ""
    loyalty_lms_api_key: str = ""
    grms_base_url: str = ""
    grms_api_key: str = ""
    maximo_base_url: str = ""
    maximo_api_key: str = ""
    gaming_cms_base_url: str = ""
    gaming_cms_api_key: str = ""
    jetson_gateway_url: str = ""
    jetson_device_token: str = ""

    fixture_root: Path = ROOT / "fixtures"

    def live_enabled(self, *keys: str) -> bool:
        if self.fixture_mode:
            return False
        return all(bool(getattr(self, k, "")) for k in keys)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
