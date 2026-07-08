import { expect, test } from "../fixtures/case.fixture";
import { AIPage } from "../pages/ai.page";

test.describe("Sprint 4 — AI summaries", () => {
  test("generates draft summary and approves it", async ({ page, createCase }) => {
    test.slow();
    test.setTimeout(360_000);

    const caseId = await createCase("E2E AI Summary");
    const ai = new AIPage(page);
    await ai.goto(caseId);

    await expect(ai.disclaimer()).toBeVisible();
    await ai.requestSummary();

    await expect(ai.summariesList()).toContainText("draft", { timeout: 300_000 });
    await expect(ai.summariesList()).toContainText(/AI Draft Summary/i);

    await ai.approveButton().click();
    await expect(ai.summariesList()).toContainText("approved", { timeout: 15_000 });
  });
});
