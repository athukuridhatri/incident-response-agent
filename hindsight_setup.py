"""
Shared Hindsight client factory.

Keeps a single place where we read env vars and construct the client,
so ingest.py, agent.py, and cli.py all talk to the same bank.
"""
import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
API_KEY = os.environ.get("HINDSIGHT_API_KEY")
BANK_ID = os.environ.get("HINDSIGHT_BANK_ID", "incident-response-agent")


def get_client() -> Hindsight:
    if not API_KEY:
        raise RuntimeError(
            "HINDSIGHT_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return Hindsight(base_url=BASE_URL, api_key=API_KEY)


def ensure_bank(client: Hindsight):
    """Create the incident-response bank if it doesn't exist yet."""
    try:
        client.create_bank(
            bank_id=BANK_ID,
            name="Incident Response Agent",
            background=(
                "This agent helps on-call engineers diagnose production "
                "incidents by recalling similar past incidents, their root "
                "causes, and how they were resolved."
            ),
        )
        print(f"Created Hindsight bank: {BANK_ID}")
    except Exception as e:
        # Bank likely already exists — that's fine, not fatal.
        print(f"Bank '{BANK_ID}' already exists or could not be created fresh ({e}). Continuing.")
