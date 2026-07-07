# Slack notification — n8n editor test cases

**Workflow:** `test-slack-notification-v1` (WF-15)  
**Production path under test:** `notification-slack-v1` (WF-14)  
**Channel:** `C0BF67RKS3Z`

Edit `test_mode` in the **Pick Test Case** Code node before each run.

---

## TC-SLACK-01 — Basic text

| Field | Value |
|-------|--------|
| `test_mode` | `basic_text` |
| Route | n8n → `notification-slack-v1` |
| Expected | `Report Result.pass` = `true`, `actual` = `accepted` |
| Slack | Plain text: "LexFlow Slack smoke — basic text from n8n editor" |

**Pass criteria:** HTTP 200 from webhook; message visible in channel.

---

## TC-SLACK-02 — Client created (Block Kit)

| Field | Value |
|-------|--------|
| `test_mode` | `client_created` |
| Route | n8n → `notification-slack-v1` |
| Event | `CLIENT_CREATED` (dummy Gitlime / WF-04) |
| Expected | `pass` = `true`, `actual` = `accepted` |

**Pass criteria:** Block Kit header "New client onboarded"; fields for client name and email.

---

## TC-SLACK-03 — Case created (Block Kit)

| Field | Value |
|-------|--------|
| `test_mode` | `case_created` |
| Route | n8n → `notification-slack-v1` |
| Event | `CASE_CREATED` (dummy Smith v. Jones) |
| Expected | `pass` = `true`, `actual` = `accepted` |

**Pass criteria:** Block Kit with case title and workflow `case-intake-v1`.

---

## TC-SLACK-04 — Workflow failed (Block Kit)

| Field | Value |
|-------|--------|
| `test_mode` | `workflow_failed` |
| Route | n8n → `notification-slack-v1` |
| Event | `WORKFLOW_FAILED` (dummy OCR timeout) |
| Expected | `pass` = `true`, `actual` = `accepted` |

**Pass criteria:** Alert-style message; status field shows Failed.

---

## TC-SLACK-05 — Stub (no credentials)

| Field | Value |
|-------|--------|
| `test_mode` | `stub_no_credentials` |
| Route | n8n → `notification-slack-v1` |
| Payload | All Slack tokens/channels explicitly `null` |
| Expected | `pass` = `true`, `actual` = `stub` |

**Pass criteria:** WF-14 **Respond Stub** path; no message in Slack; no HTTP error.

---

## TC-SLACK-06 — Full stack via FastAPI

| Field | Value |
|-------|--------|
| `test_mode` | `via_fastapi` |
| Route | `POST /internal/notifications/slack/test` |
| Expected | `pass` = `true`, `actual` = `sent` |

**Pass criteria:** FastAPI builds Block Kit, calls n8n WF-14, Slack receives "LexFlow Slack test" message.

**Requires:** `api` container healthy; `SLACK_BOT_TOKEN` in `.env`.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `pass: false`, HTTP 404 | Run `make n8n-import`; confirm WF-14 active |
| `pass: false`, `actual: failed` | Bot token scopes (`chat:write`); bot invited to channel |
| `hasCredentials: false` on n8n routes | Restart n8n after `.env` change; verify `docker compose exec n8n printenv SLACK_BOT_TOKEN` |
| `via_fastapi` fails | `curl -X POST http://localhost:8000/internal/notifications/slack/test` |

## Regenerate & import

```bash
python3 scripts/n8n/build_workflows.py
make n8n-import
make seed-workflows
```
