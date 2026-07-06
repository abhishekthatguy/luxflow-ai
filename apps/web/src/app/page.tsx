import { ApiHealthResponse, isApiHealthy } from "@lexflow/shared";
import { Button } from "@lexflow/ui";

async function fetchHealth(): Promise<{ data: ApiHealthResponse | null; error: string | null }> {
  const base =
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  try {
    const res = await fetch(`${base}/health`, { cache: "no-store" });
    if (!res.ok) {
      return { data: null, error: `API returned ${res.status}` };
    }
    const data = (await res.json()) as ApiHealthResponse;
    return { data, error: null };
  } catch {
    return { data: null, error: "Cannot reach API — is `make dev` running?" };
  }
}

export default async function HomePage() {
  const { data, error } = await fetchHealth();
  const healthy = data !== null && isApiHealthy(data);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">LexFlow AI</h1>
        <p className="mt-2 text-slate-600">Development environment — no business code yet</p>
      </div>

      <div
        className={`w-full rounded-lg border p-6 ${
          healthy ? "border-green-200 bg-green-50" : "border-amber-200 bg-amber-50"
        }`}
      >
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">API health</p>
        {healthy && data ? (
          <p className="mt-2 text-lg text-green-800">
            Connected — {data.service} status: {data.status}
          </p>
        ) : (
          <p className="mt-2 text-lg text-amber-800">{error ?? "API unhealthy"}</p>
        )}
      </div>

      <Button variant="secondary">Scaffold ready for Sprint 1 Phase 2</Button>

      <p className="text-xs text-slate-400">
        Quickstart: <code className="rounded bg-slate-100 px-1">make setup && make dev</code>
      </p>
    </main>
  );
}
