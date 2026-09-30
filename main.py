import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from auth_routes import router as auth_router
from protected_routes import router as protected_router
from public_routes import router as public_router
from supabase_client import check_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Confirm Supabase is reachable with our key before serving requests."""
    check_connection()
    print("Server running and connected to Supabase")
    yield


app = FastAPI(
    title="Auth API",
    version="1.0",
    description=(
        "Sign up, log in, and log out with Supabase Auth. "
        "To call a protected route: log in, copy the `access_token`, "
        "click **Authorize**, and paste it."
    ),
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(protected_router)


@app.exception_handler(RequestValidationError)
def invalid_request_body(request: Request, exc: RequestValidationError):
    """Return 400 with our JSON error shape instead of FastAPI's default 422."""
    return JSONResponse(status_code=400, content={"error": "Request body must be a valid JSON object"})


@app.exception_handler(HTTPException)
def http_error(request: Request, exc: HTTPException):
    """Return {"error": ...} instead of FastAPI's default {"detail": ...}.

    Covers the 401s raised by the auth guard, plus 404 and 405.
    """
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail}, headers=exc.headers)


def custom_openapi():
    """Drop the automatic 422 responses from the docs.

    invalid_request_body() turns every validation error into a 400, so the API
    never actually returns 422.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for operations in schema["paths"].values():
        for operation in operations.values():
            operation.get("responses", {}).pop("422", None)

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.get("/", description="Returns the API name and version")
def root():
    return {"name": "Auth API", "version": "1.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
