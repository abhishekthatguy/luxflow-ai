import { expect, test } from "../fixtures/auth.fixture";

test.describe("Route coverage", () => {
  test.beforeEach(async ({ loginAsJane }) => {
    await loginAsJane();
  });

  test("case overview loads for seeded case flow", async ({ page }) => {
    await page.goto("/cases/new");
    await expect(page.getByRole("heading", { name: "New case" })).toBeVisible();
  });

  test("unknown case shows not found message", async ({ page }) => {
    const unknownCaseId = "00000000-0000-0000-0000-000000000099";
    await page.goto(`/cases/${unknownCaseId}/overview`);
    await expect(page.getByText(/not found|matter wall/i)).toBeVisible();
  });
});
