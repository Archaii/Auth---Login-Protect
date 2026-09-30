import os

import truststore

# Verify HTTPS with the operating system's certificate store instead of
# Python's bundled one. Needed when antivirus software (e.g. AVG) scans HTTPS
# traffic and re-signs certificates with its own root. Must run before httpx
# and supabase create any connections.
truststore.inject_into_ssl()

import httpx
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env (see .env.example)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_connection():
    """Ping Supabase Auth so startup fails loudly if the URL or key is wrong.

    create_client() makes no network call, so without this the server would
    start even with a bad .env and only fail on the first request.
    """
    response = httpx.get(
        f"{SUPABASE_URL}/auth/v1/health",
        headers={"apikey": SUPABASE_KEY},
        timeout=10,
    )
    response.raise_for_status()
