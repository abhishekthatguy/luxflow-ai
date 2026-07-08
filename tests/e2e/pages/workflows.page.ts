import type { Page } from "@playwright/test";

export class WorkflowsPage {
  constructor(private readonly page: Page) {}

  async goto(caseId: string) {
    await this.page.goto(`/cases/${caseId}/workflows`);
    await this.page.getByRole("heading", { name: "Workflows", level: 1 }).waitFor();
  }

  executionsList() {
    return this.page.getByTestId("workflow-executions");
  }

  triggerButton() {
    return this.page
      .getByTestId("wf-card-document-upload-v1")
      .getByRole("button", { name: "Trigger", exact: true });
  }

  async triggerDocumentNotify() {
    await this.triggerButton().click();
  }
}
