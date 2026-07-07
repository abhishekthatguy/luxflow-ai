# Admin notification emails

LexFlow sends operational alerts (health failures, escalations, daily reports, AI failures) to a configurable list of admin email addresses.

## Default recipient

`abhishekthatguy@gmail.com` is pre-configured for local development.

## How to add more admins

Choose **one** of these methods (env var wins over file if both are set).

### Option A — `.env` (recommended for Docker)

Add or edit in your project `.env`:

```bash
ADMIN_NOTIFICATION_EMAILS=abhishekthatguy@gmail.com,you@firm.com,ops@firm.com
```

Restart the API:

```bash
docker compose restart api
```

### Option B — config file

Edit `config/admin-notification-emails.txt` — **one email per line**:

```text
# Platform admins — operational alerts
abhishekthatguy@gmail.com
you@firm.com
ops@firm.com
```

Lines starting with `#` are ignored. Restart API after changes:

```bash
docker compose restart api
```

## Which workflows send admin alerts?

These n8n workflows call `POST /internal/notifications/admin`:

| Workflow | Steps that email admins |
|----------|-------------------------|
| Operations Health Monitor | Create Incident, Notify Ops |
| Daily Partner Report | Email Partner, Teams Notification |
| Approval Escalation | Reminder, Escalate to Partner |
| AI Failure Recovery | Notify Attorney |

## Verify delivery

When `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set in `.env`, LexFlow sends via **Gmail SMTP** (`smtp.gmail.com:587`). Otherwise emails are logged only.

```bash
docker compose logs api worker | grep -E 'EMAIL_SENT|EMAIL_FAILED|ADMIN_NOTIFICATION'
```

### Gmail app password

1. Google Account → **Security** → enable **2-Step Verification**
2. **App passwords** → create one for "Mail" / "LexFlow"
3. Add to `.env`:

```bash
GMAIL_USER=clawtbot@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
```

Restart API and worker:

```bash
docker compose restart api worker
```

Example log line:

```text
ADMIN_NOTIFICATION email=abhishekthatguy@gmail.com subject=[LexFlow] Operations Health Monitor — Notify Ops ...
```

### Manual test

```bash
curl -X POST http://localhost:8000/internal/notifications/admin \
  -H 'Content-Type: application/json' \
  -d '{"subject":"Test alert","body":"Hello from LexFlow","source":"manual"}'
```

## Production (AWS SES)

1. Set `ADMIN_NOTIFICATION_EMAILS` in Secrets Manager / ECS task env.
2. Wire `AdminNotificationService._dispatch_email` to AWS SES (see `docs/08-security/secrets-management.md`).
3. Verify sender domain in SES before go-live.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No logs / `sent: 0` | Check `ADMIN_NOTIFICATION_EMAILS` or `config/admin-notification-emails.txt` |
| n8n step fails on Notify Ops | Ensure API container is reachable at `http://api:8000` on Docker network |
| Duplicate n8n workflows | Run `make n8n-import` — purges managed workflows before re-import |
