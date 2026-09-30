import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from supabase_client import check_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Confirm Supabase is reachable with our key before serving requests."""
    check_connection()
    print("Server running and connected to Supabase")
    yield


app = FastAPI(title="Auth API", lifespan=lifespan)


@app.get("/", description="Returns the API name and version")
def root():
    return {"name": "Auth API", "version": "1.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
