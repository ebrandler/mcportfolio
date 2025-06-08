# Code Attributions and Implementation Details

This project, MCPortfolioOptimizer, builds on and extends these open-source projects:

## PyPortfolioOpt

The core portfolio optimization features come from PyPortfolioOpt, which provides:
- Mean-variance optimization
- Risk models and risk metrics
- Efficient frontier computation
- Black-Litterman model implementation
- Hierarchical risk parity

Key components used:
- Risk models and metrics from `pypfopt.risk_models`
- Optimization objectives from `pypfopt.objective_functions`
- Efficient frontier computation from `pypfopt.efficient_frontier`
- Black-Litterman implementation from `pypfopt.black_litterman`

## USolver

The project's structure and solver interface design comes from USolver, including:
- The Model-Constraint-Problem (MCP) pattern
- The universal solver interface design
- The approach to constraint modeling

## Implementation Notes

1. Portfolio Optimization:
   - Added more risk metrics to PyPortfolioOpt's features
   - Added support for custom constraints and objectives
   - Created a more flexible interface for portfolio optimization

2. Solver Interface:
   - Adapted USolver's MCP pattern for portfolio problems
   - Made the interface simpler while keeping it extensible
   - Added support for multiple optimization backends

3. Integration:
   - Combined PyPortfolioOpt's optimization with a flexible interface
   - Added support for LLM-driven portfolio optimization
   - Created a REST API for remote optimization 