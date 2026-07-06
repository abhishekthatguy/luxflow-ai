import Link from "next/link";

const LINKS = [
  { suffix: "overview", label: "Overview" },
  { suffix: "documents", label: "Documents" },
  { suffix: "ai", label: "AI" },
  { suffix: "workflows", label: "Workflows" },
  { suffix: "timeline", label: "Timeline" },
  { suffix: "tasks", label: "Tasks" },
] as const;

export function CaseNav({ caseId, active }: { caseId: string; active: string }) {
  return (
    <nav className="flex flex-wrap gap-2 text-sm">
      {LINKS.map((link) => (
        <Link
          key={link.suffix}
          href={`/cases/${caseId}/${link.suffix}`}
          className={
            active === link.suffix
              ? "font-medium text-slate-900"
              : "text-blue-700 hover:underline"
          }
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
