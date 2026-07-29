import secrets

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_service_token(
    request: Request,
    api_key: str | None = Security(_api_key_header),
) -> None:
    """Service-token auth: authenticates the calling service (the frontend
    server), not end users. See docs/API_CONTRACT.md for the v1 trust model."""
    expected = request.app.state.settings.service_api_key.get_secret_value()
    if api_key is None or not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing service token")
