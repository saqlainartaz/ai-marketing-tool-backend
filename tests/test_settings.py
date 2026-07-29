import pytest
from pydantic import ValidationError

from content_engine.config import Settings


def test_boot_fails_closed_without_service_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SERVICE_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_boot_fails_closed_on_short_service_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_API_KEY", "too-short")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_load_with_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_API_KEY", "a-sufficiently-long-service-key")
    settings = Settings(_env_file=None)
    assert settings.service_api_key.get_secret_value() == "a-sufficiently-long-service-key"
