"""
The Incident Response Agent.

This agent can diagnose an incident:
1. Without memory (cold start)
2. With Hindsight memory

The goal is to clearly demonstrate how Hindsight improves
incident diagnosis by recalling relevant past incidents.
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from hindsight_setup import get_client, BANK_ID


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# GROQ CONFIGURATION
# ---------------------------------------------------------

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# Maximum number of recalled memory chunks passed to the model.
MAX_MEMORIES = 8


# ---------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------

SYSTEM_PROMPT = """You are an on-call incident response assistant for a \
backend engineering team. You help engineers quickly diagnose production \
incidents.

You will be given:
- A description of a NEW incident
- Zero or more MEMORY entries retrieved from past incidents. Entries are \
fragments: several entries may come from the same incident, and one \
fragment may hold the symptoms while another holds the root cause or fix.

Rules:
- If the memory contains a genuinely similar past incident, explicitly \
name that incident ID and use its documented root cause and resolution \
when relevant. Combine fragments that belong to the same incident.
- Clearly explain how the current symptoms match the historical incident.
- Only state a root cause or resolution "from" a past incident if it \
appears in the MEMORY text. If the memory shows the symptoms but not the \
root cause or fix, say that plainly instead of guessing what it was.
- Do not replace a known historical root cause with a generic guess.
- If the memory is empty or not clearly relevant, say so plainly \
("I don't have a similar past incident in memory") and provide a generic \
diagnosis based on the available symptoms.
- Be concise, concrete, and actionable.
- Never fabricate a past incident ID that wasn't provided in memory.
"""


# ---------------------------------------------------------
# DIAGNOSE INCIDENT
# ---------------------------------------------------------

def diagnose(
    new_incident_description: str,
    use_memory: bool = True
) -> dict:
    """
    Diagnose a new incident.

    use_memory=True:
        Recall relevant incidents from Hindsight.

    use_memory=False:
        Skip Hindsight to simulate a cold-start agent.

    Returns:
        memories  -> recalled Hindsight memories
        diagnosis -> Groq-generated diagnosis
    """

    memories = []

    # -----------------------------------------------------
    # HINDSIGHT MEMORY
    # -----------------------------------------------------

    if use_memory:

        client = get_client()

        recall_result = client.recall(
            bank_id=BANK_ID,
            query=new_incident_description,
            max_tokens=2000,
        )

        # Hindsight can return several chunks from the same incident
        # (symptoms in one chunk, root cause or fix in another).
        # Only drop exact duplicate text so sibling chunks are kept.
        seen_texts = set()

        for m in getattr(recall_result, "results", []):

            text = m.text.strip()

            if not text or text in seen_texts:
                continue

            seen_texts.add(text)
            memories.append(text)

            if len(memories) >= MAX_MEMORIES:
                break

    # -----------------------------------------------------
    # PREPARE MEMORY FOR THE MODEL
    # -----------------------------------------------------

    if memories:
        memory_block = "\n\n".join(f"- {memory}" for memory in memories)
    else:
        memory_block = "(no memories retrieved)"

    # -----------------------------------------------------
    # GROQ CLIENT (OpenAI-compatible endpoint)
    # -----------------------------------------------------

    llm_client = OpenAI(
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )

    # -----------------------------------------------------
    # PROMPT
    # -----------------------------------------------------

    user_prompt = (
        f"NEW INCIDENT:\n"
        f"{new_incident_description}\n\n"
        f"MEMORY (past incident fragments retrieved as potentially relevant):\n"
        f"{memory_block}\n\n"
        f"Diagnose the new incident."
    )

    # -----------------------------------------------------
    # DIAGNOSIS
    # -----------------------------------------------------

    response = llm_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return {
        "memories": memories,
        "diagnosis": response.choices[0].message.content,
    }


# ---------------------------------------------------------
# COMMAND-LINE MODE
# ---------------------------------------------------------

def main():

    if len(sys.argv) < 2:
        print('Usage: python agent.py "description of the new incident"')
        sys.exit(1)

    description = " ".join(sys.argv[1:])

    result = diagnose(description)

    print("=" * 70)
    print("RECALLED MEMORIES:")
    print("=" * 70)

    if result["memories"]:
        for memory in result["memories"]:
            print(f"- {memory}\n")
    else:
        print("(none - agent has no relevant memory for this incident)\n")

    print("=" * 70)
    print("AGENT DIAGNOSIS:")
    print("=" * 70)

    print(result["diagnosis"])


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()