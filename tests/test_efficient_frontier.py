#!/usr/bin/env python3
"""
Efficient Frontier Test Implementation

This test evaluates the mean-variance optimization capabilities of the Efficient Frontier solver.
"""

import logging
import sys

# import pandas as pd
import numpy as np
from mcportfolio.models.portfolio_models import EfficientFrontierProblem
from mcportfolio.solvers.efficient_frontier_solver import solve_efficient_frontier_problem
from mcportfolio.plotting.plotting_utils import plot_portfolio
from pypfopt.efficient_frontier import EfficientFrontier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def test_efficient_frontier() -> None:
    """Run the Efficient Frontier test suite."""
    
    # Define test portfolio
    tickers = [
        "AAPL", "MSFT", "NVDA",  # Tech
        "JNJ", "UNH",            # Healthcare
        "JPM", "V",              # Finance
        "MCD", "PG",             # Consumer
        "XOM", "CVX"             # Energy
    ]
    
    # Test Case 1: Basic Efficient Frontier
    logger.info("\nTest Case 1: Basic Efficient Frontier")
    problem = EfficientFrontierProblem(
        description="Generate efficient frontier with no constraints - baseline case",
        tickers=tickers,
        min_weight=0.0,
        max_weight=1.0,
        risk_free_rate=0.02
    )
    
    result = solve_efficient_frontier_problem(problem)
    
    if result["status"] == "success":
        data = result["data"]
        
        # Display optimal portfolio
        logger.info("\nOptimal Portfolio (Max Sharpe Ratio):")
        logger.info("----------------------------------------")
        for ticker, weight in data["weights"].items():
            logger.info(f"{ticker}: {weight:.2%}")
        logger.info(f"\nExpected Annual Return: {data['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {data['risk']:.2%}")
        logger.info(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
        
        # Create optimizer object for plotting
        from mcportfolio.solvers.portfolio_solver import retrieve_stock_data
        market_data = retrieve_stock_data(tickers=tickers, period="2y")
        if market_data["status"] == "success":
            mean_returns = market_data["data"]["mean_returns"]
            cov_matrix = market_data["data"]["cov_matrix"]
            
            ef = EfficientFrontier(mean_returns, cov_matrix)
            # Convert weights to the format expected by EfficientFrontier
            weights_dict = {ticker: float(weight) for ticker, weight in data["weights"].items()}
            ef.set_weights(weights_dict)
            
            # Generate plots
            try:
                # Create output directory if it doesn't exist
                import os
                os.makedirs("test_outputs", exist_ok=True)
                
                # Efficient frontier plot
                plot_portfolio(
                    opt=ef,
                    plot_type="efficient_frontier",
                    save_path="test_outputs/efficient_frontier.png",
                    show=True,
                    show_assets=True,
                    risk_free_rate=0.02,
                    show_tangency=True
                )
                
                # Weights distribution plot
                plot_portfolio(
                    opt=ef,
                    plot_type="weights",
                    save_path="test_outputs/weights.png",
                    show=True
                )
            except Exception as e:
                logger.error(f"Error generating plots: {e}")
                import traceback
                logger.error(traceback.format_exc())
    else:
        logger.error(f"Error in optimization: {result['message']}")
        
        # Try to diagnose the issue
        try:
            market_data = retrieve_stock_data(tickers=tickers, period="2y")
            if market_data["status"] == "error":
                logger.error(f"Data retrieval error: {market_data['message']}")
            else:
                mean_returns = market_data["data"]["mean_returns"]
                cov_matrix = market_data["data"]["cov_matrix"]
                
                # Check for potential issues
                logger.info("\nDiagnostic Information:")
                logger.info(f"Mean returns range: {mean_returns.min():.4f} to {mean_returns.max():.4f}")
                logger.info(f"Covariance matrix condition number: {np.linalg.cond(cov_matrix):.2e}")
                logger.info(f"Any NaN in returns: {mean_returns.isna().any()}")
                logger.info(f"Any NaN in covariance: {cov_matrix.isna().any().any()}")
        except Exception as e:
            logger.error(f"Error in diagnostics: {e}")

if __name__ == "__main__":
    test_efficient_frontier()
