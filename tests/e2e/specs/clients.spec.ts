import { expect, test } from "../fixtures/auth.fixture";
import { ClientDetailPage } from "../pages/client-detail.page";
import { ClientsPage } from "../pages/clients.page";

test.describe("Clients", () => {
  test.beforeEach(async ({ page, loginAsJane }) => {
    await loginAsJane();
  });

  test("lists clients and opens client detail", async ({ page }) => {
    const clients = new ClientsPage(page);
    await clients.goto();
    await expect(page.getByRole("heading", { name: "Clients" })).toBeVisible();
    await expect(clients.clientRow("Acme Corporation")).toBeVisible({ timeout: 15_000 });

    await page
      .getByRole("listitem")
      .filter({ hasText: "Acme Corporation" })
      .getByRole("link", { name: "View" })
      .click();
    await expect(page).toHaveURL(/\/clients\/[0-9a-f-]+$/);

    const detail = new ClientDetailPage(page);
    await expect(detail.detail()).toBeVisible();
    await expect(detail.detail()).toContainText("Acme Corporation");
  });

  test("shows not found for unknown client id", async ({ page }) => {
    const unknownId = "00000000-0000-0000-0000-000000000099";
    await page.goto(`/clients/${unknownId}`);

    const detail = new ClientDetailPage(page);
    await expect(detail.notFound()).toBeVisible();
    await expect(detail.notFound()).toContainText(/not found/i);
  });

  test("creates client with email and phone", async ({ page }) => {
    const clients = new ClientsPage(page);
    await clients.goto();

    const uniqueName = `E2E Client ${Date.now()}`;
    await page.getByTestId("client-name-input").fill(uniqueName);
    await page.getByTestId("client-type-select").selectOption("organization");
    await page.getByTestId("client-email-input").fill("e2e.client@example.com");
    await page.getByTestId("client-phone-input").fill("+1-555-0199");
    await page.getByRole("button", { name: "Add client" }).click();

    await expect(clients.clientRow(uniqueName)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("e2e.client@example.com")).toBeVisible();

    await page
      .getByRole("listitem")
      .filter({ hasText: uniqueName })
      .getByRole("link", { name: "View" })
      .click();

    const detail = new ClientDetailPage(page);
    await expect(detail.detail()).toContainText("e2e.client@example.com");
    await expect(detail.detail()).toContainText("+1-555-0199");
    await expect(detail.detail()).toContainText("organization");
  });
});
