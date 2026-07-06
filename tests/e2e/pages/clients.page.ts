import type { Page } from "@playwright/test";

export class ClientsPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/clients");
  }

  clientLink(name: string) {
    return this.page.getByRole("link", { name: "View" }).first();
  }

  clientRow(name: string) {
    return this.page.getByText(name, { exact: false });
  }
}
