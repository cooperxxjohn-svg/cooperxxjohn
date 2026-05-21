# Painting.AI - E2E Tests

End-to-end tests for critical user journeys using Playwright.

## Test Coverage

### 1. Authentication Flow (`auth.spec.js`)
- User registration with validation
- Login with valid/invalid credentials
- Logout functionality
- Full auth cycle: register → logout → login
- Auth persistence across page refreshes
- Protected route redirects

### 2. Complete Project Flow (`project-flow.spec.js`)
- Navigate to new project page
- Upload floor plan files (PDF/images)
- View project analysis results
- Display detected rooms and dimensions
- Edit room details
- Export project to Excel
- Export project to PDF
- Error handling for failed uploads
- Processing state indicators

### 3. Settings Management (`settings.spec.js`)
- Navigate to settings page
- Display user profile information
- Update profile name and details
- Success toast notifications
- API settings tab navigation
- Display and copy API key
- Form validation
- Subscription/plan information
- Error handling

### 4. Pricing & Navigation (`navigation.spec.js`)
- Landing page navigation
- Pricing page with multiple tiers
- "Start Free Trial" CTA flow
- Help/FAQ page with search
- Terms of Service
- Privacy Policy
- 404 Not Found handling
- Authenticated navigation (dashboard sections)
- User menu/dropdown
- Protected route guards
- Responsive navigation (mobile/tablet)
- Footer links

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run specific test file
```bash
npx playwright test e2e/auth.spec.js
```

### Run tests in UI mode
```bash
npm run test:e2e:ui
```

### Debug mode
```bash
npm run test:e2e:debug
```

### Run on specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run in headed mode (see browser)
```bash
npx playwright test --headed
```

### Generate HTML report
```bash
npx playwright show-report
```

## Test Configuration

**Browser Coverage:**
- Chromium (Desktop Chrome)
- Firefox (Desktop Firefox)
- WebKit (Desktop Safari)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

**Features:**
- Screenshots on failure
- Video recording for failures
- Trace on first retry
- Automatic dev server startup
- Parallel test execution

## Fixtures

Located in `e2e/fixtures/`:

- `test-credentials.json` - Test user credentials
- `mock-api-responses.json` - Mock API response data
- `test-floorplan.pdf` - Sample floor plan PDF for upload tests
- `sample-floorplan.svg` - Sample floor plan SVG image

## Helpers

The `helpers.js` file provides utility functions:

- `getTestCredentials()` - Load test user data
- `getMockApiResponses()` - Load mock API responses
- `login(page, email, password)` - Login helper
- `logout(page)` - Logout helper
- `setupAuthenticatedPage(page, testUser)` - Setup auth context
- `mockUploadResponse(page, response)` - Mock file upload API
- `mockProjectAnalysis(page, projectId, response)` - Mock analysis API
- `waitForToast(page, expectedText)` - Wait for toast notifications
- `createSampleFloorPlanBuffer()` - Generate test PDF

## CI/CD Integration

The tests are configured to run in CI environments with:
- 2 retries on failure
- Single worker for stability
- JSON and HTML reports
- Screenshots and videos saved to `test-results/`

## Writing New Tests

1. Create a new `.spec.js` file in the `e2e/` directory
2. Import helpers: `import { test, expect } from '@playwright/test';`
3. Use helpers from `./helpers.js` for common operations
4. Follow the existing test patterns for consistency
5. Use mocks for API responses when possible
6. Add descriptive test names and comments

## Troubleshooting

### Tests failing locally
- Ensure dev server is running on http://localhost:3000
- Check that all dependencies are installed: `npm install`
- Clear browser cache: `npx playwright test --headed --project=chromium`

### Tests timing out
- Increase timeout in `playwright.config.js`
- Check for slow API responses or network issues
- Verify selectors are correct and elements are visible

### Flaky tests
- Add explicit waits: `await page.waitForSelector()`
- Use `waitForURL()` instead of `waitForTimeout()`
- Check for race conditions in async operations

## Best Practices

1. **Use data-testid attributes** for stable selectors
2. **Avoid hard-coded delays** - use `waitFor` methods
3. **Mock external APIs** to avoid flakiness
4. **Test user flows**, not implementation details
5. **Keep tests independent** - each test should work in isolation
6. **Use descriptive assertions** with clear error messages
7. **Clean up after tests** - clear cookies, localStorage, etc.

## Coverage Goals

- ✅ Critical user registration and login flows
- ✅ Complete project creation and analysis workflow
- ✅ Settings and profile management
- ✅ Navigation and public pages
- ✅ Export functionality (Excel/PDF)
- ✅ Error handling and validation
- ✅ Responsive design (mobile/tablet)

## Maintenance

- Review and update test credentials regularly
- Update mock data to match current API responses
- Add tests for new features before deployment
- Run full test suite before major releases
- Monitor test execution times and optimize slow tests
