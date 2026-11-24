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
    skill_profile: str = (
        "全栈开发：前端（React/Vue/TypeScript）、后端（Java/Python/Go/Rust）、"
        "数据库与部署；AI 应用：LLM/RAG/Agent/MCP；BIM/CAD；自动化脚本；可远程独立交付"
    )

    @property
    def db_path(self) -> Path:
        p = Path(self.deal_radar_db)
        return p if p.is_absolute() else PROJECT_ROOT / p


settings = Settings()
