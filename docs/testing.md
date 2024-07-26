# Testing Documentation for Pixashot

This document outlines the process for setting up the testing environment and running tests for the Pixashot project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Continuous Integration](#continuous-integration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up the testing environment, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. First, clone the Pixashot repository if you haven't already:

   ```bash
   git clone https://github.com/yourusername/pixashot.git
   cd pixashot
   ```

2. It's recommended to use a virtual environment. Create and activate one using:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Install the testing dependencies:

   ```bash
   pip install pytest pytest-asyncio pytest-cov
   ```

## Running Tests

To run all tests, use the following command from the project root directory:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=src
```

To run a specific test file:

```bash
pytest tests/test_capture_service.py
```

To run tests matching a specific name pattern:

```bash
pytest -k "test_capture"
```

## Writing Tests

- All test files should be placed in the `tests/` directory and follow the naming convention `test_*.py`.
- Use descriptive names for your test functions, prefixed with `test_`.
- Use fixtures for setup and teardown operations.
- For testing asynchronous code, use the `@pytest.mark.asyncio` decorator and `async/await` syntax.

Example:

```python
import pytest

@pytest.mark.asyncio
async def test_capture_screenshot():
    # Test code here
    assert result == expected_result
```

## Continuous Integration

Pixashot uses GitHub Actions for continuous integration. The configuration file is located at `.github/workflows/tests.yml`.

To trigger CI:
1. Push your changes to a branch on GitHub.
2. Create a pull request.
3. GitHub Actions will automatically run the tests.

## Troubleshooting

If you encounter any issues while running tests, try the following:

1. Ensure all dependencies are correctly installed:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov
   ```

2. Check that you're in the correct directory (project root) when running tests.

3. If you're getting import errors, make sure your `PYTHONPATH` includes the project root:
   ```bash
   export PYTHONPATH=.
   ```

4. For issues with async tests, ensure you're using Python 3.7+ and have `pytest-asyncio` installed.

If problems persist, please open an issue on the GitHub repository with details about the error and your environment.

## Best Practices

1. Keep tests isolated: Each test should be independent and not rely on the state from other tests.
2. Use mocking: For external dependencies, use `unittest.mock` or `pytest-mock` to create mock objects.
3. Parameterize tests: Use `@pytest.mark.parametrize` to run the same test with different inputs.
4. Maintain test coverage: Aim for high test coverage, especially for critical paths in your code.
5. Update tests with code changes: When modifying functionality, always update or add corresponding tests.

Remember, good tests are essential for maintaining code quality and facilitating future development. Happy testing!