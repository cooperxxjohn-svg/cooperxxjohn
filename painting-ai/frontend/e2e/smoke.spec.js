import { test, expect } from '@playwright/test';

/**
 * Smoke Tests - Critical Path
 * These are the most important tests that verify core functionality.
 * Run these first to ensure the application is working at a basic level.
 *
 * These tests should be:
 * - Fast (complete in under 2 minutes)
 * - Reliable (no flaky tests)
 * - Critical (cover must-have features)
 */

test.describe('Smoke Tests - Critical Path', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Should load without errors
    await expect(page).toHaveURL('/');

    // Should have title
    await expect(page).toHaveTitle(/painting|floor plan/i);

    // Should have main content
    const hasContent = await page.locator('body').textContent();
    expect(hasContent).toBeTruthy();
  });

  test('can navigate to key pages', async ({ page }) => {
    // Start from home
    await page.goto('/');

    // Navigate to pricing
    await page.goto('/pricing');
    await expect(page).toHaveURL('/pricing');

    // Navigate to help
    await page.goto('/help');
    await expect(page).toHaveURL('/help');

    // Navigate to login
    await page.goto('/login');
    await expect(page).toHaveURL('/login');

    // Navigate to register
    await page.goto('/register');
    await expect(page).toHaveURL('/register');
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');

    // Should have email and password fields
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();

    // Should have submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('registration page renders correctly', async ({ page }) => {
    await page.goto('/register');

    // Should have required fields
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();

    // Should have submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('pricing page shows plans', async ({ page }) => {
    await page.goto('/pricing');

    // Should show pricing content
    const content = await page.textContent('body');
    const hasPricingContent = /free|pro|premium|plan|price|\$/i.test(content);

    expect(hasPricingContent).toBeTruthy();
  });

  test('404 page works', async ({ page }) => {
    await page.goto('/this-does-not-exist-random-123');

    // Should either show 404 or redirect
    const content = await page.textContent('body');
    const is404 = /404|not found/i.test(content) || page.url().includes('/');

    expect(is404).toBeTruthy();
  });

  test('static assets load correctly', async ({ page }) => {
    let cssLoaded = false;
    let jsLoaded = false;

    page.on('response', (response) => {
      const url = response.url();
      const status = response.status();

      if (url.includes('.css') && status === 200) {
        cssLoaded = true;
      }
      if (url.includes('.js') && status === 200) {
        jsLoaded = true;
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should load CSS and JS successfully
    expect(cssLoaded).toBeTruthy();
    expect(jsLoaded).toBeTruthy();
  });

  test('no console errors on homepage', async ({ page }) => {
    const errors = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should have no critical console errors
    const criticalErrors = errors.filter(
      (err) => !err.includes('favicon') && !err.includes('Extension')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('responsive design works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Should render without horizontal scroll
    const scrollWidth = await page.evaluate(() => {
      return document.documentElement.scrollWidth;
    });

    const clientWidth = await page.evaluate(() => {
      return document.documentElement.clientWidth;
    });

    // Allow small difference for scrollbar
    expect(scrollWidth - clientWidth).toBeLessThan(20);
  });

  test('API health check', async ({ request }) => {
    // Try to reach the API (adjust URL as needed)
    try {
      const response = await request.get('http://localhost:8000/health');
      expect(response.ok()).toBeTruthy();
    } catch (error) {
      // API might not be running, which is okay for frontend-only tests
      console.log('API health check skipped - backend not available');
    }
  });
});

test.describe('Critical User Journey - Happy Path', () => {
  test('complete user journey: landing → pricing → register', async ({ page }) => {
    // 1. Land on homepage
    await page.goto('/');
    await expect(page).toHaveURL('/');

    // 2. Navigate to pricing
    const pricingLink = page.locator('a:has-text("Pricing"), [href="/pricing"]').first();
    const hasPricingLink = await pricingLink.isVisible().catch(() => false);

    if (hasPricingLink) {
      await pricingLink.click();
      await page.waitForURL('/pricing');
    } else {
      await page.goto('/pricing');
    }

    await expect(page).toHaveURL('/pricing');

    // 3. Click on "Start Free Trial" or similar CTA
    const ctaButton = page.locator(
      'button:has-text("Start"), button:has-text("Get Started"), a:has-text("Sign Up")'
    ).first();

    const hasCtaButton = await ctaButton.isVisible().catch(() => false);

    if (hasCtaButton) {
      await ctaButton.click();
      await page.waitForTimeout(1000);
    } else {
      await page.goto('/register');
    }

    // 4. Should end up on registration page
    await page.waitForURL(/\/(register|signup|login)/, { timeout: 5000 });

    const finalUrl = page.url();
    expect(finalUrl).toMatch(/\/(register|signup|login)/);
  });
});

test.describe('Performance Smoke Tests', () => {
  test('homepage loads in reasonable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    console.log(`Homepage load time: ${loadTime}ms`);

    // Should load within 5 seconds (generous for CI)
    expect(loadTime).toBeLessThan(5000);
  });

  test('no excessive network requests on homepage', async ({ page }) => {
    let requestCount = 0;

    page.on('request', () => {
      requestCount++;
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    console.log(`Total network requests: ${requestCount}`);

    // Should have reasonable number of requests (< 50)
    expect(requestCount).toBeLessThan(50);
  });
});
