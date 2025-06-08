from typing import Optional, List
from pydantic import BaseModel, Field
from .portfolio_base_models import PortfolioProblem

class MeanVarianceProblem(PortfolioProblem):
    """Model for mean-variance portfolio optimization problems."""
    risk_free_rate: Optional[float] = Field(default=0.0, description="Risk-free rate for Sharpe ratio calculations")
    target_return: Optional[float] = Field(default=None, description="Target portfolio return")
    target_risk: Optional[float] = Field(default=None, description="Target portfolio risk (volatility)")
    min_weight: Optional[float] = Field(default=0.0, description="Minimum weight for any asset")
    max_weight: Optional[float] = Field(default=1.0, description="Maximum weight for any asset")
    sector_constraints: Optional[List[dict]] = Field(default=None, description="Sector-specific constraints") 