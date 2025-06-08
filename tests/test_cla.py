import logging
from mcportfolio.models.portfolio_models import CLAProblem
from mcportfolio.solvers.cla_solver import solve_cla_problem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cla() -> None:
    # Define tickers for the portfolio
    tickers = ["META", "ABBV", "EOG", "SBUX", "BAC", "PLD"]
    
    # Create CLA problem
    problem = CLAProblem(
        description="Test CLA Portfolio Optimization",
        tickers=tickers,
        min_weight=0.0,
        max_weight=1.0,
        risk_free_rate=0.04
    )
    
    # Solve the problem
    result = solve_cla_problem(problem)
    
    if result["status"] == "success":
        data = result["data"]
        logger.info("CLA Portfolio Optimization Results:")
        logger.info("----------------------------------------")
        logger.info("Optimal Weights:")
        for ticker, weight in data["weights"].items():
            logger.info(f"  {ticker}: {weight:.2%}")
        logger.info(f"Expected Annual Return: {data['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {data['risk']:.2%}")
        logger.info(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
        
        logger.info("\nMinimum Variance Portfolio:")
        logger.info("----------------------------------------")
        for ticker, weight in data["min_variance_portfolio"]["weights"].items():
            logger.info(f"  {ticker}: {weight:.2%}")
        logger.info(f"Expected Annual Return: {data['min_variance_portfolio']['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {data['min_variance_portfolio']['risk']:.2%}")
        
        logger.info("\nMaximum Return Portfolio:")
        logger.info("----------------------------------------")
        for ticker, weight in data["max_return_portfolio"]["weights"].items():
            logger.info(f"  {ticker}: {weight:.2%}")
        logger.info(f"Expected Annual Return: {data['max_return_portfolio']['expected_return']:.2%}")
        logger.info(f"Annual Volatility: {data['max_return_portfolio']['risk']:.2%}")
    else:
        logger.error(f"Error: {result['message']}")


if __name__ == "__main__":
    test_cla() 