"""
Synthetic historical incidents used to seed the agent's memory.

Each incident represents a resolved production issue with a known
root cause and fix. This is what the agent 'remembers' and recalls
when a similar new incident comes in.

Feel free to edit/extend these to match a service/stack you want to
demo (they're written generically so they work for most SaaS backends).
"""

PAST_INCIDENTS = [
    {
        "id": "INC-1042",
        "title": "Checkout service 502s under peak load",
        "service": "checkout-api",
        "severity": "SEV1",
        "symptoms": (
            "Checkout API started returning 502 Bad Gateway for ~12% of "
            "requests starting at 14:03 UTC. Correlated with a spike in "
            "traffic from a marketing email blast. p99 latency on "
            "/checkout/create jumped from 300ms to 9s before failures began."
        ),
        "root_cause": (
            "Connection pool to Postgres (checkout-db) was capped at 20 "
            "connections in the pgbouncer config. Under the traffic spike, "
            "requests queued waiting for a connection and hit the upstream "
            "gateway timeout of 5s, producing 502s."
        ),
        "resolution": (
            "Increased pgbouncer max_client_conn from 20 to 100 and enabled "
            "transaction pooling mode. Added a CloudWatch alarm on "
            "pgbouncer connection wait time > 500ms."
        ),
        "runbook": "runbooks/checkout-db-connection-exhaustion.md",
        "timestamp": "2026-06-14T14:03:00Z",
    },
    {
        "id": "INC-1058",
        "title": "Auth tokens rejected after cert rotation",
        "service": "auth-service",
        "severity": "SEV1",
        "symptoms": (
            "Users began seeing 'invalid token' errors on login starting "
            "right after a scheduled deploy. Error rate on /auth/verify "
            "went from 0.1% to 38% within 3 minutes of deploy completion."
        ),
        "root_cause": (
            "The JWT signing key was rotated as part of the deploy, but the "
            "API gateway's JWKS cache had a 15-minute TTL and was still "
            "serving the old public key, so new tokens signed with the new "
            "key failed verification at the gateway."
        ),
        "resolution": (
            "Manually invalidated the gateway's JWKS cache post-deploy. "
            "Added a deploy-pipeline step that forces a JWKS cache purge "
            "immediately after any key rotation."
        ),
        "runbook": "runbooks/jwt-key-rotation-cache-invalidation.md",
        "timestamp": "2026-06-22T09:41:00Z",
    },
    {
        "id": "INC-1071",
        "title": "Order webhook delivery backlog",
        "service": "notifications-worker",
        "severity": "SEV2",
        "symptoms": (
            "Customers reported not receiving order-confirmation webhooks "
            "for up to 40 minutes. Queue depth on the 'webhook-delivery' "
            "SQS queue grew from ~200 to 48,000 messages over 2 hours."
        ),
        "root_cause": (
            "A downstream customer endpoint (one specific merchant) started "
            "timing out on every webhook call. Because retries were "
            "synchronous and blocking within the worker loop, that single "
            "slow consumer starved the shared worker pool for everyone."
        ),
        "resolution": (
            "Added per-destination timeout + circuit breaker so one slow "
            "consumer can't block the shared pool. Moved retries to a "
            "separate delayed-retry queue instead of blocking in-line."
        ),
        "runbook": "runbooks/webhook-worker-starvation.md",
        "timestamp": "2026-07-02T11:15:00Z",
    },
    {
        "id": "INC-1089",
        "title": "Search results empty after index deploy",
        "service": "search-api",
        "severity": "SEV2",
        "symptoms": (
            "Product search returned zero results for all queries "
            "immediately after an Elasticsearch index schema change was "
            "deployed. No errors in application logs, just empty result sets."
        ),
        "root_cause": (
            "The new index alias was created but the write alias hadn't "
            "been repointed, so all new documents were being indexed into "
            "the new index while reads still pointed at the old, now-empty "
            "one after a routine reindex cleanup deleted it."
        ),
        "resolution": (
            "Repointed the read alias to the correct index and added an "
            "automated check in the deploy script that verifies read/write "
            "alias parity before any old index is deleted."
        ),
        "runbook": "runbooks/elasticsearch-alias-mismatch.md",
        "timestamp": "2026-07-19T16:30:00Z",
    },
    {
        "id": "INC-1103",
        "title": "Billing double-charged subscription renewals",
        "service": "billing-service",
        "severity": "SEV1",
        "symptoms": (
            "17 customers were charged twice for their monthly subscription "
            "renewal within a 5-minute window. Detected via a spike in "
            "Stripe duplicate-charge webhooks."
        ),
        "root_cause": (
            "The renewal cron job did not have a distributed lock. A "
            "deploy caused two instances of the billing worker to run "
            "simultaneously for about 6 minutes, and both processed the "
            "same batch of renewals."
        ),
        "resolution": (
            "Added a Redis-based distributed lock (SET NX with TTL) around "
            "the renewal batch job. Issued refunds for the 17 affected "
            "customers within the hour."
        ),
        "runbook": "runbooks/billing-cron-double-run.md",
        "timestamp": "2026-08-03T03:12:00Z",
    },
    {
        "id": "INC-1117",
        "title": "API latency spike traced to noisy neighbor pod",
        "service": "checkout-api",
        "severity": "SEV3",
        "symptoms": (
            "p95 latency on checkout-api crept up from 200ms to 1.4s over "
            "45 minutes with no corresponding traffic increase. CPU on the "
            "node looked normal in aggregate."
        ),
        "root_cause": (
            "A batch reporting job with no CPU limits was scheduled onto "
            "the same node and was consuming most of the node's CPU in "
            "bursts, throttling checkout-api pods via cgroup CPU throttling "
            "even though 'requests' were within limits."
        ),
        "resolution": (
            "Set explicit CPU limits on the batch reporting job and added a "
            "node anti-affinity rule so batch workloads don't share nodes "
            "with latency-sensitive services."
        ),
        "runbook": "runbooks/noisy-neighbor-cpu-throttling.md",
        "timestamp": "2026-08-21T10:05:00Z",
    },
]
