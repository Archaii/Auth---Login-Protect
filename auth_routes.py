from fastapi import APIRouter, Body, Depends, Response
from fastapi.responses import JSONResponse
from supabase_auth.errors import AuthError

from auth_guard import UNAUTHORIZED_RESPONSE, get_bearer_token, get_current_user
from supabase_client import new_client

router = APIRouter(prefix="/auth", tags=["auth"])

CREDENTIALS_EXAMPLE = {"email": "test@example.com", "password": "password123"}

# Error responses shown in Swagger UI (/docs).
BAD_REQUEST_RESPONSE = {
    400: {
        "description": "Missing email or password, or input rejected by Supabase",
        "content": {"application/json": {"example": {"error": "Email and password are required"}}},
    }
}
INVALID_LOGIN_RESPONSE = {
    401: {
        "description": "Wrong email or password",
        "content": {"application/json": {"example": {"error": "Invalid login credentials"}}},
    }
}


def read_credentials(payload: dict | None):
    """Return (email, password), or None if either is missing or not a string."""
    if not payload:
        return None

    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not email.strip():
        return None
    if not isinstance(password, str) or not password:
        return None

    return email.strip(), password


@router.post(
    "/signup",
    status_code=201,
    description="Creates a new user account in Supabase Auth",
    responses=BAD_REQUEST_RESPONSE,
)
def signup(payload: dict | None = Body(default=None, examples=[CREDENTIALS_EXAMPLE])):
    credentials = read_credentials(payload)

    if credentials is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"},
        )

    email, password = credentials

    try:
        response = new_client().auth.sign_up({"email": email, "password": password})
    except AuthError as error:
        # Supabase rejected the input: already registered, weak password,
        # invalid email, or too many signups (429).
        status = 429 if getattr(error, "status", None) == 429 else 400
        return JSONResponse(status_code=status, content={"error": error.message})

    return {"user": response.user.model_dump(mode="json")}


@router.post(
    "/login",
    description="Logs in with email and password and returns a JWT access token",
    responses={**BAD_REQUEST_RESPONSE, **INVALID_LOGIN_RESPONSE},
)
def login(payload: dict | None = Body(default=None, examples=[CREDENTIALS_EXAMPLE])):
    credentials = read_credentials(payload)

    if credentials is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"},
        )

    email, password = credentials

    try:
        response = new_client().auth.sign_in_with_password({"email": email, "password": password})
    except AuthError as error:
        if getattr(error, "status", None) == 429:
            return JSONResponse(status_code=429, content={"error": error.message})
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid login credentials"},
        )

    session = response.session

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": session.token_type,
        "expires_in": session.expires_in,
    }


@router.post(
    "/logout",
    status_code=204,
    dependencies=[Depends(get_current_user)],
    description="Ends the current session. Requires a Bearer token.",
    responses=UNAUTHORIZED_RESPONSE,
)
def logout(token: str = Depends(get_bearer_token)):
    # Our per-request client holds no session, so auth.sign_out() alone would
    # have nothing to revoke. admin.sign_out(token) is the call sign_out() makes
    # internally: it sends the user's own JWT (not the service_role key) to
    # Supabase, which ends this session and revokes its refresh token.
    new_client().auth.admin.sign_out(token, scope="local")

    return Response(status_code=204)
