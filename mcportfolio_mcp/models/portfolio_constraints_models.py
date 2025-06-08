from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class SectorConstraint(BaseModel):
    """Model for sector-specific portfolio constraints."""
    sector: str
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    tickers: List[str]

class PositionConstraint(BaseModel):
    """Model for position-specific constraints."""
    ticker: str
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None

class TurnoverConstraint(BaseModel):
    """Model for portfolio turnover constraints."""
    max_turnover: float
    current_weights: dict[str, float]

class RiskConstraint(BaseModel):
    """Model for risk-based constraints."""
    max_volatility: Optional[float] = None
    max_var: Optional[float] = None
    max_cvar: Optional[float] = None
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0) 