type DocStatus = {
  status: string;
  ocrStatus: string;
};

const STATUS_LABELS: Record<string, string> = {
  pending_upload: "Awaiting upload",
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
  pending: "Queued",
  completed: "Complete",
  skipped: "Skipped",
};

const STATUS_COLORS: Record<string, string> = {
  ready: "bg-green-100 text-green-800",
  completed: "bg-green-100 text-green-800",
  processing: "bg-blue-100 text-blue-800",
  pending: "bg-amber-100 text-amber-800",
  uploaded: "bg-slate-100 text-slate-700",
  failed: "bg-red-100 text-red-800",
  skipped: "bg-slate-100 text-slate-500",
};

function label(value: string): string {
  return STATUS_LABELS[value] ?? value.replace(/_/g, " ");
}

export function DocumentStatusBadge({ status, ocrStatus }: DocStatus) {
  const docColor = STATUS_COLORS[status] ?? "bg-slate-100 text-slate-700";
  const ocrColor = STATUS_COLORS[ocrStatus] ?? "bg-slate-100 text-slate-700";
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${docColor}`}>
        {label(status)}
      </span>
      <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${ocrColor}`}>
        OCR: {label(ocrStatus)}
      </span>
    </div>
  );
}
