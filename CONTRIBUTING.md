# Contributing to MCPortfolio

Thank you for your interest in contributing to MCPortfolio! This document provides guidelines and instructions for setting up the development environment and contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mcportfolio.git
   cd mcportfolio
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass:
   ```bash
   pytest
   ```

3. Run code quality checks:
   ```bash
   black .
   ruff check .
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "feat: add new feature"
   ```

5. Push your branch and create a pull request.

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep lines under 120 characters
- Use meaningful variable and function names

## Testing

- Write tests for all new features
- Maintain or improve test coverage
- Run tests before submitting a pull request:
  ```bash
  pytest --cov=mcportfolio_mcp
  ```

## Documentation

- Update documentation for any new features or changes
- Keep docstrings up to date
- Add examples for new functionality

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the version numbers in pyproject.toml
3. The PR will be merged once you have the sign-off of at least one other developer

## License

By contributing, you agree that your contributions will be licensed under the project's Apache 2.0 License. 