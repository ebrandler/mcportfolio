from pydantic import Field
from .portfolio_base_models import PortfolioProblem


class MeanVarianceProblem(PortfolioProblem):
    """Model for mean-variance portfolio optimization problems."""

    risk_free_rate: float | None = Field(default=0.0, description="Risk-free rate for Sharpe ratio calculations")
    target_return: float | None = Field(default=None, description="Target portfolio return")
    target_risk: float | None = Field(default=None, description="Target portfolio risk (volatility)")
    min_weight: float | None = Field(default=0.0, description="Minimum weight for any asset")
    max_weight: float | None = Field(default=1.0, description="Maximum weight for any asset")
    sector_constraints: list[dict] | None = Field(default=None, description="Sector-specific constraints")
