import numpy as np
import pandas as pd
from typing import Any
from ..models.portfolio_models import HierarchicalPortfolioProblem
from .portfolio_solver import retrieve_stock_data


def solve_hierarchical_portfolio_problem(problem: HierarchicalPortfolioProblem) -> dict[str, Any]:
    """Solve a Hierarchical Risk Parity (HRP) portfolio optimization problem.
    
    Args:
        problem: HierarchicalPortfolioProblem instance containing tickers, constraints, and optional parameters.
        
    Returns:
        Dict with status and data (weights, expected return, risk, Sharpe ratio, and min/max portfolios).
    """
    try:
        # Retrieve market data
        data = retrieve_stock_data(tickers=problem.tickers, period="2y")
        if data.get('status') == 'error':
            return data
        prices = data['data']['prices']
        mean_returns = data['data']['mean_returns']
        cov_matrix = data['data']['cov_matrix']
        
        # Compute returns from prices
        returns = prices.pct_change().dropna()
        
        # Import HRP from archive
        from archive.pypfopt.hierarchical_portfolio import HRPOpt
        hrp = HRPOpt(returns)
        weights = hrp.optimize()
        weights = {k: float(v) for k, v in weights.items()}
        
        # Calculate portfolio metrics
        expected_return = np.sum(mean_returns * pd.Series(weights))
        risk = np.sqrt(np.dot(list(weights.values()), np.dot(cov_matrix, list(weights.values()))))
        sharpe = (expected_return - problem.risk_free_rate) / risk if risk > 0 else 0
        
        # Calculate minimum variance portfolio
        from pypfopt import EfficientFrontier
        ef_min_var = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=(problem.min_weight, problem.max_weight))
        min_var_weights = ef_min_var.min_volatility()
        min_var_weights = ef_min_var.clean_weights()
        min_var_perf = ef_min_var.portfolio_performance(verbose=False)
        
        # Calculate maximum return portfolio
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
            "message": f"Error in Hierarchical Portfolio optimization: {e!s}"
        } 