# Modified by Edward Brandler, based on original files from PyPortfolioOpt and USolver
from typing import Any
# import json
import pandas as pd
import yfinance as yf
from pypfopt.efficient_frontier.efficient_frontier import EfficientFrontier
# from pypfopt.expected_returns import mean_historical_return
# from pypfopt.risk_models import CovarianceShrinkage
# import cvxpy as cp
import numpy as np
import logging
import sys

from mcportfolio.models.portfolio_base_models import PortfolioProblem

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Redirect logs to stderr
)
logger = logging.getLogger(__name__)

def extract_tickers(task: str) -> list[str]:
    """Extract stock tickers from a task description.
    
    Args:
        task: The task description containing ticker symbols
        
    Returns:
        List of extracted ticker symbols
    """
    words = task.upper().split()
    return [word.strip(",") for word in words if word.isalpha() and 2 <= len(word) <= 5]

def retrieve_stock_data(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    """
    Retrieve historical stock data for the given tickers.
    
    Args:
        tickers: List of stock tickers
        period: Time period to retrieve (e.g., "1y" for 1 year)
        
    Returns:
        Dictionary containing the processed data or error message
    """
    try:
        logger.info(f"Retrieving data for tickers: {tickers}")
        
        # Download data
        data = yf.download(tickers, period=period, progress=False)
        logger.info(f"Raw data shape: {data.shape}")
        logger.info(f"Raw data columns: {data.columns.tolist()}")
        
        # Handle multi-index columns
        if isinstance(data.columns, pd.MultiIndex):
            # Try to get prices in order of preference
            price_cols = ['Adj Close', 'Close', 'Open', 'High', 'Low']
            prices = None
            for col in price_cols:
                if (col, tickers[0]) in data.columns:
                    prices = data[col]
                    logger.info(f"Using {col} prices")
                    break
            if prices is None:
                return {
                    "status": "error",
                    "message": f"No price data available. Available columns: {data.columns.tolist()}"
                }
        else:
            # Single ticker case
            price_cols = ['Adj Close', 'Close', 'Open', 'High', 'Low']
            prices = None
            for col in price_cols:
                if col in data.columns:
                    prices = pd.DataFrame(data[col])
                    prices.columns = tickers
                    logger.info(f"Using {col} prices")
                    break
            if prices is None:
                return {
                    "status": "error",
                    "message": f"No price data available. Available columns: {data.columns.tolist()}"
                }
            
        logger.info(f"Prices DataFrame shape: {prices.shape}")
        logger.info(f"Prices DataFrame columns: {prices.columns.tolist()}")
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        logger.info(f"Returns DataFrame shape: {returns.shape}")
        logger.info(f"Returns DataFrame columns: {returns.columns.tolist()}")
        
        # Verify we have enough data points
        if len(returns) < 2:
            return {
                "status": "error",
                "message": f"Insufficient data points for tickers: {tickers}. Need at least 2 days of data."
            }
            
        # Verify we have data for all tickers
        missing_tickers = [ticker for ticker in tickers if ticker not in returns.columns]
        if missing_tickers:
            return {
                "status": "error",
                "message": f"No data available for tickers: {missing_tickers}"
            }
            
        # Calculate basic statistics
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        logger.info(f"Mean returns:\n{mean_returns}")
        logger.info(f"Covariance matrix shape: {cov_matrix.shape}")
        
        # Verify covariance matrix is valid
        if cov_matrix.isnull().any().any():
            return {
                "status": "error",
                "message": "Invalid covariance matrix: contains NaN values"
            }
            
        if (cov_matrix == 0).all().all():
            return {
                "status": "error",
                "message": "Invalid covariance matrix: all values are zero"
            }
            
        return {
            "status": "success",
            "data": {
                "prices": prices,
                "returns": returns,
                "mean_returns": mean_returns * 252,
                "cov_matrix": cov_matrix,
                "start_date": returns.index[0].strftime("%Y-%m-%d"),
                "end_date": returns.index[-1].strftime("%Y-%m-%d"),
                "num_days": len(returns)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in retrieve_stock_data: {e!s}", exc_info=True)
        return {"status": "error", "message": f"Error retrieving stock data: {e!s}"}

def solve_problem(problem: PortfolioProblem) -> dict[str, Any]:
    """Solve a portfolio optimization problem."""
    try:
        tickers = problem.tickers
        if not tickers:
            return {"status": "error", "message": "No tickers provided in problem description"}
        data = retrieve_stock_data(tickers=tickers, period="2y")
        if data.get('status') == 'error':
            return data
        # prices = data['data']['prices']
        mean_returns = data['data']['mean_returns']
        cov_matrix = data['data']['cov_matrix']
        
        # Parse constraints
        max_weight = 0.5
        sector_limits = {}
        if problem.constraints:
            for constraint in problem.constraints:
                if constraint.startswith('max_weight'):
                    max_weight = float(constraint.split()[1])
                elif constraint.startswith('sector_'):
                    sector, limit = constraint.split()
                    sector_limits[sector] = float(limit)
        
        weight_bounds = (0, max_weight)
        
        # EfficientFrontier setup
        ef = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=weight_bounds)
        
        # Apply sector constraints if specified
        if sector_limits:
            # Define sector groups
            sectors = {
                'tech': ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META'],
                'fin': ['JPM', 'V', 'BAC', 'GS', 'AXP'],
                'health': ['JNJ', 'UNH', 'PFE', 'MRK', 'ABBV'],
                'cons': ['MCD', 'PG', 'KO', 'WMT', 'SBUX'],
                'energy': ['XOM', 'CVX']
            }
            
            # Add sector constraints
            for sector, limit in sector_limits.items():
                if sector in sectors:
                    sector_tickers = sectors[sector]
                    ef.add_sector_constraints({sector: sector_tickers}, {sector: limit})
        
        # 1. Minimum variance portfolio
        # min_var_weights = ef.min_volatility()
        min_var_perf = ef.portfolio_performance(verbose=False)
        
        # 2. Maximum return portfolio
        max_ret_idx = np.argmax(mean_returns.values)
        max_ret_weights = np.zeros(len(tickers))
        max_ret_weights[max_ret_idx] = 1.0
        max_ret_weights_dict = dict(zip(tickers, max_ret_weights, strict=True))
        ef.set_weights(max_ret_weights_dict)
        max_ret_perf = ef.portfolio_performance(verbose=False)
        
        # 3. Max Sharpe ratio portfolio
        rf = 0.04  # 4% annual risk-free rate
        ef = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=weight_bounds)
        if sector_limits:
            for sector, limit in sector_limits.items():
                if sector in sectors:
                    sector_tickers = sectors[sector]
                    ef.add_sector_constraints({sector: sector_tickers}, {sector: limit})
        # sharpe_weights = ef.max_sharpe(risk_free_rate=rf)
        sharpe_perf = ef.portfolio_performance(verbose=False, risk_free_rate=rf)
        
        # Clean weights
        min_var_weights_clean = ef.clean_weights()
        max_ret_weights_clean = ef._make_output_weights(max_ret_weights)
        sharpe_weights_clean = ef.clean_weights()
        
        return {
            "status": "success",
            "data": {
                "weights": sharpe_weights_clean,
                "expected_return": sharpe_perf[0],
                "risk": sharpe_perf[1],
                "sharpe_ratio": sharpe_perf[2],
                "min_variance_portfolio": {
                    "weights": min_var_weights_clean,
                    "expected_return": min_var_perf[0],
                    "risk": min_var_perf[1]
                },
                "max_return_portfolio": {
                    "weights": max_ret_weights_clean,
                    "expected_return": max_ret_perf[0],
                    "risk": max_ret_perf[1]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in solve_problem: {e!s}", exc_info=True)
        return {"status": "error", "message": f"Error solving portfolio problem: {e!s}"} 