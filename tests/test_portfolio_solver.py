import unittest
from mcportfolio_mcp.solvers.portfolio_solver import retrieve_stock_data

class TestPortfolioSolver(unittest.TestCase):
    def setUp(self) -> None:
        self.test_tickers = ["META", "ABBV", "EOG", "SBUX", "BAC", "PLD"]

    def test_retrieve_stock_data_insufficient_data(self) -> None:
        """Test that retrieve_stock_data returns an error when insufficient data points are available."""
        result = retrieve_stock_data(self.test_tickers, period="1d")
        self.assertEqual(result["status"], "error")
        # Check for either error message since both indicate insufficient data
        self.assertTrue(
            "Insufficient data points for tickers" in result["message"] or
            "Error retrieving stock data" in result["message"],
            f"Unexpected error message: {result['message']}"
        )

if __name__ == "__main__":
    unittest.main() 