from pydantic import BaseModel, Field

class SectorConstraint(BaseModel):
    """Model for sector-specific portfolio constraints."""
    sector: str
    min_weight: float | None = None
    max_weight: float | None = None
    tickers: list[str]

class PositionConstraint(BaseModel):
    """Model for position-specific constraints."""
    ticker: str
    min_weight: float | None = None
    max_weight: float | None = None

class TurnoverConstraint(BaseModel):
    """Model for portfolio turnover constraints."""
    max_turnover: float
    current_weights: dict[str, float]

class RiskConstraint(BaseModel):
    """Model for risk-based constraints."""
    max_volatility: float | None = None
    max_var: float | None = None
    max_cvar: float | None = None
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0) 