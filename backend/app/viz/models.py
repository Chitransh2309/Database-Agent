from typing import Literal
from pydantic import BaseModel, Field


class VizSpec(BaseModel):
    chart_type: Literal["bar", "line", "scatter", "pie", "histogram"]
    x_field: str = Field(description="Column name for the x-axis (or label field for pie).")
    y_fields: list[str] = Field(description="Column name(s) for the y-axis values.")
    title: str = Field(description="Short descriptive chart title.")
    color_field: str = Field(default="", description="Optional column for color grouping.")
