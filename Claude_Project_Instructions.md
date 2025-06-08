# Claude Project Instructions

This document tells you how to use MCPortfolioOptimizer with Claude.

## Available Solvers

The project now works with this solver:

* CVXPY: For convex optimization problems in portfolio theory

## Portfolio Optimization

MCPortfolioOptimizer gives a strong interface for portfolio optimization problems using CVXPY. It can do:

1. Basic portfolio optimization
   - Minimum volatility portfolios
   - Maximum Sharpe ratio portfolios
   - Risk-constrained portfolios

2. Advanced portfolio optimization
   - Sector-constrained portfolios
   - Factor-constrained portfolios
   - Custom risk measures

## Example Usage

Here's how to use the portfolio optimization tools:

```python
# Example: Build a minimum volatility portfolio
{
    "description": "Build a minimum volatility portfolio",
    "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "constraints": ["max_weight 0.3"],  # No single stock exceeds 30%
    "objective": "minimize_volatility"
}
```

## Error Handling

When using the portfolio optimization tools, watch for these:

1. Input Validation
   - Make sure all ticker symbols are valid
   - Check that constraints are formatted right
   - Check that the objective is supported

2. Solution Validation
   - Check if the solution works
   - Make sure all constraints are met
   - Look at the portfolio metrics

3. Error Messages
   - Invalid input: "Error: Invalid input parameters"
   - No solution: "Error: No feasible solution found"
   - Runtime error: "Error: Failed to solve optimization problem"

## Best Practices

1. Start with simple problems
   - Begin with basic portfolio optimization
   - Add constraints one at a time
   - Test each constraint on its own

2. Use good constraints
   - Keep constraints realistic
   - Don't add too many constraints
   - Think about market conditions

3. Check results
   - Make sure portfolio weights add up to 1
   - Check that risk metrics make sense
   - Compare with market benchmarks

## CVXPY Optimization

The CVXPY solver works for convex optimization problems in portfolio theory. It can handle:

1. Linear constraints
   - Weight bounds
   - Sector limits
   - Factor exposures

2. Quadratic objectives
   - Minimum volatility
   - Maximum Sharpe ratio
   - Risk-adjusted returns

3. Custom constraints
   - Tracking error
   - Turnover limits
   - Transaction costs

Example CVXPY problem:

```python
{
    "variables": [
        {"name": "weights", "shape": 5}
    ],
    "objective": {
        "type": "minimize",
        "expression": "cp.quad_form(weights, cov_matrix)"
    },
    "constraints": [
        "cp.sum(weights) == 1",
        "weights >= 0",
        "weights <= 0.3"
    ]
}
```

## Response Format

The solver gives results in this format:

```python
{
    "values": {
        "weights": [0.2, 0.3, 0.1, 0.2, 0.2]
    },
    "objective_value": 0.15,
    "status": "optimal"
}
```

## Additional Resources

1. Documentation
   - [PyPortfolioOpt Documentation](https://pyportfolioopt.readthedocs.io/)
   - [CVXPY Documentation](https://www.cvxpy.org/)

2. Examples
   - Basic portfolio optimization
   - Risk-constrained portfolios
   - Factor-based optimization

3. Best Practices
   - Portfolio construction
   - Risk management
   - Performance evaluation