# Incident Response Agent, built with Hindsight

An on-call assistant that diagnoses production incidents by **recalling similar past incidents** from persistent memory, instead of reasoning from the current symptoms alone.

> **Scope note:** this is a demonstration built on **six synthetic incidents** written for the project. It does not use real production data, and the agent does not learn automatically from conversations. Incidents enter its memory only when `ingest.py` is run.

## The problem

When an alert fires, responders usually ask "have we seen this before?" Answering means reconstructing history from someone's memory, old tickets, chat threads and runbooks. A plain LLM assistant can reason about the current symptoms, but it has no access to the team's history, so it can't say "this matched the checkout incident in June, and here is what fixed it."

## How Hindsight is used

[Hindsight](https://github.com/vectorize-io/hindsight) is the agent's memory layer. The repository contains no vector database, embedding code or retrieval logic. It only calls the Hindsight client.

- **Retain** (`ingest.py`): each synthetic incident is formatted as natural-language text (ID, severity, service, title, symptoms, root cause, resolution, runbook, timestamp) and stored in a Hindsight memory bank:

  ```python
  content = format_incident_for_memory(incident)
  client.retain(bank_id=BANK_ID, content=content)
  ```

- **Recall** (`agent.py`): the new incident description is used as the query, and the recalled memories are passed to the LLM:

  ```python
  recall_result = client.recall(
      bank_id=BANK_ID,
      query=new_incident_description,
      max_tokens=2000,
  )
  ```

Recall returns memory as fragments, and one incident can be split across several (for example symptoms in one, root cause and resolution in others). The agent therefore removes only exact-duplicate text and keeps up to 8 fragments (`MAX_MEMORIES = 8`). See [Design note](#design-note-dont-deduplicate-recall-by-incident) below.

## Workflow

```text
New incident description
        |
        v
  use_memory=True? --- no ---> LLM diagnoses from symptoms only (cold start)
        | yes
        v
 Hindsight recall (up to 8 fragments, exact-text dedupe)
        |
        v
 Groq LLM (openai/gpt-oss-120b) with the recalled memory
        |
        v
 Memory-grounded diagnosis
```

## Features

- `diagnose(description, use_memory=True/False)` runs the same prompt and model with or without Hindsight, so the before/after comparison is fair.
- The system prompt tells the model that memory entries are fragments to combine, and that a root cause or resolution may be attributed to a past incident only if it appears in the recalled text.
- If memory is empty or not relevant, the agent is instructed to say so plainly and fall back to a generic diagnosis.
- `demo.py` prints the cold-start diagnosis, the recalled Hindsight memory, and the memory-grounded diagnosis in separate panels.

## Project structure

```text
.
├── agent.py                 # recall + diagnosis (use_memory flag), CLI entry point
├── demo.py                  # side-by-side cold-start vs Hindsight demo
├── hindsight_setup.py       # Hindsight client and memory bank setup
├── ingest.py                # retains the synthetic incidents into Hindsight
├── synthetic_incidents.py   # 6 synthetic past incidents
├── requirements.txt
└── .env.example
```

## Setup

### 1. Install

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Developed with Python 3.13.

### 2. Get keys

- **Hindsight:** sign up for [Hindsight Cloud](https://ui.hindsight.vectorize.io) and create an API key, or run Hindsight yourself using the [documentation](https://hindsight.vectorize.io/).
- **Groq:** create an API key at [console.groq.com](https://console.groq.com).

### 3. Configure

```bash
cp .env.example .env            # Windows: copy .env.example .env
```

Edit `.env` and fill in your own values. `.env` is git-ignored; never commit it.

## Environment variables

| Variable | Purpose |
|---|---|
| `HINDSIGHT_BASE_URL` | Hindsight instance URL (defaults to `https://api.hindsight.vectorize.io` in code) |
| `HINDSIGHT_API_KEY` | Your Hindsight API key (required) |
| `HINDSIGHT_BANK_ID` | Memory bank name (defaults to `incident-response-agent` in code) |
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | Optional; defaults to `openai/gpt-oss-120b` |

The LLM is called through the OpenAI-compatible client against `https://api.groq.com/openai/v1`.

## Run

### Load the synthetic incidents into memory

```bash
python ingest.py
```

This creates the memory bank if needed and calls `retain` once per incident. It prints `Retaining 6 past incidents...`.

Run it **once** per bank. It does not check whether the incidents are already stored, so running it repeatedly can store them repeatedly. For a clean bank, set a new `HINDSIGHT_BANK_ID`.

### Run the demo

```bash
python demo.py
```

`demo.py` runs one incident through the agent twice, without and then with Hindsight memory. Run `ingest.py` first.

The Hindsight client may print "Unclosed client session" warnings. To hide them:

```bash
python demo.py 2>/dev/null      # Windows cmd: python demo.py 2>nul
```

### Diagnose your own incident

```bash
python agent.py "Checkout API is returning intermittent 502s right after a promo email"
```

This always uses memory and prints the recalled fragments followed by the diagnosis.

## Example: cold start vs Hindsight

Demo incident:

> Checkout API is returning intermittent 502s again, started about 10 minutes ago. We're seeing it spike right after that promo email went out this morning. p99 latency on /checkout/create is climbing fast.

**Without memory** (`use_memory=False`): the agent says it has no similar past incident and gives a generic diagnostic plan. It lists possible causes (traffic surge, downstream overload, connection-pool exhaustion, circuit-breaker or timeout settings, recent configuration changes, network issues) followed by diagnostic steps. Nothing in it is specific to this team's history.

**With Hindsight memory:** Hindsight returned 8 memory matches. They included synthetic incident INC-1042: intermittent 502s on `checkout-api` after a marketing email blast, p99 latency on `/checkout/create` rising from about 300 ms to several seconds, a documented root cause of a PgBouncer connection-pool limit of 20 connections for the `checkout-db` PostgreSQL database (requests queued and exceeded the 5-second upstream gateway timeout), and a documented resolution (raise `max_client_conn` from 20 to 100, enable transaction pooling, add a CloudWatch alarm on connection-wait time). The diagnosis identified the new incident as a likely repeat of INC-1042 and used that documented root cause and resolution.

LLM output varies between runs, so exact wording will differ.

## Design note: don't deduplicate recall by incident

The first version of the recall logic kept one fragment per incident ID. For INC-1042 the surviving fragment was the symptoms, and the fragments with the root cause and resolution were discarded. The model then wrote a plausible generic "root cause" and attributed it to INC-1042, which was worse than having no memory, because the cited ID made the guess look verified.

The fix was to deduplicate only exact-duplicate text, keep up to 8 fragments, and add a prompt rule that root causes and resolutions may only be attributed if they appear in the recalled text.

## Technologies

- [Hindsight](https://github.com/vectorize-io/hindsight) (`hindsight-client`) for persistent agent memory
- Groq, using the `openai` Python client with model `openai/gpt-oss-120b`
- `python-dotenv` for configuration
- `rich` for the terminal demo output

## Limitations

- **Synthetic, small data.** Six incidents written for this project, and the demo alert is deliberately similar to one of them. No recall quality, accuracy or latency measurements have been done.
- **No automatic learning.** `diagnose()` never writes to memory. Incidents are added only by running `ingest.py`.
- **Near-duplicate recall.** Some recalled fragments restate the same fact in different words, which exact-text deduplication does not remove.
- **Ingest is not idempotent.** See the note under [Run](#load-the-synthetic-incidents-into-memory).
- **Production would need more:** data governance (access control, retention, sensitive content in logs and tickets), validation of recalled facts against source records, and integration with real incident systems such as ticketing, paging and postmortem tools.

## Resources

- [Hindsight on GitHub](https://github.com/vectorize-io/hindsight)
- [Hindsight documentation](https://hindsight.vectorize.io/)
- [Hindsight Cloud](https://ui.hindsight.vectorize.io)
- [Vectorize: what is agent memory](https://vectorize.io/what-is-agent-memory)
