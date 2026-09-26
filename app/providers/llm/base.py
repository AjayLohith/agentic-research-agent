from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface decoupling agent reasoning from specific LLM vendors."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generate unstructured text response."""
        pass

    @abstractmethod
    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        """Generate structured response guaranteed to parse into the given Pydantic model."""
        pass
