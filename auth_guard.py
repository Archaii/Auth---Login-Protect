from fastapi import Depends, Header, HTTPException
from supabase_auth.errors import AuthError
from supabase_auth.types import User

from supabase_client import new_client


def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Return the token from an "Authorization: Bearer <token>" header.

    Raises 401 if the header is missing, uses another scheme, or has no token.
    """
    parts = authorization.split() if authorization else []

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Access token required")

    return parts[1]


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
