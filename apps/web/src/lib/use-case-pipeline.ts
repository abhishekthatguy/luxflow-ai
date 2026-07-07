"use client";

import type { PipelineStage } from "@/components/pipeline-steps";
import { apiFetch } from "@/lib/auth";
import { useCallback, useEffect, useState } from "react";

type PipelineResponse = {
  caseId: string;
  stages: PipelineStage[];
  currentStage?: string | null;
};

export function useCasePipeline(caseId: string | undefined) {
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    if (!caseId) return;
    apiFetch<PipelineResponse>(`/api/v1/operations/cases/${caseId}/pipeline`)
      .then((d) => {
        setStages(d.stages);
        setCurrentStage(d.currentStage ?? null);
      })
      .catch(() => setStages([]))
      .finally(() => setLoading(false));
  }, [caseId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  return { stages, currentStage, loading, reload: load };
}
