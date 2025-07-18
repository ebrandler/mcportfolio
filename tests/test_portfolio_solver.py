import unittest
from mcportfolio.solvers.portfolio_solver import retrieve_stock_data

class TestPortfolioSolver(unittest.TestCase):
    def setUp(self) -> None:
        self.test_tickers = ["META", "ABBV", "EOG", "SBUX", "BAC", "PLD"]

    def test_retrieve_stock_data_insufficient_data(self) -> None:
        """Test that retrieve_stock_data returns an error when insufficient data points are available."""
        result = retrieve_stock_data(self.test_tickers, period="1d")
        self.assertEqual(result["status"], "error")
        # Check for error messages that indicate data retrieval failure
        self.assertTrue(
            "Insufficient data points for tickers" in result["message"] or
            "Error retrieving stock data" in result["message"] or
            "Unable to retrieve real market data" in result["message"],
            f"Unexpected error message: {result['message']}"
        )

if __name__ == "__main__":
    unittest.main() 