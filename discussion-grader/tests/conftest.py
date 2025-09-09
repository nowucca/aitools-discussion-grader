"""
Configuration for pytest.
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch

# Add the discussion-grader directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def mock_api_key():
    """Mock the ANTHROPIC_API_KEY environment variable for all tests."""
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-api-key-12345'}):
        yield
