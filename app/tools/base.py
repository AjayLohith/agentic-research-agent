import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel, ValidationError

from app.models.tool import ToolExecutionResult


class BaseTool(ABC):
    """
    Contract for all agent tools.
    Provides deterministic parameter validation, execution timing, and structured error propagation.
    """

    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    async def run(self, **kwargs) -> ToolExecutionResult:
        """Validates input, runs tool with timing, and wraps outcome in ToolExecutionResult."""
        start_time = time.perf_counter()
        try:
            # 1. Validate inputs
            validated_inputs = self.input_schema.model_validate(kwargs)

            # 2. Execute concrete tool logic
            data = await self._execute(validated_inputs)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                success=True,
                data=data.model_dump() if isinstance(data, BaseModel) else data,
                error=None,
                execution_time_ms=round(elapsed_ms, 2)
            )

        except ValidationError as ve:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=f"Input validation error for tool '{self.name}': {str(ve)}",
                execution_time_ms=round(elapsed_ms, 2)
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=f"Execution error in tool '{self.name}': {str(e)}",
                execution_time_ms=round(elapsed_ms, 2)
            )

    @abstractmethod
    async def _execute(self, inputs: Any) -> Any:
        """Concrete tool implementation to override."""
        pass

    def get_tool_definition(self) -> Dict[str, Any]:
        """Returns JSON schema definition for LLM tool selection."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema()
        }
