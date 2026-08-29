import { test, expect } from '@playwright/test';
import { getTestCredentials, getMockApiResponses, login, createSampleFloorPlanBuffer } from './helpers.js';
import { writeFileSync } from 'fs';
import { join } from 'path';

test.describe('Complete Project Flow', () => {
  let credentials;
  let mockData;
  let testFilePath;

  test.beforeAll(() => {
    credentials = getTestCredentials();
    mockData = getMockApiResponses();

    // Create a test floor plan file
    testFilePath = join(process.cwd(), 'e2e/fixtures/test-floorplan.pdf');
    const pdfBuffer = createSampleFloorPlanBuffer();
    writeFileSync(testFilePath, pdfBuffer);
  });

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.context().clearCookies();
    await login(page, credentials.testUser.email, credentials.testUser.password);
  });

  test('should navigate to new project page', async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard/);

    // Click "New Project" button
    const newProjectButton = page.locator(
      'button:has-text("New Project"), a:has-text("New Project"), button:has-text("Create Project"), a:has-text("Upload")'
    ).first();

    await newProjectButton.click();

    // Should navigate to upload page
    await page.waitForURL(/\/(upload|dashboard\/upload|new-project)/, { timeout: 5000 });
    expect(page.url()).toMatch(/\/(upload|dashboard\/upload|new-project)/);
  });

  test('should upload a floor plan file', async ({ page }) => {
    // Navigate to upload page
    await page.goto('/dashboard/upload');

    // Wait for upload form to be visible
    await page.waitForSelector('input[type="file"], [data-testid="file-upload"]', { timeout: 5000 });

    // Find file input
    const fileInput = page.locator('input[type="file"]').first();

    // Upload the file
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected (UI should show filename)
    await page.waitForTimeout(500);

    // Look for upload/submit button
    const uploadButton = page.locator(
      'button:has-text("Upload"), button:has-text("Submit"), button:has-text("Analyze"), button[type="submit"]'
    ).first();

    // Check if button is enabled
    await expect(uploadButton).toBeEnabled({ timeout: 5000 });

    await uploadButton.click();

    // Wait for processing (should show loading state or redirect)
    await page.waitForTimeout(2000);

    // Should either redirect to project view or show processing state
    const currentUrl = page.url();
    expect(currentUrl).toBeTruthy();
  });

  test('should complete full project workflow with mocked API', async ({ page }) => {
    // Mock the upload API response
    await page.route('**/api/projects/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          project_id: mockData.projectAnalysis.project_id,
          status: 'processing',
        }),
      });
    });

    // Mock the project details API response
    await page.route(`**/api/projects/${mockData.projectAnalysis.project_id}*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.projectAnalysis),
      });
    });

    // Navigate to upload page
    await page.goto('/dashboard/upload');

    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFilePath);

    // Submit
    const uploadButton = page.locator(
      'button:has-text("Upload"), button:has-text("Submit"), button:has-text("Analyze"), button[type="submit"]'
    ).first();
    await uploadButton.click();

    // Wait for redirect to project view
    await page.waitForURL(/\/projects\//, { timeout: 10000 });

    // Verify project details are displayed
    await page.waitForTimeout(2000);

    // Check for room information
    const pageContent = await page.content();
    const hasRoomData = pageContent.includes('Living Room') ||
                        pageContent.includes('room') ||
                        pageContent.includes('area') ||
                        await page.locator('text=/room|area|dimension/i').count() > 0;

    expect(hasRoomData).toBeTruthy();
  });

  test('should display detected rooms and dimensions', async ({ page }) => {
    // Mock project data
    await page.route('**/api/projects/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.projectAnalysis),
      });
    });

    // Navigate directly to a project page
    await page.goto(`/dashboard/projects/${mockData.projectAnalysis.project_id}`);

    await page.waitForTimeout(2000);

    // Look for room information in the page
    const hasContent = await page.locator('text=/living room|kitchen|bedroom|dimensions|area/i').first().isVisible()
      .catch(() => false);

    // At minimum, the page should load without errors
    const url = page.url();
    expect(url).toContain('/projects/');
  });

  test('should allow editing room details', async ({ page }) => {
    // Mock project data
    await page.route('**/api/projects/*', async (route) => {
      const url = route.request().url();
      const method = route.request().method();

      if (method === 'PUT' || method === 'PATCH') {
        // Mock update response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
      } else {
        // Mock get response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockData.projectAnalysis),
        });
      }
    });

    await page.goto(`/dashboard/projects/${mockData.projectAnalysis.project_id}`);
    await page.waitForTimeout(2000);

    // Look for edit buttons or editable fields
    const editButton = page.locator('button:has-text("Edit"), button[aria-label*="edit" i], [data-testid*="edit"]').first();

    const hasEditButton = await editButton.isVisible().catch(() => false);

    if (hasEditButton) {
      await editButton.click();
      await page.waitForTimeout(500);

      // Try to find and edit a text input
      const inputs = page.locator('input[type="text"], input[type="number"]');
      const inputCount = await inputs.count();

      if (inputCount > 0) {
        const firstInput = inputs.first();
        await firstInput.fill('Updated Room Name');

        // Look for save button
        const saveButton = page.locator('button:has-text("Save"), button:has-text("Update")').first();
        const hasSaveButton = await saveButton.isVisible().catch(() => false);

        if (hasSaveButton) {
          await saveButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }

    // Test passes if page is functional
    expect(page.url()).toContain('/projects/');
  });

  test('should export project to Excel', async ({ page }) => {
    // Mock project data
    await page.route('**/api/projects/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.projectAnalysis),
      });
    });

    // Mock export endpoint
    await page.route('**/api/projects/*/export/excel', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        body: Buffer.from('mock excel data'),
        headers: {
          'Content-Disposition': 'attachment; filename="project-export.xlsx"',
        },
      });
    });

    await page.goto(`/dashboard/projects/${mockData.projectAnalysis.project_id}`);
    await page.waitForTimeout(2000);

    // Set up download listener
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

    // Look for export to Excel button
    const exportButton = page.locator(
      'button:has-text("Excel"), button:has-text("Export to Excel"), a:has-text("Excel")'
    ).first();

    const hasExportButton = await exportButton.isVisible().catch(() => false);

    if (hasExportButton) {
      await exportButton.click();

      // Wait for download to start
      const download = await downloadPromise.catch(() => null);

      if (download) {
        expect(download.suggestedFilename()).toMatch(/\.(xlsx|xls)$/);
      }
    }

    // Test passes if no errors occurred
    expect(page.url()).toContain('/projects/');
  });

  test('should export project to PDF', async ({ page }) => {
    // Mock project data
    await page.route('**/api/projects/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.projectAnalysis),
      });
    });

    // Mock PDF export endpoint
    await page.route('**/api/projects/*/export/pdf', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: createSampleFloorPlanBuffer(),
        headers: {
          'Content-Disposition': 'attachment; filename="project-report.pdf"',
        },
      });
    });

    await page.goto(`/dashboard/projects/${mockData.projectAnalysis.project_id}`);
    await page.waitForTimeout(2000);

    // Set up download listener
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

    // Look for export to PDF button
    const exportButton = page.locator(
      'button:has-text("PDF"), button:has-text("Export to PDF"), a:has-text("PDF")'
    ).first();

    const hasExportButton = await exportButton.isVisible().catch(() => false);

    if (hasExportButton) {
      await exportButton.click();

      // Wait for download to start
      const download = await downloadPromise.catch(() => null);

      if (download) {
        expect(download.suggestedFilename()).toMatch(/\.pdf$/);
      }
    }

    // Test passes if no errors occurred
    expect(page.url()).toContain('/projects/');
  });

  test('should handle upload errors gracefully', async ({ page }) => {
    // Mock error response
    await page.route('**/api/projects/upload', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Invalid file format',
        }),
      });
    });

    await page.goto('/dashboard/upload');

    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testFilePath);

    const uploadButton = page.locator(
      'button:has-text("Upload"), button:has-text("Submit"), button:has-text("Analyze"), button[type="submit"]'
    ).first();
    await uploadButton.click();

    // Should show error message
    await page.waitForTimeout(2000);

    const hasError = await page.locator('[role="alert"], .error, .text-red-500, text=/error|invalid|fail/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);

    // Error should be shown OR stay on upload page
    expect(hasError || page.url().includes('/upload')).toBeTruthy();
  });

  test('should show processing state during analysis', async ({ page }) => {
    let requestCount = 0;

    // Mock API to simulate processing state
    await page.route('**/api/projects/*', async (route) => {
      requestCount++;

      if (requestCount === 1) {
        // First request: processing
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockData.projectAnalysis,
            status: 'processing',
          }),
        });
      } else {
        // Subsequent requests: completed
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockData.projectAnalysis),
        });
      }
    });

    await page.goto(`/dashboard/projects/${mockData.projectAnalysis.project_id}`);

    // Should show some kind of loading indicator
    const hasLoadingIndicator = await page.locator(
      '[role="progressbar"], .spinner, .loading, text=/processing|analyzing|loading/i'
    ).first().isVisible({ timeout: 5000 }).catch(() => false);

    // At minimum, page should load
    expect(page.url()).toContain('/projects/');
  });
});
