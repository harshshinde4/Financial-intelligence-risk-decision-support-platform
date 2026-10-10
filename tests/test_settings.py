import pytest
from pydantic import ValidationError

from financial_ai.config.settings import Settings


def test_default_settings_are_valid():
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.api_v1_prefix == "/api/v1"


def test_environment_and_log_level_are_normalized():
    settings = Settings(
        _env_file=None,
        app_env="DEVELOPMENT",
        log_level="info",
    )

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


@pytest.mark.parametrize("environment", ["staging", "prod", ""])
def test_invalid_environment_is_rejected(environment):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env=environment)


@pytest.mark.parametrize("level", ["TRACE", "VERBOSE", ""])
def test_invalid_log_level_is_rejected(level):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, log_level=level)


@pytest.mark.parametrize("prefix", ["api/v1", "/api/v1/", ""])
def test_invalid_api_prefix_is_rejected(prefix):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_v1_prefix=prefix)
