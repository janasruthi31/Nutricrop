import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """
    Isolated test suite configuration.
    Sets AGRI_ALLOW_TEST_BYPASS='true' strictly for test fixture execution.
    In production environments, this environment variable is unset and defaults to 'false'.
    """
    os.environ["AGRI_ALLOW_TEST_BYPASS"] = "true"
    yield
    os.environ.pop("AGRI_ALLOW_TEST_BYPASS", None)
