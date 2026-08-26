import asyncio
import json
from typing import Any, Type

import boto3
from pydantic import BaseModel

from .base import LLMProvider
from ..config import settings


def _inline_refs(schema: dict) -> dict:
    """
    Recursively replace every '$ref' pointer with the actual definition it points to.
    This produces a flat, self-contained schema that LLMs handle reliably without
    needing to understand JSON Schema $ref mechanics.
    """
    defs = schema.get("$defs", {})

    def resolve(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_key = obj["$ref"].split("/")[-1]
                return resolve(defs.get(ref_key, {}))
            return {k: resolve(v) for k, v in obj.items() if k != "$defs"}
        if isinstance(obj, list):
            return [resolve(item) for item in obj]
        return obj

    return resolve(schema)


class BedrockProvider(LLMProvider):
    """
    LLM provider backed by AWS Bedrock Runtime (converse API).
    Credentials are resolved via the standard boto3 chain:
      - env vars (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
      - ~/.aws/credentials
      - EC2 instance IAM role
    Nothing is hardcoded here.
    """

    def __init__(self) -> None:
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    # ── Internal sync call (boto3 is synchronous) ─────────────────────────

    def _converse_sync(
        self,
        messages: list[dict],
        system: str | None,
        additional_fields: dict,
    ) -> str:
        kwargs: dict = {
            "modelId": self.model_id,
            "messages": messages,
        }
        if system:
            kwargs["system"] = [{"text": system}]
        if additional_fields:
            kwargs["additionalModelRequestFields"] = additional_fields
        response = self._client.converse(**kwargs)
        # The model may prepend a reasoningContent block before the text block.
        # Find the first content item that actually carries a "text" key.
        content_blocks = response["output"]["message"]["content"]
        for block in content_blocks:
            if "text" in block:
                return block["text"]
        raise RuntimeError(f"No text block in Bedrock response: {content_blocks}")

    # ── Public async interface ─────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        loop = asyncio.get_running_loop()
        result: str = await loop.run_in_executor(
            None,
            lambda: self._converse_sync(messages, system_instruction, {}),
        )
        return result.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: str | None = None,
    ) -> Any:
        schema_json = json.dumps(_inline_refs(response_schema.model_json_schema()), indent=2)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with ONLY valid JSON that exactly matches this JSON Schema "
            f"(no explanation, no markdown, no code fences):\n{schema_json}"
        )
        messages = [{"role": "user", "content": [{"text": augmented_prompt}]}]
        loop = asyncio.get_running_loop()
        raw: str = await loop.run_in_executor(
            None,
            lambda: self._converse_sync(messages, system_instruction, {}),
        )
        raw = self.strip_code_fences(raw)
        return response_schema.model_validate_json(raw)
