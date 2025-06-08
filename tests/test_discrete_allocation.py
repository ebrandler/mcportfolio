import logging
from mcportfolio_mcp.models.portfolio_models import DiscreteAllocationProblem
from mcportfolio_mcp.solvers.discrete_allocation_solver import solve_discrete_allocation_problem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discrete_allocation() -> None:
    # Example tickers and weights (from previous CLA/HRP/BL runs)
    tickers = ["META", "ABBV", "EOG", "SBUX", "BAC", "PLD"]
    weights = {
        "META": 0.35,
        "ABBV": 0.23,
        "EOG": 0.00,
        "SBUX": 0.42,
        "BAC": 0.00,
        "PLD": 0.00
    }
    portfolio_value = 100000  # $100,000
    
    problem = DiscreteAllocationProblem(
        description="Test Discrete Allocation",
        tickers=tickers,
        weights=weights,
        portfolio_value=portfolio_value
    )
    
    result = solve_discrete_allocation_problem(problem)
    
    if result["status"] == "success":
        data = result["data"]
        logger.info("Discrete Allocation Results:")
        logger.info("----------------------------------------")
        logger.info("Allocation:")
        for ticker, shares in data["allocation"].items():
            logger.info(f"  {ticker}: {shares} shares")
        logger.info(f"Leftover cash: ${data['leftover']:.2f}")
    else:
        logger.error(f"Error: {result['message']}")

if __name__ == "__main__":
    test_discrete_allocation() 