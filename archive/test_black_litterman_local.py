import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcportfolio.solvers.black_litterman_solver import solve_problem
from mcportfolio.models.portfolio_models import PortfolioProblem, MarketView, SectorView, BlackLittermanConfig


def test_black_litterman_local():
    problem = PortfolioProblem(
        description="Optimize portfolio using Black-Litterman model with market views",
        tickers=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "JPM", "V", "JNJ", "UNH"],
        constraints=["max_weight 0.3"],
        views=[
            MarketView(ticker="NVDA", view="outperform", magnitude=0.05, confidence=0.7),
            MarketView(ticker="JPM", view="underperform", magnitude=0.02, confidence=0.6),
            SectorView(sector="tech", tickers=["AAPL", "MSFT", "NVDA"], view="outperform", magnitude=0.03, confidence=0.8)
        ],
        black_litterman=BlackLittermanConfig(risk_aversion=2.5, tau=0.05)
    )

    result = solve_problem(problem)
    if result["status"] == "success":
        data = result["data"]
        print("\nBlack-Litterman Portfolio Optimization Results:")
        print("\nOptimal Portfolio Weights:")
        for ticker, weight in data["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
        print("\nPortfolio Performance Metrics:")
        print(f"Expected Annual Return: {data['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {data['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
        print("\nImplied Returns from Black-Litterman Model:")
        for ticker, ret in data["implied_returns"].items():
            print(f"{ticker}: {ret*100:.2f}%")
        print("\nMinimum Variance Portfolio:")
        for ticker, weight in data["min_variance_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
        print(f"Expected Return: {data['min_variance_portfolio']['expected_return']*100:.2f}%")
        print(f"Risk: {data['min_variance_portfolio']['risk']*100:.2f}%")
        print("\nMaximum Return Portfolio:")
        for ticker, weight in data["max_return_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
        print(f"Expected Return: {data['max_return_portfolio']['expected_return']*100:.2f}%")
        print(f"Risk: {data['max_return_portfolio']['risk']*100:.2f}%")
    else:
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    test_black_litterman_local() 