# Test workflows (`n8n/workflows/test/`)

Manual-trigger only. **Do not activate** for webhook or scheduled production traffic.

| WF | File | Purpose |
|----|------|---------|
| WF-10 | `smoke-callback-v1.json` | n8n → FastAPI internal smoke endpoint |
| WF-15 | `test-slack-notification-v1.json` | Slack notification smoke via `notification-slack-v1` |

## Slack notification smoke (WF-15)

**Workflow:** `WF-15 · Slack Notification Smoke Test`  
**Test cases:** [slack-notification.test-cases.md](./slack-notification.test-cases.md)

### Run from n8n editor

1. Ensure stack is up: `docker compose up -d`
2. Import workflows: `make n8n-import`
3. Open n8n at http://localhost:5679
4. Open **WF-15 · Slack Notification Smoke Test**
5. In **Pick Test Case**, set `test_mode` (default: `client_created`)
6. Click **Execute workflow** (manual trigger)
7. Inspect **Report Result** — `pass: true` and check Slack channel `C0BF67RKS3Z`

### Prerequisites

- `notification-slack-v1` (WF-14) must be **active** (auto-activated on `make n8n-import`)
- Slack credentials in `.env` — forwarded to **api**, **worker**, and **n8n** containers:
  - `SLACK_BOT_TOKEN` + `SLACK_TEAM_CHANNEL_ID` (recommended)
  - or `SLACK_WEBHOOK_URL`

After changing `.env` Slack vars: `docker compose up -d n8n api worker`

### Routes

| `test_mode` | Calls |
|-------------|--------|
| `basic_text`, `client_created`, `case_created`, `workflow_failed`, `stub_no_credentials` | `POST http://n8n:5678/webhook/notification-slack-v1` |
| `via_fastapi` | `POST http://api:8000/internal/notifications/slack/test` (full FastAPI → Celery → n8n path) |
