from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class PortfolioProblem(BaseModel):
    """Base model for portfolio optimization problems."""

    description: str
    tickers: list[str] | None = None
    constraints: list[str] | None = None
    objective: str | None = None
    parameters: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)
