/** Makefile & npm commands — run from repository root unless noted. */

export type RepoCommand = {
  id: string;
  command: string;
  description: string;
  notes?: string;
};

export type RepoCommandGroup = {
  id: string;
  title: string;
  description?: string;
  commands: RepoCommand[];
};

export const repoCommandGroups: RepoCommandGroup[] = [
  {
    id: "getting-started",
    title: "Getting started",
    description: "First-time setup and daily stack control.",
    commands: [
      {
        id: "setup",
        command: "make setup",
        description: "Install deps, chmod scripts, initial project setup.",
      },
      {
        id: "dev",
        command: "make dev",
        description: "Start full Docker stack (API, web, Postgres, Redis, RabbitMQ, MinIO, n8n, Grafana).",
        notes: "Same as make dev-full",
      },
      {
        id: "down",
        command: "make down",
        description: "Stop all Docker Compose services.",
      },
      {
        id: "ps",
        command: "make ps",
        description: "Show running container status.",
      },
      {
        id: "logs",
        command: "make logs",
        description: "Tail logs from all services (Ctrl+C to exit).",
      },
    ],
  },
  {
    id: "database",
    title: "Database & seed data",
    description: "Migrations and dev fixtures — stack must be running.",
    commands: [
      {
        id: "migrate",
        command: "make migrate",
        description: "Apply Alembic migrations (upgrade head).",
      },
      {
        id: "migrate-down",
        command: "make migrate-down",
        description: "Rollback one migration revision.",
      },
      {
        id: "seed",
        command: "make seed",
        description: "Seed dev firm, users (jane/john/alex), and Acme client.",
      },
      {
        id: "seed-sprint4",
        command: "make seed-sprint4",
        description: "Seed AI prompt template and n8n workflow definition.",
      },
      {
        id: "seed-sprint5",
        command: "make seed-sprint5",
        description: "Add partner@example.com (ManagingPartner) for audit UI.",
      },
    ],
  },
  {
    id: "quality",
    title: "Lint & unit tests",
    commands: [
      {
        id: "lint",
        command: "make lint",
        description: "Run ruff + mypy (API) and next lint (web).",
      },
      {
        id: "test",
        command: "make test",
        description: "Run pytest (API) and vitest (web).",
      },
      {
        id: "npm-lint",
        command: "npm run lint",
        description: "Lint all npm workspaces from repo root.",
      },
      {
        id: "npm-test",
        command: "npm run test",
        description: "Test all npm workspaces from repo root.",
      },
      {
        id: "npm-build",
        command: "npm run build",
        description: "Production build for all npm workspaces.",
      },
    ],
  },
  {
    id: "verify",
    title: "Verification & smoke tests",
    description: "Run from repo root with stack up (make dev).",
    commands: [
      {
        id: "verify-platform",
        command: "make verify-platform",
        description: "Full platform gate: health, logging, traces, integration, n8n callback.",
      },
      {
        id: "verify-quickstart",
        command: "make verify-quickstart",
        description: "Quickstart readiness check.",
      },
      {
        id: "verify-health",
        command: "make verify-health",
        description: "API and service health endpoints.",
      },
      {
        id: "verify-integration",
        command: "make verify-integration",
        description: "Redis, RabbitMQ, Celery, MinIO integration smoke.",
      },
      {
        id: "verify-sprint3",
        command: "make verify-sprint3",
        description: "Sprint 3: auth + cases unit tests + live API smoke.",
      },
      {
        id: "verify-sprint4",
        command: "make verify-sprint4",
        description: "Sprint 4: documents, AI, workflows + strict smoke + Playwright E2E.",
        notes: "Long-running — includes test-e2e",
      },
      {
        id: "verify-sprint5",
        command: "make verify-sprint5",
        description: "Sprint 5: audit API, notifications, auth rate limit smoke.",
      },
    ],
  },
  {
    id: "e2e",
    title: "Playwright E2E",
    commands: [
      {
        id: "test-e2e",
        command: "make test-e2e",
        description: "Run browser E2E tests against localhost:3000 + :8000.",
        notes: "Requires make dev && make seed",
      },
      {
        id: "npm-test-e2e",
        command: "npm run test:e2e",
        description: "Playwright test run (same as make test-e2e without browser install step).",
      },
      {
        id: "npm-test-e2e-ui",
        command: "npm run test:e2e:ui",
        description: "Open Playwright UI mode for debugging tests.",
      },
      {
        id: "npm-test-e2e-report",
        command: "npm run test:e2e:report",
        description: "Open last Playwright HTML report.",
      },
    ],
  },
  {
    id: "integrations",
    title: "Integrations & ops",
    commands: [
      {
        id: "n8n-import",
        command: "make n8n-import",
        description: "Import workflow JSON from n8n/workflows/ into local n8n.",
        notes: "No API key needed locally — uses Docker CLI import. N8N_API_KEY only if you run scripts/n8n/import-workflows.py against a secured n8n.",
      },
      {
        id: "docker-rebuild-web",
        command: "docker compose up -d --build web",
        description: "Rebuild and restart Next.js after frontend-only Docker changes.",
      },
      {
        id: "docker-rebuild-api",
        command: "docker compose up -d --build api",
        description: "Rebuild and restart FastAPI after backend changes.",
      },
      {
        id: "k6-load",
        command: "k6 run tests/load/cases-read.js",
        description: "Load test case list/read — 100 VUs, p95 < 500ms target.",
        notes: "Install first: brew install grafana/k6/k6. Stack must be running (make dev + seed).",
      },
    ],
  },
  {
    id: "typical-flow",
    title: "Typical dev flow (copy all)",
    description: "Common sequence after cloning the repo.",
    commands: [
      {
        id: "flow-1",
        command: "cp .env.example .env && make setup && make dev",
        description: "Configure env, setup, start stack.",
      },
      {
        id: "flow-2",
        command: "make migrate && make seed && make seed-sprint4 && make seed-sprint5",
        description: "Migrate DB and load all seed data.",
      },
      {
        id: "flow-3",
        command: "make verify-sprint5",
        description: "Confirm Sprint 5 smoke passes.",
      },
    ],
  },
];

export function allRepoCommands(): RepoCommand[] {
  return repoCommandGroups.flatMap((group) => group.commands);
}

export function totalMyToolsItems(linkCount: number): number {
  return linkCount + allRepoCommands().length;
}
