from mcportfolio.models.portfolio_models import PortfolioProblem
from mcportfolio.solvers.portfolio_methods import (
    calculate_portfolio_metrics,
    calculate_risk_metrics,
    calculate_performance_metrics,
)

def test_portfolio_methods():
    # Define test portfolio problem
    problem = PortfolioProblem(
        description="Test portfolio optimization with various methods",
        tickers=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "JPM", "V", "JNJ", "UNH"],
        constraints=["max_weight 0.3"],
        objective="maximize_sharpe_ratio"
    )
    
    # Test CVaR optimization
    print("\nTesting CVaR Optimization:")
    cvar_result = calculate_portfolio_metrics(problem, "cvar")
    if cvar_result["status"] == "success":
        print("CVaR Portfolio Weights (Max Sharpe):")
        for ticker, weight in cvar_result["data"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"\nExpected Annual Return: {cvar_result['data']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {cvar_result['data']['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {cvar_result['data']['sharpe_ratio']:.2f}")
        print(f"CVaR: {cvar_result['data']['cvar']*100:.2f}%")
        print("\nMinimum CVaR Portfolio:")
        for ticker, weight in cvar_result["data"]["min_cvar_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"Expected Annual Return: {cvar_result['data']['min_cvar_portfolio']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {cvar_result['data']['min_cvar_portfolio']['risk']*100:.2f}%")
        print(f"CVaR: {cvar_result['data']['min_cvar_portfolio']['cvar']*100:.2f}%")
    else:
        print(f"Error in CVaR optimization: {cvar_result['message']}")
    
    # Test CDaR optimization
    print("\nTesting CDaR Optimization:")
    cdar_result = calculate_portfolio_metrics(problem, "cdar")
    if cdar_result["status"] == "success":
        print("CDaR Portfolio Weights (Max Sharpe):")
        for ticker, weight in cdar_result["data"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"\nExpected Annual Return: {cdar_result['data']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {cdar_result['data']['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {cdar_result['data']['sharpe_ratio']:.2f}")
        print(f"CDaR: {cdar_result['data']['cdar']*100:.2f}%")
        print("\nMinimum CDaR Portfolio:")
        for ticker, weight in cdar_result["data"]["min_cdar_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"Expected Annual Return: {cdar_result['data']['min_cdar_portfolio']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {cdar_result['data']['min_cdar_portfolio']['risk']*100:.2f}%")
        print(f"CDaR: {cdar_result['data']['min_cdar_portfolio']['cdar']*100:.2f}%")
    else:
        print(f"Error in CDaR optimization: {cdar_result['message']}")
    
    # Test Semivariance optimization
    print("\nTesting Semivariance Optimization:")
    semivar_result = calculate_portfolio_metrics(problem, "semivariance")
    if semivar_result["status"] == "success":
        print("Semivariance Portfolio Weights (Max Sharpe):")
        for ticker, weight in semivar_result["data"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"\nExpected Annual Return: {semivar_result['data']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {semivar_result['data']['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {semivar_result['data']['sharpe_ratio']:.2f}")
        print(f"Semivariance: {semivar_result['data']['semivariance']*100:.2f}%")
        print("\nMinimum Semivariance Portfolio:")
        for ticker, weight in semivar_result["data"]["min_semivariance_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"Expected Annual Return: {semivar_result['data']['min_semivariance_portfolio']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {semivar_result['data']['min_semivariance_portfolio']['risk']*100:.2f}%")
        print(f"Semivariance: {semivar_result['data']['min_semivariance_portfolio']['semivariance']*100:.2f}%")
    else:
        print(f"Error in Semivariance optimization: {semivar_result['message']}")
    
    # Test HRP optimization
    print("\nTesting HRP Optimization:")
    hrp_result = calculate_portfolio_metrics(problem, "hrp")
    if hrp_result["status"] == "success":
        print("HRP Portfolio Weights:")
        for ticker, weight in hrp_result["data"]["weights"].items():
            print(f"{ticker}: {weight*100:.2f}%")
        print(f"\nExpected Annual Return: {hrp_result['data']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {hrp_result['data']['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {hrp_result['data']['sharpe_ratio']:.2f}")
    else:
        print(f"Error in HRP optimization: {hrp_result['message']}")

if __name__ == "__main__":
    test_portfolio_methods() 