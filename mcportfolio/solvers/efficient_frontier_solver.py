import numpy as np
# import pandas as pd
from typing import Any
from ..models.portfolio_models import EfficientFrontierProblem
from .portfolio_solver import retrieve_stock_data

def solve_efficient_frontier_problem(problem: EfficientFrontierProblem) -> dict[str, Any]:
    """Solve a mean-variance optimization problem using EfficientFrontier."""
    try:
        # Retrieve market data
        data = retrieve_stock_data(tickers=problem.tickers, period="2y")
        if data.get('status') == 'error':
            return data
        mean_returns = data['data']['mean_returns']
        cov_matrix = data['data']['cov_matrix']
        
        # Import EfficientFrontier from archive
        from pypfopt.efficient_frontier import EfficientFrontier
        ef = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        # Optimize for maximum Sharpe ratio
        weights = ef.max_sharpe(risk_free_rate=problem.risk_free_rate)
        weights = ef.clean_weights()
        expected_return, risk, sharpe = ef.portfolio_performance(verbose=False, risk_free_rate=problem.risk_free_rate)
        
        # Minimum variance portfolio
        ef_min_var = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        min_var_weights = ef_min_var.min_volatility()
        min_var_weights = ef_min_var.clean_weights()
        min_var_perf = ef_min_var.portfolio_performance(verbose=False)
        
        # Maximum return portfolio
        max_ret_idx = np.argmax(mean_returns.values)
        max_ret_weights = np.zeros(len(problem.tickers))
        max_ret_weights[max_ret_idx] = 1.0
        max_ret_weights_dict = dict(zip(problem.tickers, max_ret_weights, strict=True))
        ef_max_ret = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        ef_max_ret.set_weights(max_ret_weights_dict)
        max_ret_perf = ef_max_ret.portfolio_performance(verbose=False)
        
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
                    "risk": min_var_perf[1]
                },
                "max_return_portfolio": {
                    "weights": max_ret_weights_dict,
                    "expected_return": max_ret_perf[0],
                    "risk": max_ret_perf[1]
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in Efficient Frontier optimization: {e!s}"
        } 