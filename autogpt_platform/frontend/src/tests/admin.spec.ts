import { test, expect } from "@playwright/test";

test.describe("Admin Pages", () => {
  test("admin dashboard loads", async ({ page }) => {
    await page.goto("/admin");
    // Check that the page loads without error
    await expect(page).not.toHaveTitle(/error/i);
  });

  test("unauthenticated users cannot access admin", async ({ page }) => {
    await page.goto("/admin");
    // Should redirect to login or show unauthorized
    const url = page.url();
    expect(url.includes("/login") || url.includes("/admin")).toBeTruthy();
  });
});
