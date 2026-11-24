from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "deepseek-v4.1-flash:cloud"
    deal_radar_db: str = "data/deal_radar.db"
    skill_profile: str = "AI 应用开发、Python、大模型应用（RAG/Agent）、BIM/CAD 行业工具定制"

    @property
    def db_path(self) -> Path:
        p = Path(self.deal_radar_db)
        return p if p.is_absolute() else PROJECT_ROOT / p


settings = Settings()
