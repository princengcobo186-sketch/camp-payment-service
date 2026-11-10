import pytest

from payment_service.config import ConfigError, load_settings


def test_missing_app_env_fails_closed():
    with pytest.raises(ConfigError, match="APP_ENV is required"):
        load_settings({})


def test_unknown_environment_rejected():
    with pytest.raises(ConfigError, match="must be one of"):
        load_settings({"APP_ENV": "qa"})


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_invalid_max_amount_rejected(value):
    with pytest.raises(ConfigError):
        load_settings({"APP_ENV": "local", "MAX_AMOUNT_MINOR": value})


def test_defaults():
    s = load_settings({"APP_ENV": "dev"})
    assert (s.environment, s.log_level, s.max_amount_minor) == ("dev", "INFO", 1_000_000)
