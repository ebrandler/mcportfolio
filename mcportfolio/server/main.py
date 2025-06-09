#!/usr/bin/env python3
import json
import logging
import sys
from typing import Any
from starlette.applications import Starlette

from fastmcp import FastMCP
from mcp.types import TextContent
from returns.result import Failure, Success

from mcportfolio.models.cvxpy_models import (
    CVXPYConstraint,
    CVXPYObjective,
    CVXPYProblem,
    CVXPYVariable,
)
from mcportfolio.models.portfolio_base_models import PortfolioProblem
from mcportfolio.models.portfolio_black_litterman_models import (
    BlackLittermanProblem,
    BlackLittermanView,
)
from mcportfolio.models.portfolio_models import (
    CLAProblem,
    DiscreteAllocationProblem,
    EfficientFrontierProblem,
    HierarchicalPortfolioProblem,
)
from mcportfolio.solvers.black_litterman_solver import solve_black_litterman_problem
from mcportfolio.solvers.cla_solver import solve_cla_problem
from mcportfolio.solvers.cvxpy_solver import solve_cvxpy_problem
from mcportfolio.solvers.discrete_allocation_solver import solve_discrete_allocation_problem
from mcportfolio.solvers.efficient_frontier_solver import solve_efficient_frontier_problem
from mcportfolio.solvers.hierarchical_portfolio_solver import solve_hierarchical_portfolio_problem
from mcportfolio.solvers.portfolio_solver import (
    retrieve_stock_data,
    solve_problem as solve_portfolio_problem,
)

# Modified by Edward Brandler, based on original files from PyPortfolioOpt and USolver

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # Redirect logs to stderr
)
logger = logging.getLogger(__name__)

# Move FastMCP app initialization to after tool function definitions


def solve_cvxpy_problem_tool(problem: CVXPYProblem) -> list[TextContent]:
    """Solve a CVXPY optimization problem.

    This tool takes a CVXPY optimization problem defined with variables, objective,
    and constraints, and returns the solution.

    Args:
        problem: A CVXPYProblem instance containing the optimization problem definition.

    Returns:
        A list of TextContent objects containing the solution or error message.
    """
    result = solve_cvxpy_problem(problem)

    match result:
        case Success(solution):
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "values": {
                                k: v.tolist() if hasattr(v, "tolist") else v for k, v in solution.values.items()
                            },
                            "objective_value": solution.objective_value,
                            "status": solution.status,
                            "dual_values": {
                                k: v.tolist() if hasattr(v, "tolist") else v
                                for k, v in (solution.dual_values or {}).items()
                            },
                        }
                    ),
                )
            ]
        case Failure(error):
            return [TextContent(type="text", text=f"Error solving problem: {error}")]
        case _:
            return [TextContent(type="text", text="Unexpected error in solve_cvxpy_problem_tool")]


def simple_cvxpy_solver(
    variables: list[dict[str, Any]],
    objective_type: str,
    objective_expr: str,
    constraints: list[str],
    parameters: dict[str, Any] | None = None,
    description: str = "",
) -> list[TextContent]:
    """A simpler interface for solving CVXPY optimization problems.

    This tool provides a more straightforward interface for CVXPY problems,
    without requiring the full CVXPYProblem model structure.

    Args:
        variables: List of variable definitions, each containing 'name' and 'shape'
        objective_type: Type of objective ('minimize' or 'maximize')
        objective_expr: Expression string for the objective function
        constraints: List of constraint expression strings
        parameters: Dictionary of parameter values (e.g., matrices A, b)
        description: Optional description of the problem

    Returns:
        A list of TextContent objects containing the solution or error message.
    """
    try:
        problem_variables = []
        for var in variables:
            if "name" not in var or "shape" not in var:
                return [
                    TextContent(
                        type="text",
                        text="Each variable must have 'name' and 'shape' fields",
                    )
                ]

            problem_variables.append(CVXPYVariable(**var))

        obj_type = objective_type.lower()
        if obj_type not in ["minimize", "maximize"]:
            return [
                TextContent(
                    type="text",
                    text=f"Invalid objective type: {obj_type}. Must be 'minimize' or 'maximize'",
                )
            ]

        objective = CVXPYObjective(type=obj_type, expression=objective_expr)
        problem_constraints = [CVXPYConstraint(expression=expr) for expr in constraints]

        problem = CVXPYProblem(
            variables=problem_variables,
            objective=objective,
            constraints=problem_constraints,
            parameters=parameters or {},
            description=description,
        )

        result = solve_cvxpy_problem(problem)

        match result:
            case Success(solution):
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "values": {
                                    k: v.tolist() if hasattr(v, "tolist") else v for k, v in solution.values.items()
                                },
                                "objective_value": solution.objective_value,
                                "status": solution.status,
                                "dual_values": {
                                    k: v.tolist() if hasattr(v, "tolist") else v
                                    for k, v in (solution.dual_values or {}).items()
                                },
                            }
                        ),
                    )
                ]
            case Failure(error):
                return [TextContent(type="text", text=f"Error solving problem: {error}")]
            case _:
                return [TextContent(type="text", text="Unexpected error in simple_cvxpy_solver")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error in simple_cvxpy_solver: {e!s}")]


def retrieve_stock_data_tool(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    """Retrieve historical stock data for the given tickers.

    This tool fetches historical price data for the specified stock tickers using Yahoo Finance.

    Example:
        To retrieve 3 years of data for technology stocks:
        {
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
            "period": "3y"
        }

    Args:
        tickers: List of stock tickers to retrieve data for
        period: Time period to retrieve (e.g., "1y" for 1 year, "3y" for 3 years)
                Supported periods: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - data: If successful, contains:
            - prices: Historical price data
            - returns: Daily returns
            - mean_returns: Annualized mean returns
            - cov_matrix: Covariance matrix
            - start_date: Start date of the data
            - end_date: End date of the data
            - num_days: Number of trading days
        - message: Error message if status is "error"
    """
    try:
        return retrieve_stock_data(tickers=tickers, period=period)
    except Exception as e:
        logger.error(f"Error in retrieve_stock_data_tool: {e!s}", exc_info=True)
        return {"status": "error", "message": str(e)}


def solve_portfolio_tool(
    description: str, tickers: list[str], constraints: list[str], objective: str
) -> dict[str, Any]:
    """Solve a portfolio optimization problem.

    This tool optimizes a portfolio of stocks based on historical data and specified constraints.

    Examples:
        1. Basic minimum volatility portfolio:
        {
            "description": "Build a minimum volatility portfolio",
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
            "constraints": ["max_weight 0.3"],  # No single stock exceeds 30%
            "objective": "minimize_volatility"
        }

        2. Maximum Sharpe ratio portfolio:
        {
            "description": "Build a maximum Sharpe ratio portfolio",
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
            "constraints": ["max_weight 0.3"],
            "objective": "maximize_sharpe_ratio"
        }

        3. Sector-constrained portfolio:
        {
            "description": "Build a diversified portfolio across major sectors",
            "tickers": ["AAPL", "MSFT", "JPM", "V", "JNJ", "UNH", "MCD", "PG", "XOM", "CVX"],
            "constraints": [
                "max_weight 0.15",     # No single stock exceeds 15%
                "sector_tech 0.35",    # Technology sector max 35%
                "sector_fin 0.35",     # Financial sector max 35%
                "sector_health 0.35",  # Healthcare sector max 35%
                "sector_cons 0.35",    # Consumer sector max 35%
                "sector_energy 0.35"   # Energy sector max 35%
            ],
            "objective": "minimize_volatility"
        }

        4. Risk-constrained portfolio:
        {
            "description": "Build a portfolio with risk constraints",
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JPM", "V", "JNJ", "UNH"],
            "constraints": [
                "max_weight 0.2",      # No single stock exceeds 20%
                "min_weight 0.05",     # Each stock must have at least 5%
                "max_volatility 0.15"  # Maximum portfolio volatility of 15%
            ],
            "objective": "maximize_sharpe_ratio"
        }

        5. Factor-constrained portfolio:
        {
            "description": "Build a portfolio with factor constraints",
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JPM", "V", "JNJ", "UNH"],
            "constraints": [
                "max_weight 0.2",           # No single stock exceeds 20%
                "min_weight 0.05",          # Each stock must have at least 5%
                "max_beta 1.2",             # Maximum portfolio beta of 1.2
                "min_momentum 0.1",         # Minimum momentum factor exposure
                "max_value 0.3"             # Maximum value factor exposure
            ],
            "objective": "maximize_sharpe_ratio"
        }

        6. Custom risk measures portfolio:
        {
            "description": "Build a portfolio with custom risk measures",
            "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JPM", "V", "JNJ", "UNH"],
            "constraints": [
                "max_weight 0.2",           # No single stock exceeds 20%
                "max_cvar 0.1",             # Maximum Conditional Value at Risk of 10%
                "max_cdar 0.15",            # Maximum Conditional Drawdown at Risk of 15%
                "max_semivariance 0.12"     # Maximum semivariance of 12%
            ],
            "objective": "minimize_volatility"
        }

    Args:
        description: Description of the portfolio optimization problem
        tickers: List of stock tickers to include in the portfolio
        constraints: List of constraints in the format "constraint_type value"
                    Supported constraints:
                    - max_weight: Maximum weight for any single stock (e.g., "max_weight 0.15")
                    - min_weight: Minimum weight for any single stock (e.g., "min_weight 0.05")
                    - sector_X: Maximum weight for sector X (e.g., "sector_tech 0.35")
                    - max_volatility: Maximum portfolio volatility (e.g., "max_volatility 0.15")
                    - max_beta: Maximum portfolio beta (e.g., "max_beta 1.2")
                    - min_momentum: Minimum momentum factor exposure (e.g., "min_momentum 0.1")
                    - max_value: Maximum value factor exposure (e.g., "max_value 0.3")
                    - max_cvar: Maximum Conditional Value at Risk (e.g., "max_cvar 0.1")
                    - max_cdar: Maximum Conditional Drawdown at Risk (e.g., "max_cdar 0.15")
                    - max_semivariance: Maximum semivariance (e.g., "max_semivariance 0.12")
        objective: Optimization objective, one of:
                  - "minimize_volatility": Minimize portfolio volatility
                  - "maximize_sharpe_ratio": Maximize Sharpe ratio
                  - "maximize_quadratic_utility": Maximize quadratic utility
                  - "efficient_risk": Efficient risk optimization
                  - "efficient_return": Efficient return optimization

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - data: If successful, contains:
            - weights: Dictionary of ticker to weight
            - expected_return: Annualized expected return
            - risk: Annualized volatility
            - sharpe_ratio: Sharpe ratio (if maximize_sharpe_ratio objective)
            - factor_exposures: Dictionary of factor exposures (if factor constraints used)
            - risk_measures: Dictionary of risk measures (if custom risk measures used)
        - message: Error message if status is "error"
    """
    try:
        problem = PortfolioProblem(
            description=description, tickers=tickers, constraints=constraints, objective=objective
        )
        result = solve_portfolio_problem(problem)
        return result
    except Exception as e:
        logger.error(f"Error in solve_portfolio_tool: {e!s}", exc_info=True)
        return {"status": "error", "message": str(e)}


def solve_black_litterman_tool(
    description: str,
    tickers: list[str],
    views: list[dict[str, Any]],
    risk_free_rate: float = 0.0,
    tau: float = 0.05,
    market_cap_weights: dict[str, float] | None = None,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> dict[str, Any]:
    """Solve a portfolio optimization problem using the Black-Litterman model.

    Args:
        description: Problem description
        tickers: List of asset tickers
        views: List of investor views, each containing:
            - asset: Asset ticker
            - expected_return: Expected return for this asset
            - confidence: Confidence level in the view (0-1)
        risk_free_rate: Risk-free rate
        tau: Prior uncertainty parameter
        market_cap_weights: Market capitalization weights
        min_weight: Minimum weight for any asset
        max_weight: Maximum weight for any asset

    Returns:
        Dictionary containing optimization results
    """
    try:
        # Convert views to BlackLittermanView objects
        bl_views = [BlackLittermanView(**view) for view in views]

        # Create problem
        problem = BlackLittermanProblem(
            description=description,
            tickers=tickers,
            views=bl_views,
            risk_free_rate=risk_free_rate,
            tau=tau,
            market_cap_weights=market_cap_weights,
            min_weight=min_weight,
            max_weight=max_weight,
        )

        # Solve problem
        result = solve_black_litterman_problem(problem)
        return result
    except Exception as e:
        return {"status": "error", "message": f"Error in Black-Litterman optimization: {e!s}"}


def solve_cla_tool(
    description: str, tickers: list[str], min_weight: float = 0.0, max_weight: float = 1.0, risk_free_rate: float = 0.0
) -> list[TextContent]:
    """Solve a Critical Line Algorithm (CLA) portfolio optimization problem.

    The Critical Line Algorithm is an efficient method for solving mean-variance optimization
    problems. It finds the entire efficient frontier by identifying critical points where
    constraints become active or inactive.

    Args:
        description: Description of the optimization problem
        tickers: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        min_weight: Minimum weight for any asset (default: 0.0)
        max_weight: Maximum weight for any asset (default: 1.0)
        risk_free_rate: Risk-free rate for Sharpe ratio calculation (default: 0.0)

    Returns:
        JSON result containing optimized portfolio weights, performance metrics,
        and comparison portfolios (minimum variance and maximum return).

    Example:
        {
            "description": "Optimize tech portfolio using CLA",
            "tickers": ["AAPL", "MSFT", "GOOGL", "NVDA"],
            "min_weight": 0.05,
            "max_weight": 0.4,
            "risk_free_rate": 0.02
        }
    """
    try:
        problem = CLAProblem(
            description=description,
            tickers=tickers,
            min_weight=min_weight,
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )

        result = solve_cla_problem(problem)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in CLA optimization: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Error in CLA optimization: {e!s}"}, indent=2),
            )
        ]


def solve_efficient_frontier_tool(
    description: str, tickers: list[str], min_weight: float = 0.0, max_weight: float = 1.0, risk_free_rate: float = 0.0
) -> list[TextContent]:
    """Solve a mean-variance optimization problem using the Efficient Frontier method.

    This tool implements the classic Markowitz mean-variance optimization to find
    the portfolio that maximizes the Sharpe ratio (risk-adjusted return).

    Args:
        description: Description of the optimization problem
        tickers: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        min_weight: Minimum weight for any asset (default: 0.0)
        max_weight: Maximum weight for any asset (default: 1.0)
        risk_free_rate: Risk-free rate for Sharpe ratio calculation (default: 0.0)

    Returns:
        JSON result containing optimized portfolio weights, performance metrics,
        and comparison portfolios (minimum variance and maximum return).

    Example:
        {
            "description": "Maximize Sharpe ratio for diversified portfolio",
            "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"],
            "min_weight": 0.0,
            "max_weight": 0.3,
            "risk_free_rate": 0.025
        }
    """
    try:
        problem = EfficientFrontierProblem(
            description=description,
            tickers=tickers,
            min_weight=min_weight,
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )

        result = solve_efficient_frontier_problem(problem)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in Efficient Frontier optimization: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"status": "error", "message": f"Error in Efficient Frontier optimization: {e!s}"}, indent=2
                ),
            )
        ]


def solve_hierarchical_portfolio_tool(
    description: str, tickers: list[str], min_weight: float = 0.0, max_weight: float = 1.0, risk_free_rate: float = 0.0
) -> list[TextContent]:
    """Solve a Hierarchical Risk Parity (HRP) portfolio optimization problem.

    HRP is a modern portfolio optimization technique that uses machine learning
    concepts to build diversified portfolios. It addresses some limitations of
    traditional mean-variance optimization by using hierarchical clustering.

    Args:
        description: Description of the optimization problem
        tickers: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        min_weight: Minimum weight for any asset (default: 0.0)
        max_weight: Maximum weight for any asset (default: 1.0)
        risk_free_rate: Risk-free rate for Sharpe ratio calculation (default: 0.0)

    Returns:
        JSON result containing optimized portfolio weights, performance metrics,
        and comparison portfolios (minimum variance and maximum return).

    Example:
        {
            "description": "Build HRP portfolio for risk parity",
            "tickers": ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ", "PG", "XOM"],
            "min_weight": 0.02,
            "max_weight": 0.25,
            "risk_free_rate": 0.02
        }
    """
    try:
        problem = HierarchicalPortfolioProblem(
            description=description,
            tickers=tickers,
            min_weight=min_weight,
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )

        result = solve_hierarchical_portfolio_problem(problem)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in Hierarchical Portfolio optimization: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"status": "error", "message": f"Error in Hierarchical Portfolio optimization: {e!s}"}, indent=2
                ),
            )
        ]


def solve_discrete_allocation_tool(
    description: str, tickers: list[str], weights: dict[str, float], portfolio_value: float
) -> list[TextContent]:
    """Convert portfolio weights to discrete share allocations for a given portfolio value.

    This tool takes theoretical portfolio weights (which sum to 1.0) and converts them
    to actual share quantities that can be purchased, accounting for indivisible shares
    and the specific portfolio value.

    Args:
        description: Description of the allocation problem
        tickers: List of stock ticker symbols that match the weights keys
        weights: Dictionary mapping ticker symbols to their target weights (should sum to ~1.0)
        portfolio_value: Total portfolio value in dollars to allocate

    Returns:
        JSON result containing the number of shares to buy for each stock
        and any leftover cash that couldn't be allocated.

    Example:
        {
            "description": "Allocate $10,000 based on optimized weights",
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "weights": {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25},
            "portfolio_value": 10000
        }
    """
    try:
        problem = DiscreteAllocationProblem(
            description=description, tickers=tickers, weights=weights, portfolio_value=portfolio_value
        )

        result = solve_discrete_allocation_problem(problem)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in Discrete Allocation: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Error in Discrete Allocation: {e!s}"}, indent=2),
            )
        ]


# At the module level, after all function definitions, update the app initialization:
app = FastMCP(name="mcportfolio")
app.tool("solve_cvxpy_problem")(solve_cvxpy_problem_tool)
app.tool("simple_cvxpy_solver")(simple_cvxpy_solver)
app.tool("retrieve_stock_data")(retrieve_stock_data_tool)
app.tool("solve_portfolio")(solve_portfolio_tool)
app.tool("solve_black_litterman")(solve_black_litterman_tool)
app.tool("solve_cla")(solve_cla_tool)
app.tool("solve_efficient_frontier")(solve_efficient_frontier_tool)
app.tool("solve_hierarchical_portfolio")(solve_hierarchical_portfolio_tool)
app.tool("solve_discrete_allocation")(solve_discrete_allocation_tool)

# Health route for HTTP mode only - not needed for stdio transport
# @app.custom_route("/health", methods=["GET"])
# def health_route() -> JSONResponse:
#     return JSONResponse({"status": "ok"})


# ASGI app for HTTP/JSON-RPC transport (uvicorn)
# Only create when explicitly imported for uvicorn
def create_asgi_app() -> Starlette:
    """Create ASGI app for uvicorn deployment"""
    http_app = app.http_app()

    # Add health endpoint
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy", "service": "mcportfolio"})

    # Add the health route
    http_app.routes.append(Route("/health", health_check))

    return http_app


# For uvicorn, use: uvicorn mcportfolio.server.main:create_asgi_app --factory --host 0.0.0.0 --port 8001


def main() -> None:
    """Main entry point for the MCP server"""
    app.run(transport="stdio")


if __name__ == "__main__":
    # For Claude Desktop and MCP clients, use stdio transport by default
    # For HTTP server, use: uvicorn mcportfolio.server.main:create_asgi_app --factory --host 0.0.0.0 --port 8001
    main()
