# import numpy as np
# import pandas as pd
from typing import Any
from ..models.portfolio_models import DiscreteAllocationProblem
from .portfolio_solver import retrieve_stock_data

def solve_discrete_allocation_problem(problem: DiscreteAllocationProblem) -> dict[str, Any]:
    """Solve a discrete allocation problem given weights, prices, and portfolio value."""
    try:
        # Retrieve latest prices
        data = retrieve_stock_data(tickers=problem.tickers, period="5d")
        if data.get('status') == 'error':
            return data
        prices = data['data']['prices']
        latest_prices = prices.iloc[-1]
        
        # Import DiscreteAllocation from archive
        from archive.pypfopt.discrete_allocation import DiscreteAllocation  # , get_latest_prices
        weights = problem.weights
        portfolio_value = problem.portfolio_value
        
        da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=portfolio_value)
        allocation, leftover = da.lp_portfolio()
        
        return {
            "status": "success",
            "data": {
                "allocation": allocation,
                "leftover": leftover
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in Discrete Allocation: {e!s}"
        } 