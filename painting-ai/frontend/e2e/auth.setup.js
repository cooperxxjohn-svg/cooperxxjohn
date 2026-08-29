import { test as setup, expect } from '@playwright/test';
import { getTestCredentials } from './helpers.js';

/**
 * Authentication setup for reusable auth state
 * This creates authenticated sessions that can be reused across tests
 * to avoid logging in for every test.
 */

const authFile = '.auth/user.json';

setup('authenticate as test user', async ({ page }) => {
  const credentials = getTestCredentials();
  const testUser = credentials.testUser;

  // Navigate to login page
  await page.goto('/login');

  // Perform login
  await page.fill('input[name="email"], input[type="email"]', testUser.email);
  await page.fill('input[name="password"], input[type="password"]', testUser.password);
  await page.click('button[type="submit"]');

  // Wait for successful login (redirect to dashboard)
  await page.waitForURL(/\/dashboard/, { timeout: 10000 });

  // Verify we're authenticated
  await expect(page).toHaveURL(/\/dashboard/);

  // Save authentication state
  await page.context().storageState({ path: authFile });
});

// You can create multiple auth states for different user roles
setup('authenticate as premium user', async ({ page }) => {
  const credentials = getTestCredentials();
  const testUser = credentials.testUser2 || credentials.testUser;

  await page.goto('/login');

  await page.fill('input[name="email"], input[type="email"]', testUser.email);
  await page.fill('input[name="password"], input[type="password"]', testUser.password);
  await page.click('button[type="submit"]');

  await page.waitForURL(/\/dashboard/, { timeout: 10000 });

  await page.context().storageState({ path: '.auth/premium-user.json' });
});
