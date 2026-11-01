"""Application configuration settings using Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for Empório AI."""

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCS_DIR: Path = BASE_DIR / "docs"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'emporio.db'}"
    POLICY_PDF_PATH: Path = DOCS_DIR / "políticas_da_loja.pdf"

    # LLM Settings: Support both NVIDIA NIM (Cloud Free) and Ollama (Local)
    LLM_PROVIDER: str = "nvidia"  # 'nvidia', 'ollama', or 'mock'
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    LLM_MODEL: str = "meta/llama-3.3-70b-instruct"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024

    # Local Ollama Defaults
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"

    # Agent Safeguards
    AGENT_MAX_ITERATIONS: int = 5
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
