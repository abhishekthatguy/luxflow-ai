import { test as base, expect } from "@playwright/test";

export type AuthFixtures = {
  loginAsJane: () => Promise<void>;
  createCase: (title?: string) => Promise<string>;
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

  createCase: async ({ page, loginAsJane }, use) => {
    const createCase = async (title = "E2E Sprint 4 Case") => {
      await loginAsJane();
      const caseNumber = `e2e-${Date.now()}`;
      await page.goto("/cases/new");
      await page.getByLabel("Case number").fill(caseNumber);
      await page.getByLabel("Title").fill(title);
      await page.getByRole("button", { name: "Create case" }).click();
      await expect(page).toHaveURL(/\/cases\/[0-9a-f-]+\/overview$/);
      const match = page.url().match(/\/cases\/([0-9a-f-]+)/);
      if (!match) throw new Error("Could not parse case id from URL");
      return match[1];
    };
    await use(createCase);
  },
});

export { expect };
