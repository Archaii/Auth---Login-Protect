from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthError
from supabase_auth.types import User

from supabase_client import new_client

# Reads "Authorization: Bearer <token>" and registers a bearer security scheme
# in OpenAPI, which gives every route using it a padlock in Swagger UI (/docs).
# auto_error=False so we return our own 401 JSON instead of FastAPI's default.
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    description="Paste the access_token from POST /auth/login (without the word Bearer).",
    auto_error=False,
)

# Documents the guard's 401 response on every protected route in Swagger UI.
UNAUTHORIZED_RESPONSE = {
    401: {
        "description": "Missing, malformed, invalid, or expired token",
        "content": {"application/json": {"example": {"error": "Invalid or expired token"}}},
    }
}


def get_bearer_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    """Return the token from an "Authorization: Bearer <token>" header.

    Raises 401 if the header is missing, uses another scheme, or has no token.
    """
    token = credentials.credentials.strip() if credentials else ""

    if not token or " " in token:
        raise HTTPException(status_code=401, detail="Access token required")

    return token


def get_current_user(token: str = Depends(get_bearer_token)) -> User:
    """Guard for protected routes: verify the token with Supabase and return the user.

    Add `user: User = Depends(get_current_user)` to any route to protect it.
    The route body only runs if Supabase confirms the token is real, unexpired,
    and belongs to an active session.
    """
    try:
        response = new_client().auth.get_user(token)
    except AuthError:
        response = None

    if response is None or response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.user
