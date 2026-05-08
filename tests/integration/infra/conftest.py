import pytest


@pytest.fixture(scope="session", autouse=False)
def localstack_check():
    import requests
    try:
        requests.get("http://localhost:4566/_localstack/health", timeout=2)
    except Exception:
        pytest.skip("LocalStack not running — start with: docker run --rm -d -p 4566:4566 localstack/localstack")