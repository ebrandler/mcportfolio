import requests
import json

def test_black_litterman():
    """Test the Black-Litterman solver with market views."""
    
    # Define the portfolio problem with market views
    problem = {
        "description": "Optimize portfolio using Black-Litterman model with market views",
        "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "JPM", "V", "JNJ", "UNH"],
        "constraints": ["max_weight 0.3"],
        "views": [
            {
                "ticker": "NVDA",
                "view": "outperform",
                "magnitude": 0.05,
                "confidence": 0.7
            },
            {
                "ticker": "JPM",
                "view": "underperform",
                "magnitude": 0.02,
                "confidence": 0.6
            },
            {
                "sector": "tech",
                "tickers": ["AAPL", "MSFT", "NVDA"],
                "view": "outperform",
                "magnitude": 0.03,
                "confidence": 0.8
            }
        ],
        "black_litterman": {
            "risk_aversion": 2.5,
            "tau": 0.05
        }
    }
    
    # Add authentication headers
    headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }
    
    # Send request to the Black-Litterman solver endpoint
    response = requests.post(
        "http://localhost:8000/solve/black_litterman",
        json=problem,
        headers=headers
    )
    
    # Print the results
    if response.status_code == 200:
        result = response.json()
        print("\nBlack-Litterman Portfolio Optimization Results:")
        print("\nOptimal Portfolio Weights:")
        for ticker, weight in result["data"]["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
            
        print("\nPortfolio Performance Metrics:")
        print(f"Expected Annual Return: {result['data']['expected_return']*100:.2f}%")
        print(f"Annual Volatility: {result['data']['risk']*100:.2f}%")
        print(f"Sharpe Ratio: {result['data']['sharpe_ratio']:.2f}")
        
        print("\nImplied Returns from Black-Litterman Model:")
        for ticker, ret in result["data"]["implied_returns"].items():
            print(f"{ticker}: {ret*100:.2f}%")
            
        print("\nMinimum Variance Portfolio:")
        for ticker, weight in result["data"]["min_variance_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
        print(f"Expected Return: {result['data']['min_variance_portfolio']['expected_return']*100:.2f}%")
        print(f"Risk: {result['data']['min_variance_portfolio']['risk']*100:.2f}%")
        
        print("\nMaximum Return Portfolio:")
        for ticker, weight in result["data"]["max_return_portfolio"]["weights"].items():
            print(f"{ticker}: {weight*100:.1f}%")
        print(f"Expected Return: {result['data']['max_return_portfolio']['expected_return']*100:.2f}%")
        print(f"Risk: {result['data']['max_return_portfolio']['risk']*100:.2f}%")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_black_litterman() 