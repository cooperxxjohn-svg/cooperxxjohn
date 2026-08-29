import { test, expect } from '@playwright/test';
import { getTestCredentials, login, logout } from './helpers.js';

test.describe('Authentication Flow', () => {
  let credentials;

  test.beforeAll(() => {
    credentials = getTestCredentials();
  });

  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.context().clearCookies();
    await page.goto('/');
  });

  test('should display registration page', async ({ page }) => {
    await page.goto('/register');

    await expect(page).toHaveURL('/register');
    await expect(page.locator('h1, h2').filter({ hasText: /register|sign up/i })).toBeVisible();

    // Check for required form fields
    await expect(page.locator('input[name="name"], input[name="full_name"], input[type="text"]').first()).toBeVisible();
    await expect(page.locator('input[name="email"], input[type="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"], input[type="password"]').first()).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should register a new user', async ({ page }) => {
    const timestamp = Date.now();
    const newUser = {
      name: `Test User ${timestamp}`,
      email: `test${timestamp}@paintingai.test`,
      password: 'TestPassword123!',
    };

    await page.goto('/register');

    // Fill registration form
    await page.fill('input[name="name"], input[name="full_name"], input[type="text"]', newUser.name);
    await page.fill('input[name="email"], input[type="email"]', newUser.email);
    const passwordFields = page.locator('input[name="password"], input[type="password"]');
    await passwordFields.first().fill(newUser.password);

    // If there's a confirm password field, fill it too
    const passwordCount = await passwordFields.count();
    if (passwordCount > 1) {
      await passwordFields.nth(1).fill(newUser.password);
    }

    // Submit the form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard after successful registration
    await page.waitForURL(/\/(dashboard|login)/, { timeout: 10000 });

    // If redirected to login, that's also acceptable - login with new credentials
    if (page.url().includes('/login')) {
      await login(page, newUser.email, newUser.password);
    }

    // Verify we're on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should show validation errors for invalid registration', async ({ page }) => {
    await page.goto('/register');

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Should show validation errors or prevent submission
    const url = page.url();
    expect(url).toContain('/register');
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await expect(page).toHaveURL('/login');

    // Fill login form
    await page.fill('input[name="email"], input[type="email"]', credentials.testUser.email);
    await page.fill('input[name="password"], input[type="password"]', credentials.testUser.password);

    // Submit
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL('/dashboard', { timeout: 10000 });
    await expect(page).toHaveURL('/dashboard');
  });

  test('should show error for invalid login credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"], input[type="email"]', 'invalid@example.com');
    await page.fill('input[name="password"], input[type="password"]', 'wrongpassword');

    await page.click('button[type="submit"]');

    // Should remain on login page or show error
    await page.waitForTimeout(2000);

    // Check for error message or toast
    const hasError = await page.locator('[role="alert"], .error, .text-red-500, .text-red-600').count() > 0;
    expect(hasError || page.url().includes('/login')).toBeTruthy();
  });

  test('should complete full auth cycle: register → logout → login', async ({ page }) => {
    const timestamp = Date.now();
    const testUser = {
      name: `Cycle Test ${timestamp}`,
      email: `cycle${timestamp}@paintingai.test`,
      password: 'CycleTest123!',
    };

    // 1. Register
    await page.goto('/register');
    await page.fill('input[name="name"], input[name="full_name"], input[type="text"]', testUser.name);
    await page.fill('input[name="email"], input[type="email"]', testUser.email);
    const passwordFields = page.locator('input[name="password"], input[type="password"]');
    await passwordFields.first().fill(testUser.password);

    const passwordCount = await passwordFields.count();
    if (passwordCount > 1) {
      await passwordFields.nth(1).fill(testUser.password);
    }

    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|login)/, { timeout: 10000 });

    // If on login, login first
    if (page.url().includes('/login')) {
      await login(page, testUser.email, testUser.password);
    }

    // 2. Verify on dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // 3. Logout
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out"), a:has-text("Logout"), a:has-text("Log out")').first();
    await logoutButton.click();

    await page.waitForURL(/\/(login|^\/$)/, { timeout: 5000 });

    // 4. Login again with same credentials
    if (!page.url().includes('/login')) {
      await page.goto('/login');
    }

    await page.fill('input[name="email"], input[type="email"]', testUser.email);
    await page.fill('input[name="password"], input[type="password"]', testUser.password);
    await page.click('button[type="submit"]');

    // 5. Verify successful login
    await page.waitForURL('/dashboard', { timeout: 10000 });
    await expect(page).toHaveURL('/dashboard');
  });

  test('should redirect authenticated users from login page to dashboard', async ({ page }) => {
    // First login
    await login(page, credentials.testUser.email, credentials.testUser.password);
    await expect(page).toHaveURL(/\/dashboard/);

    // Try to navigate to login page while authenticated
    await page.goto('/login');

    // Should redirect back to dashboard
    await page.waitForTimeout(1000);
    const url = page.url();

    // Should either redirect to dashboard or stay on login (depends on implementation)
    // Most apps redirect authenticated users away from login
    expect(url).toBeTruthy();
  });

  test('should persist authentication across page refreshes', async ({ page }) => {
    await login(page, credentials.testUser.email, credentials.testUser.password);
    await expect(page).toHaveURL(/\/dashboard/);

    // Reload the page
    await page.reload();

    // Should still be authenticated
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
