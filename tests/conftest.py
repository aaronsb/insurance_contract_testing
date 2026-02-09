import pytest

from policy.green_cross import green_cross_policy


@pytest.fixture
def policy():
    """The Green Cross contract as source of truth for all verification tests."""
    return green_cross_policy
