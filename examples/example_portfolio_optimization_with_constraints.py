#!/usr/bin/env python3
"""
Portfolio Optimization Example

This example demonstrates how to use the portfolio solver to optimize a stock portfolio
with the following features:
1. Retrieves historical stock data for given tickers
2. Optimizes portfolio weights based on:
   - Maximum Sharpe ratio
   - Risk constraints
   - Weight constraints
3. Calculates and displays portfolio metrics
"""

import logging
import sys
from mcportfolio.models.portfolio_models import PortfolioProblem
from mcportfolio.solvers.portfolio_solver import solve_problem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def main() -> None:
    # Define the portfolio problem
    problem = PortfolioProblem(
        description="Optimize portfolio of diverse stocks",
        tickers=["NVDA", "JPM", "UNH", "TSLA", "AMD", "JNJ", "V", "MA"],
        constraints=["max_weight 0.5"],  # 50% maximum weight per stock
        objective="maximize_sharpe_ratio"
    )
    
    # Solve the portfolio optimization problem
    result = solve_problem(problem)
    
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
        
        # Display minimum variance portfolio
        min_var = data["min_variance_portfolio"]
        logger.info("\nMinimum Variance Portfolio:")
        logger.info("----------------------------------------")
        for ticker, weight in min_var["weights"].items():
            logger.info(f"{ticker}: {weight:.2%}")
        logger.info(f"\nExpected Annual Return: {min_var['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {min_var['risk']:.2%}")
        
        # Display maximum return portfolio
        max_ret = data["max_return_portfolio"]
        logger.info("\nMaximum Return Portfolio:")
        logger.info("----------------------------------------")
        for ticker, weight in max_ret["weights"].items():
            logger.info(f"{ticker}: {weight:.2%}")
        logger.info(f"\nExpected Annual Return: {max_ret['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {max_ret['risk']:.2%}")
    else:
        logger.error(f"Error: {result['message']}")

if __name__ == "__main__":
    main() 