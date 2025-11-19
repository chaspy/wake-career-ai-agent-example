from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_BACKEND_DIR.parent


class Settings(BaseSettings):
    """アプリ全体の環境設定を集中管理する。"""

    model_config = SettingsConfigDict(
        env_file=(BASE_BACKEND_DIR / ".env", REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mode: Literal["fake", "live"] = Field(default="live", alias="MODE")
    db_mode: Literal["sqlite", "json"] = Field(default="sqlite", alias="DB_MODE")
    database_url: str = Field(default=f"sqlite:///{BASE_BACKEND_DIR / 'app.db'}", alias="DATABASE_URL")
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    sqlite_path: Path = Field(default=BASE_BACKEND_DIR / "app.db", alias="SQLITE_PATH")
    json_db_dir: Path = Field(default=BASE_BACKEND_DIR / "data/db", alias="JSON_DB_DIR")
    articles_dir: Path = Field(default=BASE_BACKEND_DIR / "data/wake_articles", alias="ARTICLES_DIR")
    vectorstore_dir: Path = Field(default=BASE_BACKEND_DIR / "data/vectorstore", alias="VECTORSTORE_DIR")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, exclude=True)  # 廃止: 常に OpenAI 公式を使用
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settingsのシングルトンインスタンスを返す。"""

    return Settings()


def get_runtime_mode() -> Literal["fake", "live"]:
    settings = get_settings()
    if settings.mode == "live" and not settings.openai_api_key:
        return "fake"
    return settings.mode


def get_llm_provider() -> str:
    settings = get_settings()
    if settings.mode != "live" or not settings.openai_api_key:
        return "fake"
    base = (settings.openai_base_url or "").lower()
    if "groq" in base:
        return "Groq (OpenAI compatible)"
    return "OpenAI"
