# LexFlow n8n Workflows

n8n runs **internally** on Docker network `http://n8n:5678`. The editor is exposed locally at **http://localhost:5679**.

## Quick start

```bash
make dev
make n8n-build          # JSON + docs from catalog
make n8n-import         # purge duplicates → import → activate
make seed-workflows     # PostgreSQL definitions
```

## Workflow groups

| Group | Folder | Purpose |
|-------|--------|---------|
| **Business** | `workflows/business/` | Case, document, AI lifecycle |
| **Notifications** | `workflows/notifications/` | Escalations & reminders |
| **Reports** | `workflows/reports/` | Scheduled partner digests |
| **Infrastructure** | `workflows/infra/` | Platform health monitoring |
| **Test** | `workflows/test/` | CI smoke (manual only) |

See [workflows/README.md](./workflows/README.md) (auto-generated) and [docs/06-workflows/workflow-groups.md](../docs/06-workflows/workflow-groups.md).

## Documentation

| Doc | Description |
|-----|-------------|
| [workflow-groups.md](../docs/06-workflows/workflow-groups.md) | What each group and workflow does |
| [workflow-technical-reference.md](../docs/06-workflows/workflow-technical-reference.md) | Webhooks, payloads, callbacks, cron |
| [admin-notification-emails.md](../docs/14-playbooks/admin-notification-emails.md) | Admin alert recipients |

Regenerate docs: `python3 scripts/n8n/build_workflows.py`

## Admin alerts

Operational workflows notify admins via `POST /internal/notifications/admin`. Configure `config/admin-notification-emails.txt` or `ADMIN_NOTIFICATION_EMAILS` in `.env`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Duplicate workflows in n8n | `make n8n-import` |
| Webhook 404 | `make n8n-import` then wait ~15s |
| Empty LexFlow catalog | `make seed-workflows` |
