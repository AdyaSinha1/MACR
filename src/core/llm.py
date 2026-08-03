import os
import asyncio
import json
from typing import Type, TypeVar, Any
from pydantic import BaseModel
from structlog import get_logger
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from groq import Groq, RateLimitError, InternalServerError

logger = get_logger()
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model_name = model_name
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")
        self.client = Groq(api_key=api_key)

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((RateLimitError, InternalServerError)),
        reraise=True,
    )
    def _generate_content_sync(self, prompt: str, schema: Type[T] | None = None) -> Any:
        """Synchronous generation using Groq SDK with retry logic."""
        try:
            if schema:
                schema_prompt = (
                    f"{prompt}\n\n"
                    f"IMPORTANT: You must return ONLY valid JSON matching this exact schema. "
                    f"No extra text, no markdown code fences, just raw JSON:\n"
                    f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
                )
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": schema_prompt}],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                return schema.model_validate_json(response.choices[0].message.content)
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error("LLM API call failed",
                         error=str(e), model=self.model_name)
            raise

    async def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """Asynchronously generate a structured Pydantic model."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._generate_content_sync, prompt, schema), timeout=60.0
        )

    async def generate_text(self, prompt: str) -> str:
        """Asynchronously generate raw text."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._generate_content_sync, prompt, None), timeout=60.0
        )
