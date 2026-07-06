import type { Page } from "@playwright/test";

export class AIPage {
  constructor(private readonly page: Page) {}

  async goto(caseId: string) {
    await this.page.goto(`/cases/${caseId}/ai`);
    await this.page.getByRole("heading", { name: "AI Summaries" }).waitFor();
  }

  summariesList() {
    return this.page.getByTestId("ai-summaries-list");
  }

  requestSummaryButton() {
    return this.page.getByRole("button", { name: "Request case summary" });
  }

  async requestSummary() {
    await this.requestSummaryButton().click();
  }

  draftSummary() {
    return this.summariesList().getByText("draft", { exact: true });
  }

  approveButton() {
    return this.page.getByRole("button", { name: "Approve" });
  }

  disclaimer() {
    return this.page.getByText(/attorney approval/i);
  }
}
