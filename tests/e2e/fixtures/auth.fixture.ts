import { test as base, expect } from "@playwright/test";

export type AuthFixtures = {
  loginAsJane: () => Promise<void>;
};

export const test = base.extend<AuthFixtures>({
  loginAsJane: async ({ page }, use) => {
    const login = async () => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(process.env.E2E_USER_EMAIL ?? "jane@example.com");
      await page.getByLabel("Password").fill(process.env.E2E_USER_PASSWORD ?? "password123");
      await page.getByRole("button", { name: "Sign in" }).click();
      await expect(page).toHaveURL(/\/cases/);
    };
    await use(login);
  },
});

export { expect };
