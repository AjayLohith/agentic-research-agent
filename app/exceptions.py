class ResearchAgentError(Exception):
    """Base exception for research agent errors."""
    pass


class ConfigurationError(ResearchAgentError):
    """Raised when required environment or runtime configuration is missing or invalid."""
    pass


class ProviderError(ResearchAgentError):
    """Raised when an external LLM or search provider fails or returns unparseable data."""
    pass


class ToolError(ResearchAgentError):
    """Raised when a research tool encounters an unrecoverable execution failure."""
    pass


class AgentLimitError(ResearchAgentError):
    """Raised when an execution budget (max steps, tool calls, or runtime) is exceeded."""
    pass
