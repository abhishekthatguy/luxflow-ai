## Summary

<!-- What changed and WHY (not just what). Link to issue. -->

Closes #

## Type of Change

- [ ] Feature
- [ ] Bug fix
- [ ] Tech debt
- [ ] Documentation
- [ ] Infrastructure / CI
- [ ] Security

## Bounded Context

<!-- Which services/{context}/ owns this change? -->

## Changes

<!-- 1-3 bullets describing the behavioral change -->

-
-
-

## Security Impact

- [ ] No security impact
- [ ] Touches authentication / authorization
- [ ] Touches matter walls (case-scoped access)
- [ ] Touches PII or AI outputs
- [ ] Security review completed

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Matter wall tests pass (required if auth touched)
- [ ] E2E tests added/updated (or follow-up issue: #)
- [ ] Tested locally (`make lint && make test`)

### Test Evidence

<!-- Paste CI run link or describe manual test steps -->

## Database

- [ ] No schema change
- [ ] Alembic migration included (upgrade + downgrade tested)
- [ ] Schema docs updated (`docs/05-database/`)

## API

- [ ] No API change
- [ ] OpenAPI spec updated
- [ ] SDK/types regenerated
- [ ] API docs updated (`docs/04-api/`)

## n8n Workflow

- [ ] No workflow change
- [ ] Workflow JSON committed (`n8n/workflows/`)
- [ ] JSON schemas committed (`n8n/schemas/`)
- [ ] Catalog updated (`docs/06-workflows/workflow-catalog.md`)
- [ ] No business logic in n8n (ADR-002)

## AI

- [ ] No AI change
- [ ] Async processing (202 Accepted — ADR-004)
- [ ] PII redaction before LLM
- [ ] HITL gate for legal outputs
- [ ] Prompt versioned in registry

## Documentation

- [ ] No docs change needed
- [ ] Docs updated in same PR
- [ ] ADR created (if significant architectural decision): ADR-___

## Deployment Notes

<!-- Feature flags, migration order, rollback plan, env vars -->

- [ ] Backward compatible
- [ ] Requires new environment variables (documented in `.env.example`)
- [ ] Rollback plan documented

## Checklist

- [ ] PR explains **why**, not just what
- [ ] No secrets in code or commits
- [ ] PR size < 500 lines (or justified)
- [ ] Follows [development standards](../../docs/development-standards.md)
- [ ] [Definition of Done](../handbook/definition-of-done.md) met

## Screenshots / Recordings

<!-- If UI change, add before/after screenshots -->

## Reviewer Notes

<!-- Anything specific reviewers should focus on -->
