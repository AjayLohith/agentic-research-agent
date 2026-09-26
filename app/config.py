from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Settings
    LLM_PROVIDER: str = Field(default="openai", description="LLM provider name: 'openai' or 'mock'")
    LLM_MODEL: str = Field(default="gpt-4o-mini", description="Model name")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", description="OpenAI base URL")

    # Search Settings
    SEARCH_PROVIDER: str = Field(default="duckduckgo", description="Search provider: 'duckduckgo', 'tavily', or 'mock'")
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily API key if using Tavily")

    # Execution Modes
    MOCK_MODE: bool = Field(default=False, description="Run deterministically offline with test fixtures")
    DEMO_FAILURE_MODE: str = Field(default="none", description="Failure injection: 'none', 'timeout', 'http_500', 'empty_response'")

    # Research Budget and Safety Limits
    MAX_AGENT_STEPS: int = Field(default=15, description="Maximum agent execution cycles")
    MAX_TOOL_CALLS: int = Field(default=25, description="Maximum tool invocations per session")
    MAX_RETRIES_PER_TOOL: int = Field(default=2, description="Retries per tool call failure before fallback")
    MAX_RESEARCH_TIME_SECONDS: int = Field(default=300, description="Session timeout in seconds")
    MAX_SOURCE_COUNT: int = Field(default=15, description="Maximum distinct sources to record")
    MAX_FETCH_CONTENT_LENGTH: int = Field(default=20000, description="Max character length for web page text")

    # Outputs
    OUTPUT_DIR: str = Field(default="output", description="Directory where report artifacts are saved")
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    @property
    def output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
