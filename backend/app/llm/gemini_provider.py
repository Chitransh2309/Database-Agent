import json
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
        """
        Embeds the JSON Schema in the prompt text rather than passing it as a native
        `response_schema` to GenerateContentConfig. Gemini's Developer API (free tier)
        rejects schemas containing free-form `dict[str, Any]` fields (used by Mongo
        query specs for arbitrary filters/pipelines) with "additionalProperties is only
        supported in Gemini Enterprise Agent Platform mode" — prompt-based JSON mirrors
        the approach already used for Bedrock and works around that restriction.
        """
        schema_json = json.dumps(self.inline_schema_refs(response_schema.model_json_schema()), indent=2)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with ONLY valid JSON that exactly matches this JSON Schema "
            f"(no explanation, no markdown, no code fences):\n{schema_json}"
        )
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=system_instruction or "",
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=augmented_prompt,
            config=config,
        )
        raw = self.strip_code_fences(response.text)
        return response_schema.model_validate_json(raw)
