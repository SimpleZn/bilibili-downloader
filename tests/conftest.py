# Pytest configuration

import pytest

@pytest.fixture(scope="session")
def shared_resource():
    """Example shared test resource"""
    return {
        "mock_db": "sqlite:///:memory:"
    }