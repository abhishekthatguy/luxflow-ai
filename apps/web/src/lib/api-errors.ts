type ProblemBody = {
  detail?: string;
  title?: string;
  status?: number;
  errors?: Array<{ field?: string; message?: string }>;
};

const FIELD_LABELS: Record<string, string> = {
  "body.email": "Email",
  "body.password": "Password",
};

function friendlyValidationMessage(field: string, message: string): string {
  if (field.includes("email") && message.toLowerCase().includes("email")) {
    if (message.includes(".local") || message.includes("reserved")) {
      return "Use a dev seed email like jane@example.com — @lexflow.local is not accepted.";
    }
    return `Email is invalid. Try jane@example.com (dev seed).`;
  }
  if (field.includes("password") && message.includes("at least")) {
    return "Password must be at least 8 characters.";
  }
  const label = FIELD_LABELS[field] ?? field.replace(/^body\./, "");
  return `${label}: ${message}`;
}

/** Parse RFC 7807 problem+json (or FastAPI validation) into user-facing text. */
export function formatApiError(body: unknown, fallback = "Request failed"): string {
  if (!body || typeof body !== "object") return fallback;
  const problem = body as ProblemBody;

  if (problem.errors?.length) {
    return problem.errors
      .map((e) => friendlyValidationMessage(e.field ?? "field", e.message ?? "invalid"))
      .join(" ");
  }

  if (problem.detail) {
    if (problem.detail === "One or more fields failed validation.") {
      return "Check your email and password format.";
    }
    return problem.detail;
  }

  if (problem.title && problem.status) {
    return `${problem.title} (${problem.status})`;
  }

  return fallback;
}

export function devEmailHint(email: string): string | null {
  const normalized = email.trim().toLowerCase();
  if (normalized.endsWith(".local")) {
    return "Dev accounts use @example.com — try jane@example.com with password password123.";
  }
  if (normalized === "jane@lexflow.local") {
    return "jane@lexflow.local was renamed to jane@example.com in seed data.";
  }
  return null;
}
