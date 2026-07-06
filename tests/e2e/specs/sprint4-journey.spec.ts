import { expect, test } from "../fixtures/case.fixture";
import { AIPage } from "../pages/ai.page";
import { DocumentsPage } from "../pages/documents.page";
import { WorkflowsPage } from "../pages/workflows.page";

/**
 * End-to-end Sprint 4 journey: upload → OCR → AI summary → approve → workflow.
 * Tagged @release-blocker per docs/10-testing/e2e-testing.md catalog.
 */
test.describe("Sprint 4 journey @release-blocker", () => {
  test("upload, summarize, approve, and trigger workflow", async ({ page, createCase }) => {
    test.slow();
    test.setTimeout(180_000);

    const caseId = await createCase("E2E Full Sprint 4 Journey");
    const documents = new DocumentsPage(page);
    const ai = new AIPage(page);
    const workflows = new WorkflowsPage(page);

    await documents.goto(caseId);
    await documents.uploadSampleDocument();
    await expect(documents.uploadSuccessMessage()).toBeVisible();
    await expect(documents.list()).toContainText(/ready/i, { timeout: 90_000 });

    await ai.goto(caseId);
    await ai.requestSummary();
    await expect(ai.summariesList()).toContainText("draft", { timeout: 90_000 });
    await ai.approveButton().click();
    await expect(ai.summariesList()).toContainText("approved");

    await workflows.goto(caseId);
    await workflows.triggerDocumentNotify();
    await expect(workflows.executionsList()).toContainText(/completed|queued|running/i, {
      timeout: 30_000,
    });
  });
});
