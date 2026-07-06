# Documentation Migration Guide

**Status:** Legacy flat docs superseded by numbered folders (2026-07-06)

The original flat documentation files at `docs/` root have been reorganized into 15 numbered folders. Use this guide to find the canonical location for any topic.

---

## Mapping: Legacy → Canonical

| Legacy File | Canonical Location |
|-------------|-------------------|
| `product-overview.md` | [01-product/vision.md](./01-product/vision.md) + [01-product/capabilities.md](./01-product/capabilities.md) |
| `domain-model.md` | [02-domain/](./02-domain/README.md) (all aggregate docs) |
| `high-level-architecture.md` | [03-architecture/](./03-architecture/README.md) |
| `folder-structure.md` | [14-playbooks/local-dev-setup.md](./14-playbooks/local-dev-setup.md) + [03-architecture/component-architecture.md](./03-architecture/component-architecture.md) |
| `database-architecture.md` | [05-database/](./05-database/README.md) |
| `api-architecture.md` | [04-api/](./04-api/README.md) |
| `authentication-authorization.md` | [04-api/authentication.md](./04-api/authentication.md) + [04-api/authorization-rbac.md](./04-api/authorization-rbac.md) |
| `security-architecture.md` | [08-security/](./08-security/README.md) |
| `workflow-orchestration.md` | [06-workflows/](./06-workflows/README.md) |
| `ai-architecture.md` | [07-ai/](./07-ai/README.md) |
| `event-driven-architecture.md` | [03-architecture/event-driven-design.md](./03-architecture/event-driven-design.md) |
| `integration-architecture.md` | [03-architecture/integration-patterns.md](./03-architecture/integration-patterns.md) |
| `deployment-architecture.md` | [09-deployment/](./09-deployment/README.md) |
| `observability.md` | [11-observability/](./11-observability/README.md) |
| `disaster-recovery.md` | [09-deployment/disaster-recovery.md](./09-deployment/disaster-recovery.md) |
| `compliance-data-governance.md` | [08-security/compliance-mapping.md](./08-security/compliance-mapping.md) |
| `testing-strategy.md` | [10-testing/](./10-testing/README.md) |
| `development-standards.md` | [14-playbooks/onboarding.md](./14-playbooks/onboarding.md) |
| `adr/` | [13-decisions/](./13-decisions/README.md) |

---

## Action for Engineers

- **New work:** Reference numbered folders only
- **Existing bookmarks:** Update using the table above
- **Legacy files:** Retained temporarily for backward compatibility; will be removed in a future cleanup PR
