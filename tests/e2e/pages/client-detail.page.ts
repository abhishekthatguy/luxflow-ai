import type { Page } from "@playwright/test";

export class ClientDetailPage {
  constructor(private readonly page: Page) {}

  detail() {
    return this.page.getByTestId("client-detail");
  }

  notFound() {
    return this.page.getByTestId("client-not-found");
  }

  loading() {
    return this.page.getByTestId("client-detail-loading");
  }

  casesList() {
    return this.page.getByTestId("client-cases-list");
  }

  casesEmpty() {
    return this.page.getByTestId("client-cases-empty");
  }
}
