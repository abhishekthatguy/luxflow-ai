import path from "path";
import type { Page } from "@playwright/test";

export class DocumentsPage {
  constructor(private readonly page: Page) {}

  async goto(caseId: string) {
    await this.page.goto(`/cases/${caseId}/documents`);
    await this.page.getByRole("heading", { name: "Documents" }).waitFor();
  }

  list() {
    return this.page.getByTestId("documents-list");
  }

  async uploadSampleDocument(fixtureName = "sample-document.txt") {
    const filePath = path.join(__dirname, "../fixtures", fixtureName);
    await this.page.locator('input[name="file"]').setInputFiles(filePath);
    await this.page.getByRole("button", { name: "Upload", exact: true }).click();
  }

  uploadSuccessMessage() {
    return this.page.getByText(/uploaded successfully.*OCR/i);
  }
}
