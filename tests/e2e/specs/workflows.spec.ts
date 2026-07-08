import { expect, test } from "../fixtures/case.fixture";
import { WorkflowsPage } from "../pages/workflows.page";

test.describe("Sprint 4 — Workflows", () => {
  test("manually triggers document upload pipeline", async ({ page, createCase }) => {
    test.slow();
    const caseId = await createCase("E2E Workflow Trigger");
    const workflows = new WorkflowsPage(page);

    await workflows.goto(caseId);
    await workflows.triggerDocumentNotify();

    await expect(workflows.executionsList()).not.toContainText(
      "No workflow executions yet.",
    );
    await expect(workflows.executionsList()).toContainText(/queued|running|completed/i, {
      timeout: 30_000,
    });
  });

  test("case nav includes workflows tab", async ({ page, createCase }) => {
    const caseId = await createCase("E2E Workflow Nav");
    await page.goto(`/cases/${caseId}/overview`);
    await page.getByRole("link", { name: "Workflows" }).click();
    await expect(page).toHaveURL(new RegExp(`/cases/${caseId}/workflows$`));
    await expect(page.getByRole("heading", { name: "Workflows", level: 1 })).toBeVisible({
      timeout: 30_000,
    });
  });
});
