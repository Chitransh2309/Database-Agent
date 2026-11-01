import re
from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str: ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: str | None = None,
    ) -> Any: ...

    @staticmethod
    def strip_code_fences(text: str) -> str:
        text = re.sub(r"^```(?:sql|postgresql|postgres|json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @staticmethod
    def inline_schema_refs(schema: dict) -> dict:
        """
        Recursively replace every '$ref' pointer with the actual definition it points to.
        Produces a flat, self-contained JSON Schema that LLMs handle reliably without
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
