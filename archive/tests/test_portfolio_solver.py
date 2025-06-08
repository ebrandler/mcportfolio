import unittest
import numpy as np
import pandas as pd
from mcportfolio.models.portfolio_models import PortfolioProblem
from mcportfolio.solvers.portfolio_solver import solve_problem, retrieve_stock_data

class TestPortfolioSolver(unittest.TestCase):
    def setUp(self):
        """Set up test cases with different portfolio configurations."""
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]
        self.test_problem = PortfolioProblem(
            description="Test portfolio optimization",
            tickers=self.test_tickers,
            constraints=["max_weight 0.4"],
            objective="maximize_sharpe_ratio"
        )

    def test_data_retrieval(self):
        """Test stock data retrieval functionality."""
        result = retrieve_stock_data(self.test_tickers, period="1y")
        
        # Check response structure
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        data = result["data"]
        self.assertIn("returns", data)
        self.assertIn("mean_returns", data)
        self.assertIn("cov_matrix", data)
        
        # Check data types and shapes
        returns_df = pd.DataFrame(data["returns"])
        self.assertEqual(len(returns_df.columns), len(self.test_tickers))
        self.assertTrue(returns_df.notna().all().all())

    def test_optimization_constraints(self):
        """Test that optimization respects constraints."""
        result = solve_problem(self.test_problem)
        
        self.assertEqual(result["status"], "success")
        data = result["data"]
        
        # Check weights sum to 1
        weights = data["weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        
        # Check no shorting
        self.assertTrue(all(w >= 0 for w in weights.values()))
        
        # Check max weight constraint
        self.assertTrue(all(w <= 0.4 for w in weights.values()))

    def test_portfolio_metrics(self):
        """Test portfolio metrics calculations."""
        result = solve_problem(self.test_problem)
        
        self.assertEqual(result["status"], "success")
        data = result["data"]
        
        # Check metrics exist and are positive
        self.assertIn("expected_return", data)
        self.assertIn("risk", data)
        self.assertIn("sharpe_ratio", data)
        
        self.assertGreater(data["expected_return"], 0)
        self.assertGreater(data["risk"], 0)
        self.assertGreater(data["sharpe_ratio"], 0)

    def test_min_variance_portfolio(self):
        """Test minimum variance portfolio properties."""
        result = solve_problem(self.test_problem)
        
        self.assertEqual(result["status"], "success")
        min_var = result["data"]["min_variance_portfolio"]
        
        # Check weights sum to 1
        weights = min_var["weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        
        # Check risk is lower than optimal portfolio
        self.assertLess(min_var["risk"], result["data"]["risk"])

    def test_max_return_portfolio(self):
        """Test maximum return portfolio properties."""
        result = solve_problem(self.test_problem)
        
        self.assertEqual(result["status"], "success")
        max_ret = result["data"]["max_return_portfolio"]
        
        # Check weights sum to 1
        weights = max_ret["weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        
        # Check return is higher than optimal portfolio
        self.assertGreater(max_ret["expected_return"], result["data"]["expected_return"])

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test with invalid ticker
        invalid_problem = PortfolioProblem(
            description="Invalid portfolio",
            tickers=["INVALID_TICKER"],
            constraints=["max_weight 0.4"],
            objective="maximize_sharpe_ratio"
        )
        result = solve_problem(invalid_problem)
        self.assertEqual(result["status"], "error")
        
        # Test with empty tickers
        empty_problem = PortfolioProblem(
            description="Empty portfolio",
            tickers=[],
            constraints=["max_weight 0.4"],
            objective="maximize_sharpe_ratio"
        )
        result = solve_problem(empty_problem)
        self.assertEqual(result["status"], "error")

    def test_consistency(self):
        """Test consistency of results across multiple runs."""
        result1 = solve_problem(self.test_problem)
        result2 = solve_problem(self.test_problem)
        
        self.assertEqual(result1["status"], "success")
        self.assertEqual(result2["status"], "success")
        
        # Compare weights
        weights1 = result1["data"]["weights"]
        weights2 = result2["data"]["weights"]
        for ticker in self.test_tickers:
            self.assertAlmostEqual(weights1[ticker], weights2[ticker], places=6)

if __name__ == '__main__':
    unittest.main() 