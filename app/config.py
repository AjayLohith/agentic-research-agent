from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from app.exceptions import ConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Primary LLM Settings (Free Groq by default, OpenAI-compatible)
    LLM_PROVIDER: str = Field(default="groq", description="LLM provider: 'groq', 'openai', or 'mock'")
    LLM_MODEL: str = Field(default="openai/gpt-oss-120b", description="Model name")
    GROQ_MODEL: Optional[str] = Field(default=None, description="Groq model alias")
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1", description="Groq API base URL")

    # Optional OpenAI settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key (if using OpenAI)")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", description="OpenAI base URL")

    # Primary Search Settings (Tavily free tier by default)
    SEARCH_PROVIDER: str = Field(default="tavily", description="Search provider: 'tavily', 'duckduckgo', or 'mock'")
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily API key")
    tavily: Optional[str] = Field(default=None, description="Tavily key alias")

    # Execution Modes
    MOCK_MODE: bool = Field(default=False, description="Run offline with deterministic fixtures")
    DEMO_FAILURE_MODE: str = Field(default="none", description="Failure injection: 'none', 'timeout', 'http_500', 'empty_response'")

    # Research Budget and Safety Limits
    MAX_AGENT_STEPS: int = Field(default=15, description="Maximum agent execution cycles")
    MAX_TOOL_CALLS: int = Field(default=25, description="Maximum tool invocations per session")
    MAX_RETRIES_PER_TOOL: int = Field(default=2, description="Retries per tool call before fallback")
    MAX_RESEARCH_TIME_SECONDS: int = Field(default=300, description="Session timeout in seconds")
    MAX_SOURCE_COUNT: int = Field(default=15, description="Maximum distinct sources to record")
    MAX_FETCH_CONTENT_LENGTH: int = Field(default=20000, description="Max character length for web page text")

    # Outputs
    OUTPUT_DIR: str = Field(default="output", description="Directory where report artifacts are saved")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    @property
    def output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def model_post_init(self, __context: object) -> None:
        if self.GROQ_MODEL and self.GROQ_MODEL.strip():
            self.LLM_MODEL = self.GROQ_MODEL.strip()
        if not self.TAVILY_API_KEY and self.tavily and self.tavily.strip():
            self.TAVILY_API_KEY = self.tavily.strip()

    def validate_runtime(self, is_mock: bool = False) -> None:
        """Validates that necessary API keys are present for the active provider."""
        if is_mock or self.MOCK_MODE:
            return

        provider = self.LLM_PROVIDER.lower()
        if provider == "groq" and not self.GROQ_API_KEY:
            raise ConfigurationError(
                "GROQ_API_KEY is not set.\n"
                "To use the free Groq provider in live mode, add your key to .env:\n"
                "  GROQ_API_KEY=your_groq_key_here\n"
                "Or run offline without API keys using --mock."
            )
        elif provider == "openai" and not self.OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY is not set.\n"
                "Please add OPENAI_API_KEY to your .env file, or set LLM_PROVIDER=groq."
            )

        search_provider = self.SEARCH_PROVIDER.lower()
        if search_provider == "tavily" and not self.TAVILY_API_KEY:
            raise ConfigurationError(
                "TAVILY_API_KEY is not set.\n"
                "To use the Tavily search provider in live mode, add your key to .env:\n"
                "  TAVILY_API_KEY=your_tavily_key_here\n"
                "Or set SEARCH_PROVIDER=duckduckgo for keyless search, or run with --mock."
            )


settings = Settings()
