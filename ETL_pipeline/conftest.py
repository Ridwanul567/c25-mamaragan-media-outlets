"""Pytest configuration and global fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def mock_aws_credentials():
    """Mock environment variables for AWS credentials so tests run offline cleanly."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
