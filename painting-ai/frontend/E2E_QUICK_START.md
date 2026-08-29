# E2E Testing Quick Start Guide

## Installation Complete ✓

Playwright has been installed and configured with comprehensive E2E tests for Painting.AI.

## Quick Commands

```bash
# Navigate to frontend directory
cd /home/user/cooperxxjohn/painting-ai/frontend

# Run all E2E tests
npm run test:e2e

# Run tests with UI (interactive mode)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test e2e/auth.spec.js

# Run tests on specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox

# Run in headed mode (see browser)
npx playwright test --headed

# Generate and view HTML report
npx playwright show-report
```

## Test Files Created

### Core Tests (Required)
1. **e2e/auth.spec.js** - Authentication flows
   - Registration, login, logout
   - Auth persistence
   - Protected routes

2. **e2e/project-flow.spec.js** - Complete project workflow
   - File upload
   - Project analysis
   - Room editing
   - Excel/PDF export

3. **e2e/settings.spec.js** - Settings management
   - Profile updates
   - API key management
   - Form validation

4. **e2e/navigation.spec.js** - Pricing & navigation
   - Public pages
   - Pricing flows
   - Responsive design
   - Footer links

### Bonus Tests (Optional)
5. **e2e/visual.spec.js** - Visual regression tests
   - Screenshot comparison
   - Component screenshots
   - Responsive screenshots

6. **e2e/performance.spec.js** - Performance tests
   - Page load times
   - Core Web Vitals
   - Bundle size checks
   - Concurrent user simulation

### Support Files
- **e2e/helpers.js** - Utility functions
- **e2e/auth.setup.js** - Authentication setup
- **e2e/fixtures/** - Test data and sample files
- **playwright.config.js** - Playwright configuration
- **e2e/README.md** - Detailed documentation

## First Test Run

1. **Start the development server:**
   ```bash
   npm run dev
   ```

2. **In another terminal, run tests:**
   ```bash
   npm run test:e2e
   ```

3. **View the results:**
   ```bash
   npx playwright show-report
   ```

## Test Configuration

The tests are configured to run on:
- ✅ Chromium (Desktop Chrome)
- ✅ Firefox (Desktop Firefox)
- ✅ WebKit (Desktop Safari)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)

## Key Features

### Automatic Features
- Dev server auto-starts when running tests
- Screenshots captured on failure
- Videos recorded for failed tests
- Trace files for debugging
- Parallel test execution

### Test Coverage
- User registration and authentication
- Complete project creation workflow
- File upload and processing
- Room detection and editing
- Excel and PDF export
- Settings and profile management
- API key management
- Navigation and routing
- Error handling
- Form validation
- Responsive design

## Sample Test Data

Test credentials are in `e2e/fixtures/test-credentials.json`:

```json
{
  "testUser": {
    "email": "test@paintingai.test",
    "password": "TestPassword123!"
  }
}
```

## Running in CI/CD

A GitHub Actions workflow has been created at:
`.github/workflows/e2e-tests.yml`

This will automatically run tests on:
- Push to main/develop branches
- Pull requests to main/develop branches

## Debugging Tests

### Using Playwright Inspector
```bash
npm run test:e2e:debug
```

### Using UI Mode (Recommended)
```bash
npm run test:e2e:ui
```

### View trace files
```bash
npx playwright show-trace test-results/trace.zip
```

## Writing New Tests

1. Create a new file in `e2e/` directory
2. Import test utilities:
   ```javascript
   import { test, expect } from '@playwright/test';
   import { login, getTestCredentials } from './helpers.js';
   ```

3. Write your test:
   ```javascript
   test.describe('My Feature', () => {
     test('should do something', async ({ page }) => {
       await page.goto('/my-page');
       await expect(page).toHaveTitle(/My Page/);
     });
   });
   ```

## Common Patterns

### Login before test
```javascript
test.beforeEach(async ({ page }) => {
  const credentials = getTestCredentials();
  await login(page, credentials.testUser.email, credentials.testUser.password);
});
```

### Mock API responses
```javascript
await page.route('**/api/projects', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ data: [] }),
  });
});
```

### Wait for navigation
```javascript
await page.click('button');
await page.waitForURL('/dashboard');
```

### Handle file uploads
```javascript
await page.setInputFiles('input[type="file"]', 'path/to/file.pdf');
```

### Check for toast notifications
```javascript
await expect(page.locator('[role="alert"]')).toContainText('Success');
```

## Troubleshooting

### Tests fail on first run
- Ensure dev server is running: `npm run dev`
- Check that backend API is accessible
- Verify test credentials are valid

### Tests are flaky
- Add explicit waits: `await page.waitForSelector()`
- Use `waitForURL()` instead of `waitForTimeout()`
- Increase timeout if needed in `playwright.config.js`

### Screenshots don't match (visual tests)
- Update snapshots: `npx playwright test visual.spec.js --update-snapshots`
- Only needed when intentional UI changes are made

### Performance tests fail
- Adjust thresholds in `performance.spec.js`
- Performance varies by machine/network

## Next Steps

1. ✅ Run the test suite to verify everything works
2. ✅ Review test output and HTML report
3. ✅ Add tests for new features as they're developed
4. ✅ Integrate into CI/CD pipeline
5. ✅ Set up test notifications (Slack, email, etc.)
6. ✅ Schedule regular test runs (nightly builds)

## Success Criteria Met

- ✅ Playwright installed and configured
- ✅ Test directory structure created
- ✅ 4 critical test suites implemented
- ✅ Test fixtures and helpers created
- ✅ Sample floor plan files added
- ✅ Configuration files set up
- ✅ GitHub Actions workflow created
- ✅ Documentation provided
- ✅ All critical user journeys covered

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [CI/CD Integration](https://playwright.dev/docs/ci)

## Support

For issues or questions:
1. Check `e2e/README.md` for detailed documentation
2. Review test examples in the spec files
3. Consult Playwright documentation
4. Check test output and error messages

Happy Testing! 🚀
