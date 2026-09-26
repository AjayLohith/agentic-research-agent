import asyncio
import json
import logging
import re
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
import httpx
from openai import AsyncOpenAI, RateLimitError, APIError

from app.providers.llm.base import LLMProvider, T
from app.exceptions import ProviderError

logger = logging.getLogger("agentic_research.groq")


class GroqProvider(LLMProvider):
    """
    Groq provider using the high-speed OpenAI-compatible API endpoint.
    Supports free-tier developer models like llama-3.3-70b-versatile.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        base_url: str = "https://api.groq.com/openai/v1",
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content or ""
            except RateLimitError as rle:
                delay = self._extract_retry_after(rle, attempt)
                logger.warning(f"Groq rate limit (429) hit. Backing off for {delay:.1f}s (Attempt {attempt}/{self.max_retries})")
                await asyncio.sleep(delay)
            except Exception as e:
                if attempt == self.max_retries:
                    raise ProviderError(f"Groq generate failed after {self.max_retries} attempts: {e}") from e
                await asyncio.sleep(1.0 * attempt)

        raise ProviderError("Groq generate failed: max retries exceeded.")

    async def structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_msg = (
            (system_prompt or "")
            + "\n\nCRITICAL REQUIREMENT: Return ONLY a valid JSON object strictly conforming to this schema:\n"
            + schema_json
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

        raw_text = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content or "{}"
                parsed_json = self._extract_json(raw_text)
                return schema.model_validate(parsed_json)

            except RateLimitError as rle:
                delay = self._extract_retry_after(rle, attempt)
                logger.warning(f"Groq rate limit hit during structured output. Waiting {delay:.1f}s...")
                await asyncio.sleep(delay)

            except (json.JSONDecodeError, ValidationError) as parse_err:
                logger.warning(f"JSON validation failed on attempt {attempt}: {parse_err}. Attempting schema repair.")
                repair_prompt = (
                    f"{prompt}\n\n"
                    f"CRITICAL: Previous response failed validation: {parse_err}.\n"
                    f"Please output strictly valid JSON conforming to the schema."
                )
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": repair_prompt}
                ]

            except Exception as e:
                if attempt == self.max_retries:
                    raise ProviderError(f"Groq structured output failed after {self.max_retries} attempts: {e}") from e
                await asyncio.sleep(1.0 * attempt)

        raise ProviderError(f"Groq failed to produce valid {schema.__name__} after {self.max_retries} attempts.")

    def _extract_json(self, text: str) -> dict:
        """Extracts JSON object from response, handling markdown fences or text wrappers."""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

        data = json.loads(text)

        # Unpack any stringified JSON objects in lists (e.g. evidence, entities)
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str) and item.strip().startswith("{") and item.strip().endswith("}"):
                            try:
                                v[idx] = json.loads(item)
                            except Exception:
                                pass

        return data

    def _extract_retry_after(self, error: Exception, attempt: int) -> float:
        """Extracts Retry-After value from response headers if available, or uses exponential backoff."""
        if hasattr(error, "response") and error.response is not None:
            retry_header = error.response.headers.get("retry-after")
            if retry_header:
                try:
                    return float(retry_header)
                except ValueError:
                    pass
        return 2.0 ** attempt
