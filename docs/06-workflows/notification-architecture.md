# Notification Engine Architecture

**LexFlow AI** — enterprise workflow notifications (email, Teams, in-app)

## Flow

```
Domain Event (case created, OCR done, AI ready, workflow complete)
        ↓
NotificationEngine (FastAPI — business logic)
        ├── RecipientResolver (RBAC from DB users + env fallbacks)
        ├── EmailTemplateService (Jinja2 HTML)
        ├── In-app NotificationService
        ├── Celery: deliver_email_notification (SMTP + retry + DLQ)
        ├── Celery: deliver_teams_notification → n8n webhook → Teams Incoming Webhook
        └── Celery: deliver_slack_notification → n8n webhook → Slack Bot API / Incoming Webhook
        ↓
Audit log + notification_deliveries table (correlation_id, latency, attempts)
```

## Principles

- **Business logic stays in FastAPI** — templates, RBAC routing, context building
- **n8n orchestrates Teams and Slack delivery** — pre-built payloads posted via channel webhooks/API
- **No hardcoded emails** — recipients resolved from DB users by role; env vars are fallbacks for seed/dev

## Configuration

| Variable | Purpose |
|----------|---------|
| `MAIL_FROM_NAME` | Display name for sender |
| `MAIL_FROM_ADDRESS` | From address (defaults to `GMAIL_USER`) |
| `GMAIL_USER` / `GMAIL_APP_PASSWORD` | SMTP transport |
| `MANAGING_PARTNER_EMAIL` | Seed/fallback for ManagingPartner role |
| `ATTORNEY_EMAIL` | Seed/fallback for Attorney role |
| `ASSOCIATE_EMAIL` | Seed/fallback for Associate role |
| `TEAMS_WEBHOOK_URL` | Teams Incoming Webhook (production) |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token (`chat:write`) — forwarded to n8n |
| `SLACK_TEAM_CHANNEL_ID` | Slack channel for team follow-ups (default `C0BF67RKS3Z`) |
| `SLACK_WEBHOOK_URL` | Optional Slack Incoming Webhook (alternative to bot token) |
| `NOTIFICATION_WEB_BASE_URL` | Portal base for CTA links |

## Seed notification users

```bash
make seed-notification-users
```

Reads emails from env and creates/updates RBAC users in `lexflow-dev` firm.

## Verify

```bash
make verify-notifications
```

## n8n workflows

| Slug | Purpose |
|------|---------|
| `notification-teams-v1` | POST Adaptive Card to Teams webhook |
| `notification-slack-v1` | POST Block Kit message to Slack (bot token or webhook) |
| `approval-escalation-v1` | Scheduled approval reminders (calls internal admin API) |

## Templates

Located at `apps/api/templates/emails/` — all extend `base.html` with responsive inline CSS for Outlook.
