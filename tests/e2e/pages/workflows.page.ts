import type { Page } from "@playwright/test";

export class WorkflowsPage {
  constructor(private readonly page: Page) {}

  async goto(caseId: string) {
    await this.page.goto(`/cases/${caseId}/workflows`);
    await this.page.getByRole("heading", { name: "Workflows" }).waitFor();
  }

  executionsList() {
    return this.page.getByTestId("workflow-executions");
  }

  triggerButton() {
    return this.page.getByRole("button", { name: /Trigger Document Upload Pipeline/i });
  }

  async triggerDocumentNotify() {
    await this.triggerButton().click();
  }
}
