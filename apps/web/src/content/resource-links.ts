/** Curated resource links — add entries here to show on the authenticated Links page. */

export type ResourceLink = {
  id: string;
  title: string;
  description: string;
  href?: string;
  external?: boolean;
  repoPath?: string;
};

export type ResourceLinkGroup = {
  id: string;
  title: string;
  links: ResourceLink[];
};

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const resourceLinkGroups: ResourceLinkGroup[] = [
  {
    id: "api",
    title: "API & Documentation",
    links: [
      {
        id: "swagger",
        title: "Swagger UI (OpenAPI)",
        description: "Interactive API docs — try endpoints with your JWT.",
        href: `${apiBase}/docs`,
        external: true,
      },
      {
        id: "redoc",
        title: "ReDoc",
        description: "Readable API reference generated from OpenAPI schema.",
        href: `${apiBase}/redoc`,
        external: true,
      },
      {
        id: "openapi-json",
        title: "OpenAPI JSON",
        description: "Machine-readable schema for codegen and Postman import.",
        href: `${apiBase}/openapi.json`,
        external: true,
      },
      {
        id: "health",
        title: "API Health Check",
        description: "Liveness probe used by Docker and load balancers.",
        href: `${apiBase}/health`,
        external: true,
      },
    ],
  },
  {
    id: "observability",
    title: "Observability & Infrastructure (local dev)",
    links: [
      {
        id: "grafana",
        title: "Grafana",
        description: "Traces and dashboards (Tempo datasource).",
        href: "http://localhost:3001",
        external: true,
      },
      {
        id: "n8n",
        title: "n8n Workflow Editor",
        description: "Visual workflow UI — import JSON from n8n/workflows/ or use make n8n-import.",
        href: "http://localhost:5679",
        external: true,
      },
      {
        id: "rabbitmq",
        title: "RabbitMQ Management",
        description: "Queue depth, Celery broker monitoring — guest/guest.",
        href: "http://localhost:15672",
        external: true,
      },
      {
        id: "minio",
        title: "MinIO Console",
        description: "S3 object browser for uploaded documents.",
        href: "http://localhost:9001",
        external: true,
      },
      {
        id: "tempo",
        title: "Tempo (traces)",
        description: "Trace backend queried by Grafana.",
        href: "http://localhost:3200",
        external: true,
      },
    ],
  },
  {
    id: "demo",
    title: "Demo & Interview Materials (repository)",
    links: [
      {
        id: "demo-script",
        title: "Live Demo Script (20 min)",
        description: "Step-by-step insurance matter walkthrough for interviews.",
        repoPath: "docs/demo/DEMO_SCRIPT.md",
      },
      {
        id: "e2e-flow",
        title: "End-to-End System Flow",
        description: "Browser → audit log with every component explained.",
        repoPath: "docs/demo/E2E_FLOW.md",
      },
      {
        id: "exec-deck",
        title: "Executive Presentation",
        description: "15-slide CTO briefing with speaker notes.",
        repoPath: "docs/demo/EXECUTIVE_PRESENTATION.md",
      },
      {
        id: "interview-questions",
        title: "100 Interview Q&A",
        description: "Principal engineer questions with senior-level answers.",
        repoPath: "docs/interview/QUESTIONS.md",
      },
      {
        id: "runbook",
        title: "Operations Runbook",
        description: "Incidents, backup, deploy, and rollback procedures.",
        repoPath: "docs/operations/RUNBOOK.md",
      },
    ],
  },
  {
    id: "app",
    title: "Application",
    links: [
      {
        id: "marketing",
        title: "Public Landing Page",
        description: "Marketing site, privacy policy, and terms.",
        href: "/",
      },
      {
        id: "cases",
        title: "Cases",
        description: "Matter list and case management.",
        href: "/cases",
      },
      {
        id: "clients",
        title: "Clients",
        description: "Client directory and linked matters.",
        href: "/clients",
      },
      {
        id: "audit",
        title: "Audit Log",
        description: "Compliance audit trail (Managing Partner / Admin).",
        href: "/audit",
      },
    ],
  },
];

/** Flat list of every link for search/filter on the Links page. */
export function allResourceLinks(): ResourceLink[] {
  return resourceLinkGroups.flatMap((group) => group.links);
}
