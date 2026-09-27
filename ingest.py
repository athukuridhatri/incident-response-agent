"""
Loads the synthetic past incidents into Hindsight memory (the 'retain' step).

Run this once before the demo:
    python ingest.py

This is the step that gives the agent its "before it had memory / after
it had memory" contrast — run the agent BEFORE this to show it flailing,
then run this, then run the agent again to show it nailing the diagnosis.
"""
from synthetic_incidents import PAST_INCIDENTS
from hindsight_setup import get_client, ensure_bank, BANK_ID


def format_incident_for_memory(incident: dict) -> str:
    """Turn a structured incident into natural-language text for retain()."""
    return (
        f"Incident {incident['id']} ({incident['severity']}) on service "
        f"'{incident['service']}': {incident['title']}.\n"
        f"Symptoms: {incident['symptoms']}\n"
        f"Root cause: {incident['root_cause']}\n"
        f"Resolution: {incident['resolution']}\n"
        f"Runbook: {incident['runbook']}\n"
        f"Occurred: {incident['timestamp']}"
    )


def main():
    client = get_client()
    ensure_bank(client)

    print(f"Retaining {len(PAST_INCIDENTS)} past incidents into bank '{BANK_ID}'...\n")
    for incident in PAST_INCIDENTS:
        content = format_incident_for_memory(incident)
        client.retain(bank_id=BANK_ID, content=content)
        print(f"  retained {incident['id']}: {incident['title']}")

    print("\nDone. The agent now has memory of these incidents.")
    print("Run: python agent.py \"<describe a new incident>\" to see it recall them.")


if __name__ == "__main__":
    main()
