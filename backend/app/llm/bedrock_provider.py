import json
from typing import Any, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from .base import LLMProvider
from ..config import settings


class BedrockProvider(LLMProvider):
    """
    LLM provider backed by AWS Bedrock via the Bedrock Mantle OpenAI-compatible
    endpoint (https://bedrock-mantle.<region>.api.aws/v1). Mantle speaks the
    standard OpenAI Chat Completions API, so plain `openai.AsyncOpenAI` works —
    no AWS SigV4 signing or boto3 credential chain involved.
    """

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.BEDROCK_MANTLE_API_KEY,
            base_url=settings.BEDROCK_MANTLE_BASE_URL,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        messages: list[dict] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model_id,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: str | None = None,
    ) -> Any:
        schema_json = json.dumps(self.inline_schema_refs(response_schema.model_json_schema()), indent=2)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with ONLY valid JSON that exactly matches this JSON Schema "
            f"(no explanation, no markdown, no code fences):\n{schema_json}"
        )
        raw = await self.generate(augmented_prompt, system_instruction)
        raw = self.strip_code_fences(raw)
        return response_schema.model_validate_json(raw)
