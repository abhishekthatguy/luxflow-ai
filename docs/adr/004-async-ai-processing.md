# ADR-004: All AI Processing via Async Worker Path

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI integrates with LLM providers (OpenAI, Azure OpenAI, Claude) for summarization, research, contract review, and chat. LLM API calls have variable latency (2–60 seconds) and can fail or rate-limit.

Exposing synchronous AI calls in the HTTP request path would cause timeout issues, poor UX (blocked UI), and inability to retry gracefully.

## Options Considered

1. **Synchronous AI in request path** — Frontend calls API, API calls LLM, waits, returns.
   - Pros: Simplest implementation
   - Cons: Timeouts, blocked UI, no retry, poor scalability

2. **Async via queue** — API accepts request (202), worker calls LLM, result stored, frontend polls/WebSocket.
   - Pros: Resilient, retryable, scalable, non-blocking UX
   - Cons: More complex (job status, polling/SSE)

3. **Streaming via SSE** — API streams LLM tokens to frontend in real-time.
   - Pros: Good UX for chat
   - Cons: Still blocks a server connection; harder to audit complete response

## Decision

All AI processing goes through the **async worker path** (RabbitMQ → Celery → LLM provider). The API returns `202 Accepted` with a job ID. The frontend polls or receives SSE updates.

For the **case-scoped chat assistant**, streaming SSE may be added in Phase 2 as an enhancement — but the full response is still persisted asynchronously for audit.

## Consequences

- **Easier:** Retry, rate limiting, cost metering, and audit logging in one path
- **Easier:** LLM provider failures don't affect API availability
- **Easier:** Horizontal scaling of AI workers independently
- **Harder:** Frontend must handle async status (polling/SSE)
- **Harder:** Slightly higher perceived latency for simple summaries
