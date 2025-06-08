from pydantic import BaseModel


class HierarchicalPortfolioProblem(BaseModel):
    description: str
    tickers: list[str]
    min_weight: float = 0.0
    max_weight: float = 1.0
    risk_free_rate: float = 0.0


class CLAProblem(BaseModel):
    description: str
    tickers: list[str]
    min_weight: float = 0.0
    max_weight: float = 1.0
    risk_free_rate: float = 0.0


class DiscreteAllocationProblem(BaseModel):
    description: str
    tickers: list[str]
    weights: dict[str, float]
    portfolio_value: float 


class EfficientFrontierProblem(BaseModel):
    description: str
    tickers: list[str]
    min_weight: float = 0.0
    max_weight: float = 1.0
    risk_free_rate: float = 0.0 