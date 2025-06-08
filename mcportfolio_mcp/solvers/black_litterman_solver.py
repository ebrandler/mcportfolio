import numpy as np
import pandas as pd
from typing import Any
from ..models.portfolio_black_litterman_models import BlackLittermanProblem, BlackLittermanView
from .portfolio_solver import retrieve_stock_data

def market_implied_prior_returns(
    market_caps: dict[str, float],
    risk_aversion: float,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0
) -> pd.Series:
    """Compute the prior estimate of returns implied by the market weights.
    
    Args:
        market_caps: Market capitalizations of all assets
        risk_aversion: Risk aversion parameter
        cov_matrix: Covariance matrix of asset returns
        risk_free_rate: Risk-free rate of borrowing/lending
        
    Returns:
        Prior estimate of returns as implied by the market caps
    """
    mcaps = pd.Series(market_caps)
    mkt_weights = mcaps / mcaps.sum()
    # Pi is excess returns so must add risk_free_rate to get return
    return risk_aversion * cov_matrix.dot(mkt_weights) + risk_free_rate

def default_omega(cov_matrix: pd.DataFrame, p: np.ndarray, tau: float) -> np.ndarray:
    """Calculate the default uncertainty matrix.
    
    Args:
        cov_matrix: Covariance matrix
        p: Picking matrix
        tau: Prior uncertainty parameter
        
    Returns:
        KxK diagonal uncertainty matrix
    """
    return np.diag(np.diag(tau * p @ cov_matrix @ p.T))

def idzorek_method(
    view_confidences: np.ndarray,
    cov_matrix: pd.DataFrame,
    pi: np.ndarray,
    q: np.ndarray,
    p: np.ndarray,
    tau: float,
    risk_aversion: float
) -> np.ndarray:
    """Use Idzorek's method to create the uncertainty matrix.
    
    Args:
        view_confidences: Vector of percentage view confidences (0-1)
        cov_matrix: Covariance matrix
        pi: Prior returns
        q: Views vector
        p: Picking matrix
        tau: Prior uncertainty parameter
        risk_aversion: Risk aversion parameter
        
    Returns:
        KxK diagonal uncertainty matrix
    """
    view_omegas = []
    for view_idx in range(len(q)):
        conf = view_confidences[view_idx]
        
        if conf < 0 or conf > 1:
            raise ValueError("View confidences must be between 0 and 1")
            
        # Special handler to avoid dividing by zero
        if conf == 0:
            view_omegas.append(1e6)
            continue
            
        p_view = p[view_idx].reshape(1, -1)
        alpha = (1 - conf) / conf
        omega = tau * alpha * p_view @ cov_matrix.values @ p_view.T
        view_omegas.append(float(omega[0, 0]))
        
    return np.diag(view_omegas)

def calculate_black_litterman_returns(
    market_cap_weights: dict[str, float],
    cov_matrix: pd.DataFrame,
    views: list[BlackLittermanView],
    tau: float = 0.05,
    risk_free_rate: float = 0.0,
    risk_aversion: float = 1.0
) -> pd.Series:
    """Calculate Black-Litterman expected returns.
    
    Args:
        market_cap_weights: Market capitalization weights
        cov_matrix: Covariance matrix
        views: List of investor views
        tau: Prior uncertainty parameter
        risk_free_rate: Risk-free rate
        risk_aversion: Risk aversion parameter
        
    Returns:
        Black-Litterman posterior returns
    """
    # Calculate market implied prior returns
    pi = market_implied_prior_returns(
        market_cap_weights,
        risk_aversion,
        cov_matrix,
        risk_free_rate
    )
    pi = pi.values.reshape(-1, 1)
    
    # Create view matrices
    p = np.zeros((len(views), len(market_cap_weights)))
    q = np.zeros((len(views), 1))
    view_confidences = np.zeros(len(views))
    
    for i, view in enumerate(views):
        asset_idx = list(market_cap_weights.keys()).index(view.asset)
        p[i, asset_idx] = 1
        q[i] = view.expected_return
        view_confidences[i] = view.confidence
    
    # Calculate uncertainty matrix using Idzorek's method
    omega = idzorek_method(
        view_confidences,
        cov_matrix,
        pi,
        q,
        p,
        tau,
        risk_aversion
    )
    
    # Calculate Black-Litterman returns
    tau_sigma = tau * cov_matrix.values
    tau_sigma_p = tau_sigma @ p.T
    a = (p @ tau_sigma_p) + omega
    b = q - p @ pi
    
    try:
        solution = np.linalg.solve(a, b)
    except np.linalg.LinAlgError as e:
        if "Singular matrix" in str(e):
            solution = np.linalg.lstsq(a, b, rcond=None)[0]
        else:
            raise e
            
    post_rets = pi + tau_sigma_p @ solution
    return pd.Series(post_rets.flatten(), index=market_cap_weights.keys())

def solve_black_litterman_problem(problem: BlackLittermanProblem) -> dict[str, Any]:
    """Solve a Black-Litterman portfolio optimization problem."""
    try:
        # Get market data
        data = retrieve_stock_data(tickers=problem.tickers, period="2y")
        if data.get('status') == 'error':
            return data
            
        # Variables from original PyPortfolioOpt implementation, currently unused
        # prices = data['data']['prices']
        # mean_returns = data['data']['mean_returns']
        cov_matrix = data['data']['cov_matrix']
        
        # Use equal weights if market cap weights not provided
        if not problem.market_cap_weights:
            problem.market_cap_weights = {ticker: 1.0/len(problem.tickers) for ticker in problem.tickers}
        
        # Calculate Black-Litterman returns
        bl_returns = calculate_black_litterman_returns(
            market_cap_weights=problem.market_cap_weights,
            cov_matrix=cov_matrix,
            views=problem.views,
            tau=problem.tau,
            risk_free_rate=problem.risk_free_rate
        )
        
        # Set up optimization constraints
        weight_bounds = (problem.min_weight, problem.max_weight)
        
        # Create efficient frontier with Black-Litterman returns
        from pypfopt import EfficientFrontier
        ef = EfficientFrontier(bl_returns, cov_matrix, weight_bounds=weight_bounds)
        # Optimize for maximum Sharpe ratio
        weights = ef.max_sharpe(risk_free_rate=problem.risk_free_rate)
        weights = ef.clean_weights()
        expected_return, risk, sharpe = ef.portfolio_performance(verbose=False, risk_free_rate=problem.risk_free_rate)

        # Calculate minimum variance portfolio
        ef_min_var = EfficientFrontier(bl_returns, cov_matrix, weight_bounds=weight_bounds)
        min_var_weights = ef_min_var.min_volatility()
        min_var_weights = ef_min_var.clean_weights()
        min_var_perf = ef_min_var.portfolio_performance(verbose=False)

        # Calculate maximum return portfolio
        max_ret_idx = np.argmax(bl_returns.values)
        max_ret_weights = np.zeros(len(problem.tickers))
        max_ret_weights[max_ret_idx] = 1.0
        max_ret_weights_dict = dict(zip(problem.tickers, max_ret_weights, strict=True))
        ef_max_ret = EfficientFrontier(bl_returns, cov_matrix, weight_bounds=weight_bounds)
        ef_max_ret.set_weights(max_ret_weights_dict)
        max_ret_perf = ef_max_ret.portfolio_performance(verbose=False)

        return {
            "status": "success",
            "data": {
                "weights": weights,
                "expected_return": expected_return,
                "risk": risk,
                "sharpe_ratio": sharpe,
                "black_litterman_returns": bl_returns.to_dict(),
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
            "message": f"Error in Black-Litterman optimization: {e!s}"
        } 