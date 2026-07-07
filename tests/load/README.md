# Load testing (Sprint 5 — LEX-507)

Baseline k6 scripts for API throughput and latency thresholds.

## Prerequisites

- [k6](https://k6.io/docs/get-started/installation/) installed locally

**macOS (Homebrew):**

```bash
brew install grafana/k6/k6
```

**Verify:** `k6 version`
- LexFlow stack running (`make dev && make migrate && make seed`)

## Cases list/read

```bash
k6 run tests/load/cases-read.js
```

Environment overrides:

| Variable | Default |
|----------|---------|
| `API_URL` | `http://localhost:8000` |
| `LOAD_TEST_EMAIL` | `jane@example.com` |
| `LOAD_TEST_PASSWORD` | `password123` |

Thresholds (per sprint plan): p95 &lt; 500ms, error rate &lt; 1%.
