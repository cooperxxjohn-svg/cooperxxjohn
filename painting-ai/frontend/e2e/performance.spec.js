import { test, expect } from '@playwright/test';
import { getTestCredentials, login } from './helpers.js';

/**
 * Performance Tests
 * These tests measure page load times, lighthouse scores,
 * and other performance metrics to ensure a fast user experience.
 */

test.describe('Performance Tests', () => {
  test('landing page should load quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');

    const loadTime = Date.now() - startTime;

    // Page should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);

    console.log(`Landing page load time: ${loadTime}ms`);
  });

  test('pricing page should load quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/pricing');

    const loadTime = Date.now() - startTime;

    // Page should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);

    console.log(`Pricing page load time: ${loadTime}ms`);
  });

  test('dashboard should load quickly after login', async ({ page }) => {
    const credentials = getTestCredentials();

    // Login first
    await login(page, credentials.testUser.email, credentials.testUser.password);

    // Measure dashboard load time
    const startTime = Date.now();

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Dashboard should load in under 4 seconds
    expect(loadTime).toBeLessThan(4000);

    console.log(`Dashboard load time: ${loadTime}ms`);
  });

  test('should have acceptable Core Web Vitals', async ({ page }) => {
    await page.goto('/');

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Measure Core Web Vitals
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        // Use PerformanceObserver to get metrics
        const metrics = {
          lcp: 0,
          fid: 0,
          cls: 0,
        };

        // Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          metrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // Cumulative Layout Shift
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          metrics.cls = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });

        // Wait a bit for metrics to be collected
        setTimeout(() => {
          resolve(metrics);
        }, 2000);
      });
    });

    console.log('Core Web Vitals:', metrics);

    // LCP should be under 2.5 seconds (good)
    if (metrics.lcp > 0) {
      expect(metrics.lcp).toBeLessThan(2500);
    }

    // CLS should be under 0.1 (good)
    if (metrics.cls > 0) {
      expect(metrics.cls).toBeLessThan(0.1);
    }
  });

  test('should not have excessive bundle size', async ({ page }) => {
    // Monitor network requests
    const jsResources = [];
    const cssResources = [];

    page.on('response', (response) => {
      const url = response.url();
      const size = parseInt(response.headers()['content-length'] || '0');

      if (url.includes('.js')) {
        jsResources.push({ url, size });
      } else if (url.includes('.css')) {
        cssResources.push({ url, size });
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Calculate total JS size
    const totalJsSize = jsResources.reduce((sum, r) => sum + r.size, 0);
    const totalCssSize = cssResources.reduce((sum, r) => sum + r.size, 0);

    console.log(`Total JS size: ${(totalJsSize / 1024).toFixed(2)} KB`);
    console.log(`Total CSS size: ${(totalCssSize / 1024).toFixed(2)} KB`);

    // JS bundle should be under 500KB (uncompressed)
    expect(totalJsSize).toBeLessThan(500 * 1024);

    // CSS should be under 100KB
    expect(totalCssSize).toBeLessThan(100 * 1024);
  });

  test('should have minimal render-blocking resources', async ({ page }) => {
    let renderBlockingCount = 0;

    page.on('response', (response) => {
      const url = response.url();
      const contentType = response.headers()['content-type'] || '';

      // Check for render-blocking resources
      if (
        (contentType.includes('javascript') || contentType.includes('css')) &&
        !url.includes('async') &&
        !url.includes('defer')
      ) {
        renderBlockingCount++;
      }
    });

    await page.goto('/');

    console.log(`Render-blocking resources: ${renderBlockingCount}`);

    // Should have minimal render-blocking resources
    expect(renderBlockingCount).toBeLessThan(10);
  });

  test('images should be optimized', async ({ page }) => {
    const images = [];

    page.on('response', async (response) => {
      const url = response.url();
      const contentType = response.headers()['content-type'] || '';

      if (contentType.includes('image')) {
        const size = parseInt(response.headers()['content-length'] || '0');
        images.push({ url, size, contentType });
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    console.log(`Total images loaded: ${images.length}`);

    // Check each image size
    for (const img of images) {
      console.log(`Image: ${img.url.substring(0, 50)}... - ${(img.size / 1024).toFixed(2)} KB`);

      // Individual images should be under 500KB
      expect(img.size).toBeLessThan(500 * 1024);
    }

    // Total image payload should be reasonable
    const totalImageSize = images.reduce((sum, img) => sum + img.size, 0);
    console.log(`Total image size: ${(totalImageSize / 1024).toFixed(2)} KB`);

    expect(totalImageSize).toBeLessThan(2 * 1024 * 1024); // 2MB
  });

  test('should handle concurrent users efficiently', async ({ browser }) => {
    const credentials = getTestCredentials();

    // Simulate 5 concurrent users
    const contexts = await Promise.all(
      Array(5).fill(null).map(() => browser.newContext())
    );

    const pages = await Promise.all(
      contexts.map(context => context.newPage())
    );

    const startTime = Date.now();

    // All users login simultaneously
    await Promise.all(
      pages.map(async (page) => {
        await login(page, credentials.testUser.email, credentials.testUser.password);
      })
    );

    const totalTime = Date.now() - startTime;

    console.log(`5 concurrent logins completed in: ${totalTime}ms`);

    // Should handle concurrent requests efficiently
    expect(totalTime).toBeLessThan(10000); // 10 seconds for 5 concurrent logins

    // Cleanup
    await Promise.all(contexts.map(context => context.close()));
  });

  test('navigation should be instantaneous', async ({ page }) => {
    await page.goto('/');

    // Measure navigation time
    const measureNavigation = async (url) => {
      const startTime = Date.now();
      await page.click(`a[href="${url}"]`);
      await page.waitForURL(url);
      return Date.now() - startTime;
    };

    const pricingNavTime = await measureNavigation('/pricing');
    console.log(`Navigation to pricing: ${pricingNavTime}ms`);

    // Client-side navigation should be very fast
    expect(pricingNavTime).toBeLessThan(1000);

    const helpNavTime = await measureNavigation('/help');
    console.log(`Navigation to help: ${helpNavTime}ms`);

    expect(helpNavTime).toBeLessThan(1000);
  });

  test('should cache static assets', async ({ page }) => {
    // First load
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    let cachedResources = 0;

    page.on('response', (response) => {
      const cacheHeader = response.headers()['cache-control'];
      if (cacheHeader && (cacheHeader.includes('max-age') || cacheHeader.includes('immutable'))) {
        cachedResources++;
      }
    });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    console.log(`Resources with cache headers: ${cachedResources}`);

    // Should have caching enabled for static assets
    expect(cachedResources).toBeGreaterThan(0);
  });
});
