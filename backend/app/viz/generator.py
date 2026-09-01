from ..llm.base import LLMProvider
from .models import VizSpec

_VIZ_SYSTEM = (
    "You are a data visualization expert. "
    "Given a natural-language question and SQL result columns, "
    "choose the best chart type and axis mapping. "
    "Return only valid JSON — no explanation, no markdown."
)


class VizGenerator:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def generate(
        self,
        nl_query: str,
        columns: list[str],
        sample_rows: list[dict],
    ) -> tuple["VizSpec | None", "str | None"]:
        if not columns:
            return None, "No columns to visualize."

        sample_text = "\n".join(str(r) for r in sample_rows[:3])
        prompt = (
            f"User question: {nl_query}\n\n"
            f"Result columns: {columns}\n\n"
            f"Sample rows (up to 3):\n{sample_text}\n\n"
            "Choose the best chart type and axis mapping. Rules:\n"
            "- Use 'bar' for comparisons across categories.\n"
            "- Use 'line' for time-series or ordered sequences.\n"
            "- Use 'pie' when there are 2 columns (category + value) and ≤ 10 distinct rows.\n"
            "- Use 'scatter' for correlations between two numeric columns.\n"
            "- Use 'histogram' for the distribution of a single numeric column.\n"
            "- x_field and ALL y_fields MUST be exact column names from the result list above.\n"
            "- title should be a short descriptive chart title.\n"
            "Return ONLY valid JSON."
        )
        try:
            spec: VizSpec = await self._llm.generate_structured(
                prompt=prompt,
                response_schema=VizSpec,
                system_instruction=_VIZ_SYSTEM,
            )
            # Guard: ensure fields reference real columns
            valid = set(columns)
            if spec.x_field not in valid:
                spec = spec.model_copy(update={"x_field": columns[0]})
            good_y = [f for f in spec.y_fields if f in valid]
            if not good_y:
                good_y = [columns[1]] if len(columns) > 1 else [columns[0]]
            spec = spec.model_copy(update={"y_fields": good_y})
            if spec.color_field and spec.color_field not in valid:
                spec = spec.model_copy(update={"color_field": ""})
            return spec, None
        except Exception as exc:
            return None, str(exc)
