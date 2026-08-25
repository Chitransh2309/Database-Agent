from typing import Any, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from .base import LLMProvider
from ..config import settings


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction or "",
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response.text.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: str | None = None,
    ) -> Any:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction or "",
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response_schema.model_validate_json(response.text)
