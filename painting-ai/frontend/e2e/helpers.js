import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * Load test credentials
 */
export function getTestCredentials() {
  const credPath = join(process.cwd(), 'e2e/fixtures/test-credentials.json');
  return JSON.parse(readFileSync(credPath, 'utf-8'));
}

/**
 * Load mock API responses
 */
export function getMockApiResponses() {
  const mockPath = join(process.cwd(), 'e2e/fixtures/mock-api-responses.json');
  return JSON.parse(readFileSync(mockPath, 'utf-8'));
}

/**
 * Login helper - performs login and returns auth state
 */
export async function login(page, email, password) {
  await page.goto('/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard', { timeout: 10000 });
}

/**
 * Logout helper
 */
export async function logout(page) {
  // Look for logout button in the UI
  await page.click('button:has-text("Logout"), a:has-text("Logout")');
  await page.waitForURL('/login', { timeout: 5000 });
}

/**
 * Setup authenticated context
 */
export async function setupAuthenticatedPage(page, testUser) {
  await login(page, testUser.email, testUser.password);
  return page;
}

/**
 * Mock API response for file upload
 */
export async function mockUploadResponse(page, response) {
  await page.route('**/api/projects/upload', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API response for project analysis
 */
export async function mockProjectAnalysis(page, projectId, response) {
  await page.route(`**/api/projects/${projectId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Wait for toast notification
 */
export async function waitForToast(page, expectedText) {
  const toast = page.locator('[role="alert"], .toast, [data-testid="toast"]');
  await toast.waitFor({ state: 'visible', timeout: 5000 });
  if (expectedText) {
    await expect(toast).toContainText(expectedText);
  }
  return toast;
}

/**
 * Create a sample floor plan file buffer
 */
export function createSampleFloorPlanBuffer() {
  // Create a minimal valid PDF buffer
  const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 24 Tf
100 700 Td
(Floor Plan) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF`;

  return Buffer.from(pdfContent);
}
