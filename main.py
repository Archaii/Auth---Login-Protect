import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


app = FastAPI(title="Auth API", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(protected_router)


@app.exception_handler(RequestValidationError)
def invalid_request_body(request: Request, exc: RequestValidationError):
    """Return 400 with our JSON error shape instead of FastAPI's default 422."""
    return JSONResponse(status_code=400, content={"error": "Request body must be a valid JSON object"})


@app.get("/", description="Returns the API name and version")
def root():
    return {"name": "Auth API", "version": "1.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
