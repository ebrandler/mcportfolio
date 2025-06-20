# Modified by Edward Brandler, based on original files from PyPortfolioOpt and USolver
from typing import Any
from datetime import datetime, timedelta

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

# Alternative data sources
try:
    import pandas_datareader as pdr

    PANDAS_DATAREADER_AVAILABLE = True
except ImportError:
    PANDAS_DATAREADER_AVAILABLE = False
    pdr = None

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # Redirect logs to stderr
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


def _get_data_from_stooq(tickers: list[str], period: str = "1y") -> tuple[pd.DataFrame | None, str]:
    """Fetch data from Stooq via pandas-datareader."""
    if not PANDAS_DATAREADER_AVAILABLE:
        return None, "pandas-datareader not available"

    try:
        logger.info("Trying Stooq data source...")

        # Convert period to start/end dates
        end_date = datetime.now()
        period_days = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "ytd": 200,
            "max": 3650,
        }
        days = period_days.get(period, 365)
        start_date = end_date - timedelta(days=days)

        # Fetch data for each ticker
        data_frames = []
        for ticker in tickers:
            try:
                # Stooq uses different format - add .US suffix for US stocks
                stooq_ticker = f"{ticker}.US"
                ticker_data = pdr.get_data_stooq(stooq_ticker, start=start_date, end=end_date)
                if not ticker_data.empty:
                    # Rename columns to match yfinance format
                    ticker_data.columns = [f"{col}_{ticker}" for col in ticker_data.columns]
                    data_frames.append(ticker_data)
                else:
                    logger.warning(f"No data from Stooq for {ticker}")
            except Exception as e:
                logger.warning(f"Stooq failed for {ticker}: {e}")
                continue

        if data_frames:
            # Combine all ticker data
            combined_data = pd.concat(data_frames, axis=1)

            # Restructure to match yfinance multi-index format
            price_data = {}
            for col in ["Open", "High", "Low", "Close"]:
                price_data[col] = pd.DataFrame(
                    {
                        ticker: combined_data[f"{col}_{ticker}"]
                        for ticker in tickers
                        if f"{col}_{ticker}" in combined_data.columns
                    }
                )

            # Create MultiIndex columns like yfinance
            if price_data:
                result = pd.concat(price_data, axis=1)
                logger.info(f"Stooq data retrieved - shape: {result.shape}")
                return result, ""

        return None, "No data retrieved from Stooq"

    except Exception as e:
        logger.warning(f"Stooq data source failed: {e}")
        return None, f"Stooq error: {e}"


def _get_data_from_fred(tickers: list[str], period: str = "1y") -> tuple[pd.DataFrame | None, str]:
    """Fetch data from FRED (Federal Reserve Economic Data) - mainly for economic indicators."""
    if not PANDAS_DATAREADER_AVAILABLE:
        return None, "pandas-datareader not available"

    try:
        logger.info("Trying FRED data source...")

        # Convert period to start/end dates
        end_date = datetime.now()
        period_days = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "ytd": 200,
            "max": 3650,
        }
        days = period_days.get(period, 365)
        start_date = end_date - timedelta(days=days)

        # FRED is mainly for economic data, not individual stocks
        # This is more useful for market indices or economic indicators
        # Common FRED series: 'SP500', 'DEXUSEU', 'DGS10', etc.
        fred_tickers = []
        for ticker in tickers:
            # Map common tickers to FRED series
            fred_mapping = {
                "SPY": "SP500",  # S&P 500
                "QQQ": "NASDAQCOM",  # NASDAQ
                # Add more mappings as needed
            }
            if ticker in fred_mapping:
                fred_tickers.append(fred_mapping[ticker])

        if fred_tickers:
            data = pdr.get_data_fred(fred_tickers, start=start_date, end=end_date)
            if data is not None and not data.empty:
                logger.info(f"FRED data retrieved - shape: {data.shape}")
                return data, ""

        return None, "No FRED data available for these tickers"

    except Exception as e:
        logger.warning(f"FRED data source failed: {e}")
        return None, f"FRED error: {e}"


def retrieve_stock_data(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    """
    Retrieve historical stock data for the given tickers with robust error handling.

    Args:
        tickers: List of stock tickers
        period: Time period to retrieve (e.g., "1y" for 1 year)

    Returns:
        Dictionary containing the processed data or error message
    """
    try:
        logger.info(f"Retrieving data for tickers: {tickers}")

        # Try multiple approaches for data retrieval
        data = None
        error_messages = []

        # Approach 1: Standard yfinance download
        try:
            data = yf.download(tickers, period=period, progress=False, threads=False)
            logger.info(f"Standard download - Raw data shape: {data.shape}")
        except Exception as e:
            error_messages.append(f"Standard download failed: {e}")
            logger.warning(f"Standard download failed: {e}")

        # Approach 2: Individual ticker download if standard fails
        if data is None or data.empty:
            try:
                logger.info("Trying individual ticker downloads...")
                individual_data = {}
                for ticker in tickers:
                    ticker_obj = yf.Ticker(ticker)
                    ticker_data = ticker_obj.history(period=period)
                    if not ticker_data.empty:
                        individual_data[ticker] = ticker_data

                if individual_data:
                    # Combine individual ticker data
                    combined_data = {}
                    for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                        combined_data[col] = pd.DataFrame(
                            {ticker: individual_data[ticker][col] for ticker in individual_data.keys()}
                        )

                    # Create MultiIndex columns like yf.download
                    data = pd.concat(combined_data, axis=1)
                    logger.info(f"Individual download - Combined data shape: {data.shape}")
                else:
                    error_messages.append("Individual ticker downloads returned no data")
            except Exception as e:
                error_messages.append(f"Individual download failed: {e}")
                logger.warning(f"Individual download failed: {e}")

        # Approach 3: Try Stooq via pandas-datareader
        if data is None or data.empty:
            stooq_data, stooq_error = _get_data_from_stooq(tickers, period)
            if stooq_data is not None and not stooq_data.empty:
                data = stooq_data
                logger.info(f"Stooq data retrieved - shape: {data.shape}")
            else:
                error_messages.append(f"Stooq failed: {stooq_error}")

        # Approach 4: Try FRED for market indices
        if data is None or data.empty:
            fred_data, fred_error = _get_data_from_fred(tickers, period)
            if fred_data is not None and not fred_data.empty:
                data = fred_data
                logger.info(f"FRED data retrieved - shape: {data.shape}")
            else:
                error_messages.append(f"FRED failed: {fred_error}")

        # If all real data sources fail, return clear error
        if data is None or data.empty:
            error_summary = "; ".join(error_messages) if error_messages else "Unknown data retrieval failure"
            return {
                "status": "error",
                "message": f"Unable to retrieve real market data for tickers {tickers}. "
                f"All data sources failed: {error_summary}. "
                f"Please check ticker symbols and try again later, or verify internet connectivity.",
            }

        logger.info(f"Final data shape: {data.shape}")
        logger.info(f"Final data columns: {data.columns.tolist()}")

        # Handle empty data
        if data.empty:
            return {
                "status": "error",
                "message": f"No data retrieved for tickers: {tickers}. Errors: {'; '.join(error_messages)}",
            }

        # Handle multi-index columns
        if isinstance(data.columns, pd.MultiIndex):
            # Try to get prices in order of preference
            price_cols = ["Adj Close", "Close", "Open", "High", "Low"]
            prices = None
            for col in price_cols:
                if any((col, ticker) in data.columns for ticker in tickers):
                    prices = data[col]
                    logger.info(f"Using {col} prices")
                    break
            if prices is None:
                return {
                    "status": "error",
                    "message": f"No price data available. Available columns: {data.columns.tolist()}",
                }
        else:
            # Single ticker case
            price_cols = ["Adj Close", "Close", "Open", "High", "Low"]
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
                    "message": f"No price data available. Available columns: {data.columns.tolist()}",
                }

        logger.info(f"Prices DataFrame shape: {prices.shape}")
        logger.info(f"Prices DataFrame columns: {prices.columns.tolist()}")

        # Handle empty prices DataFrame
        if prices.empty:
            return {
                "status": "error",
                "message": f"Empty price data for tickers: {tickers}",
            }

        # Calculate returns with additional safety checks
        returns = prices.pct_change().dropna()
        logger.info(f"Returns DataFrame shape: {returns.shape}")
        logger.info(f"Returns DataFrame columns: {returns.columns.tolist()}")

        # Verify we have enough data points
        if len(returns) < 2:
            return {
                "status": "error",
                "message": f"Insufficient data points for tickers: {tickers}. "
                f"Need at least 2 days of data, got {len(returns)}.",
            }

        # Verify we have data for all tickers
        missing_tickers = [ticker for ticker in tickers if ticker not in returns.columns]
        if missing_tickers:
            return {"status": "error", "message": f"No data available for tickers: {missing_tickers}"}

        # Calculate basic statistics
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        logger.info(f"Mean returns:\n{mean_returns}")
        logger.info(f"Covariance matrix shape: {cov_matrix.shape}")

        # Verify covariance matrix is valid
        if cov_matrix.isnull().any().any():
            return {"status": "error", "message": "Invalid covariance matrix: contains NaN values"}

        if (cov_matrix == 0).all().all():
            return {"status": "error", "message": "Invalid covariance matrix: all values are zero"}

        return {
            "status": "success",
            "data": {
                "prices": prices,
                "returns": returns,
                "mean_returns": mean_returns * 252,
                "cov_matrix": cov_matrix,
                "start_date": returns.index[0].strftime("%Y-%m-%d"),
                "end_date": returns.index[-1].strftime("%Y-%m-%d"),
                "num_days": len(returns),
            },
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
        if data.get("status") == "error":
            return data
        # prices = data['data']['prices']
        mean_returns = data["data"]["mean_returns"]
        cov_matrix = data["data"]["cov_matrix"]

        # Parse constraints
        max_weight = 0.5
        sector_limits = {}
        if problem.constraints:
            for constraint in problem.constraints:
                if constraint.startswith("max_weight"):
                    max_weight = float(constraint.split()[1])
                elif constraint.startswith("sector_"):
                    sector, limit = constraint.split()
                    sector_limits[sector] = float(limit)

        weight_bounds = (0, max_weight)

        # EfficientFrontier setup
        ef = EfficientFrontier(mean_returns, cov_matrix, weight_bounds=weight_bounds)

        # Apply sector constraints if specified
        if sector_limits:
            # Define sector groups
            sectors = {
                "tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
                "fin": ["JPM", "V", "BAC", "GS", "AXP"],
                "health": ["JNJ", "UNH", "PFE", "MRK", "ABBV"],
                "cons": ["MCD", "PG", "KO", "WMT", "SBUX"],
                "energy": ["XOM", "CVX"],
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
                    "risk": min_var_perf[1],
                },
                "max_return_portfolio": {
                    "weights": max_ret_weights_clean,
                    "expected_return": max_ret_perf[0],
                    "risk": max_ret_perf[1],
                },
            },
        }
    except Exception as e:
        logger.error(f"Error in solve_problem: {e!s}", exc_info=True)
        return {"status": "error", "message": f"Error solving portfolio problem: {e!s}"}
