# Staging ECS — Terraform stubs (Sprint 1 LEX-110)

Terraform modules for staging deploy land in Sprint 1 Phase 2 follow-up.

Planned resources:
- ECR repositories: `lexflow-api`, `lexflow-web`
- ECS Fargate services behind ALB
- `/health` target group checks

See `docs/09-deployment/terraform.md` and `docs/14-playbooks/deploy-production.md`.

**Status:** Stub — wire CI deploy job when AWS credentials and remote state are configured.
