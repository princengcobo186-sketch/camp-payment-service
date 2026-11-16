"""12-factor configuration. Fails closed: a missing required value stops startup."""

import os
from dataclasses import dataclass

ENVIRONMENTS = frozenset({"local", "dev", "staging", "prod"})


class ConfigError(RuntimeError):
    """Raised at startup when configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    environment: str
    log_level: str
    # Payments above this are declined by the fake provider (minor units).
    max_amount_minor: int


def load_settings(env: dict[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env

    environment = source.get("APP_ENV")
    if not environment:
        raise ConfigError("APP_ENV is required")
    if environment not in ENVIRONMENTS:
        raise ConfigError(f"APP_ENV must be one of {sorted(ENVIRONMENTS)}, got {environment!r}")

    try:
        max_amount = int(source.get("MAX_AMOUNT_MINOR", "1000000"))
    except ValueError as exc:
        raise ConfigError("MAX_AMOUNT_MINOR must be an integer") from exc
    if max_amount <= 0:
        raise ConfigError("MAX_AMOUNT_MINOR must be positive")

    return Settings(
        environment=environment,
        log_level=source.get("LOG_LEVEL", "INFO").upper(),
        max_amount_minor=max_amount,
    )
