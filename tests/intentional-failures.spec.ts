import { test, expect } from '@playwright/test';

test.describe('Intentional failures — QA Agent trigger', () => {

  test('should find a button that does not exist', async ({ page }) => {
    await page.goto('https://example.com');
    // This button does not exist on the page — will fail
    await expect(page.getByRole('button', { name: 'Buy Now' })).toBeVisible({ timeout: 3000 });
  });

  test('should find a heading with wrong text', async ({ page }) => {
    await page.goto('https://example.com');
    // The real heading is "Example Domain", not this
    await expect(page.getByRole('heading', { name: 'Welcome to my store' })).toBeVisible({ timeout: 3000 });
  });

  test('should navigate to a page that returns 404', async ({ page }) => {
    const response = await page.goto('https://example.com/this-page-does-not-exist');
    // Expects 200 but will get 404
    expect(response?.status()).toBe(200);
  });

});
