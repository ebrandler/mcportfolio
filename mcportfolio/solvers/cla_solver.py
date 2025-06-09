import numpy as np
import pandas as pd
from typing import Any
from ..models.portfolio_models import CLAProblem
from .portfolio_solver import retrieve_stock_data


def solve_cla_problem(problem: CLAProblem) -> dict[str, Any]:
    """Solve a Critical Line Algorithm (CLA) portfolio optimization problem.

    Args:
        problem: CLAProblem instance containing tickers, constraints, and optional parameters.

    Returns:
        Dict with status and data (weights, expected return, risk, Sharpe ratio, and min/max portfolios).
    """
    try:
        # Retrieve market data
        data = retrieve_stock_data(tickers=problem.tickers, period="2y")
        if data.get("status") == "error":
            return data
        # prices = data['data']['prices']
        mean_returns = data["data"]["mean_returns"]
        cov_matrix = data["data"]["cov_matrix"]

        # Import CLA from archive
        from pypfopt.cla import CLA

        cla = CLA(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        cla.max_sharpe()
        weights = {ticker: float(cla.weights[i]) for i, ticker in enumerate(problem.tickers)}

        # Calculate portfolio metrics
        expected_return = np.sum(mean_returns * pd.Series(weights))
        risk = np.sqrt(np.dot(list(weights.values()), np.dot(cov_matrix, list(weights.values()))))
        sharpe = (expected_return - problem.risk_free_rate) / risk if risk > 0 else 0

        # Calculate minimum variance portfolio
        cla_min_var = CLA(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        cla_min_var.min_volatility()
        min_var_weights = {ticker: float(cla_min_var.weights[i]) for i, ticker in enumerate(problem.tickers)}
        min_var_perf = cla_min_var.portfolio_performance(verbose=False)

        # Calculate maximum return portfolio
        max_ret_idx = np.argmax(mean_returns.values)
        max_ret_weights = np.zeros(len(problem.tickers))
        max_ret_weights[max_ret_idx] = 1.0
        max_ret_weights_dict = dict(zip(problem.tickers, max_ret_weights, strict=True))
        max_ret_expected_return = mean_returns[max_ret_idx]
        max_ret_risk = np.sqrt(cov_matrix.iloc[max_ret_idx, max_ret_idx])
        max_ret_perf = (max_ret_expected_return, max_ret_risk)

        return {
            "status": "success",
            "data": {
                "weights": weights,
                "expected_return": expected_return,
                "risk": risk,
                "sharpe_ratio": sharpe,
                "min_variance_portfolio": {
                    "weights": min_var_weights,
                    "expected_return": min_var_perf[0],
                    "risk": min_var_perf[1],
                },
                "max_return_portfolio": {
                    "weights": max_ret_weights_dict,
                    "expected_return": max_ret_perf[0],
                    "risk": max_ret_perf[1],
                },
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"Error in CLA optimization: {e!s}"}
