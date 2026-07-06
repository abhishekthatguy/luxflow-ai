import { expect, test } from "../fixtures/auth.fixture";
import { LoginPage } from "../pages/login.page";

test.describe("Authentication", () => {
  test("signs in with dev seed credentials", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn("jane@example.com", "password123");
    await expect(page).toHaveURL(/\/cases/);
    await expect(page.getByRole("heading", { name: "Cases" })).toBeVisible();
  });

  test("shows meaningful error for invalid .local email", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn("jane@lexflow.local", "password123");
    await expect(login.errorAlert()).toContainText(/example\.com/i);
  });

  test("redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/cases");
    await expect(page).toHaveURL(/\/login/);
  });
});
