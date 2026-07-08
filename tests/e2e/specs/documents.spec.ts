import { expect, test } from "../fixtures/case.fixture";
import { DocumentsPage } from "../pages/documents.page";

test.describe("Sprint 4 — Documents", () => {
  test("uploads a document and reaches ready status", async ({ page, createCase }) => {
    test.slow();
    const caseId = await createCase("E2E Document Upload");
    const documents = new DocumentsPage(page);

    await documents.goto(caseId);
    await documents.uploadSampleDocument();

    await expect(documents.uploadSuccessMessage()).toBeVisible();
    await expect(documents.list()).toContainText("sample-document.txt");
    await expect(documents.list()).toContainText(/ready/i, { timeout: 180_000 });
    await expect(documents.list()).toContainText(/OCR: Complete/i, { timeout: 180_000 });
  });

  test("case nav includes documents tab", async ({ page, createCase }) => {
    const caseId = await createCase("E2E Nav Check");
    await page.goto(`/cases/${caseId}/overview`);
    await page.getByRole("link", { name: "Documents" }).click();
    await expect(page).toHaveURL(new RegExp(`/cases/${caseId}/documents$`));
    await expect(page.getByRole("heading", { name: "Documents" })).toBeVisible();
  });
});
