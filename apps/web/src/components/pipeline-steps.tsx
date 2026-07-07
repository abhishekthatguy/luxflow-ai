export type PipelineStageStatus = "pending" | "active" | "completed" | "skipped";

export type PipelineStage = {
  id: string;
  label: string;
  status: PipelineStageStatus;
};

const STATUS_STYLES: Record<PipelineStageStatus, string> = {
  pending: "border-slate-200 bg-white text-slate-400",
  active: "border-blue-500 bg-blue-50 text-blue-900 ring-2 ring-blue-200",
  completed: "border-green-500 bg-green-50 text-green-900",
  skipped: "border-slate-100 bg-slate-50 text-slate-300 line-through",
};

export function PipelineSteps({
  stages,
  title = "AI Processing Timeline",
  compact = false,
  currentStage,
}: {
  stages: PipelineStage[];
  title?: string;
  compact?: boolean;
  currentStage?: string | null;
}) {
  const normalized = currentStage
    ? stages.map((stage) =>
        stage.status === "active" && stage.id !== currentStage
          ? { ...stage, status: "pending" as const }
          : stage.id === currentStage && stage.status !== "completed" && stage.status !== "skipped"
            ? { ...stage, status: "active" as const }
            : stage
      )
    : stages;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="processing-pipeline">
      {!compact && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
      <ol className={`${compact ? "mt-0" : "mt-4"} space-y-0`}>
        {normalized.map((stage, index) => (
          <li key={stage.id} className="flex flex-col items-center">
            <div
              className={`w-full rounded-md border px-3 py-2 text-center text-sm font-medium ${STATUS_STYLES[stage.status]}`}
              data-testid={`pipeline-stage-${stage.id}`}
            >
              {stage.label}
              {stage.status === "active" && (
                <span className="ml-2 text-xs font-normal text-blue-600">in progress…</span>
              )}
            </div>
            {index < normalized.length - 1 && (
              <div className="flex h-6 flex-col items-center justify-center text-slate-300" aria-hidden>
                ↓
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

export const DOCUMENT_WORKFLOW_STAGES: PipelineStage[] = [
  { id: "upload", label: "Upload", status: "completed" },
  { id: "ocr", label: "OCR", status: "completed" },
  { id: "ai", label: "AI", status: "completed" },
  { id: "approval", label: "Approval", status: "completed" },
  { id: "email", label: "Email", status: "pending" },
  { id: "archive", label: "Archive", status: "pending" },
  { id: "complete", label: "Complete", status: "pending" },
];

export function WorkflowPipelineVisual({
  stages,
  title = "Workflow pipeline",
}: {
  stages: PipelineStage[];
  title?: string;
}) {
  return <PipelineSteps stages={stages} title={title} />;
}
