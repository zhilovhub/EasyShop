import pytest

from common_utils.config import settings
from common_utils.config.env_config import Mode


@pytest.fixture(scope="session")
async def check_test_env():
    assert settings.MODE == Mode.TEST
