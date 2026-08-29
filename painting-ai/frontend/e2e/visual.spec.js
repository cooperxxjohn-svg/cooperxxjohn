import { test, expect } from '@playwright/test';
import { getTestCredentials, login } from './helpers.js';

/**
 * Visual Regression Tests
 * These tests capture screenshots and compare them to baseline images
 * to detect unintended visual changes.
 *
 * Run with: npx playwright test visual.spec.js --update-snapshots
 * to update baseline images when intentional changes are made.
 */

test.describe('Visual Regression Tests', () => {
  test.describe('Public Pages', () => {
    test('landing page should match screenshot', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(1000); // Wait for animations

      // Take full page screenshot
      await expect(page).toHaveScreenshot('landing-page.png', {
        fullPage: true,
        maxDiffPixels: 100, // Allow small differences
      });
    });

    test('pricing page should match screenshot', async ({ page }) => {
      await page.goto('/pricing');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('pricing-page.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });

    test('login page should match screenshot', async ({ page }) => {
      await page.goto('/login');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot('login-page.png', {
        fullPage: true,
        maxDiffPixels: 50,
      });
    });

    test('register page should match screenshot', async ({ page }) => {
      await page.goto('/register');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot('register-page.png', {
        fullPage: true,
        maxDiffPixels: 50,
      });
    });
  });

  test.describe('Authenticated Pages', () => {
    let credentials;

    test.beforeAll(() => {
      credentials = getTestCredentials();
    });

    test.beforeEach(async ({ page }) => {
      await page.context().clearCookies();
      await login(page, credentials.testUser.email, credentials.testUser.password);
    });

    test('dashboard should match screenshot', async ({ page }) => {
      await expect(page).toHaveURL(/\/dashboard/);
      await page.waitForTimeout(1500);

      await expect(page).toHaveScreenshot('dashboard-page.png', {
        fullPage: true,
        maxDiffPixels: 150,
      });
    });

    test('upload page should match screenshot', async ({ page }) => {
      await page.goto('/dashboard/upload');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('upload-page.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });

    test('settings page should match screenshot', async ({ page }) => {
      await page.goto('/dashboard/settings');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('settings-page.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });
  });

  test.describe('Component Screenshots', () => {
    test('navigation header', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(500);

      const header = page.locator('header, nav').first();
      await expect(header).toHaveScreenshot('header-component.png', {
        maxDiffPixels: 50,
      });
    });

    test('footer component', async ({ page }) => {
      await page.goto('/');
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(500);

      const footer = page.locator('footer').first();
      const hasFooter = await footer.isVisible().catch(() => false);

      if (hasFooter) {
        await expect(footer).toHaveScreenshot('footer-component.png', {
          maxDiffPixels: 50,
        });
      }
    });
  });

  test.describe('Responsive Screenshots', () => {
    test('landing page on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('landing-mobile.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });

    test('landing page on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('landing-tablet.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });

    test('pricing page on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/pricing');
      await page.waitForTimeout(1000);

      await expect(page).toHaveScreenshot('pricing-mobile.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    });
  });
});
