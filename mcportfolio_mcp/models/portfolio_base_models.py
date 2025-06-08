from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class PortfolioProblem(BaseModel):
    """Base model for portfolio optimization problems."""
    description: str
    tickers: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    objective: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True) 