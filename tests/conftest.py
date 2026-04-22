"""Session-wide fixtures for the test suite."""
import pytest
from volcano_pygmt.config import load_config


@pytest.fixture(scope="session", autouse=True)
def gmt_config():
    """Load .env and configure GMT_LIBRARY_PATH once for the entire test session."""
    load_config()
