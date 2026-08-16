from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EcommerceMVP API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    mock_mode: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8080"]
    )

    database_url: str = "sqlite:///./data/runtime/ecommerce_mvp.db"
    upload_dir: Path = Path("./uploads")
    generated_dir: Path = Path("./generated")
    max_upload_size_mb: int = 10

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    qwen_image_api_key: str | None = None
    qwen_image_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    qwen_image_model: str = "qwen-image-edit"

    provider_timeout_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_runtime_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
