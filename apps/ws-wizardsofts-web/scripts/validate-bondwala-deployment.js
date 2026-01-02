#!/usr/bin/env node

/**
 * BondWala Deployment Validation Script
 *
 * This script validates that the BondWala coming soon page is properly deployed
 * and displays the expected content.
 *
 * Usage:
 *   node scripts/validate-bondwala-deployment.js
 *   node scripts/validate-bondwala-deployment.js https://www.wizardsofts.com/bondwala
 */

const puppeteer = require('puppeteer');

const DEPLOYMENT_URL = process.argv[2] || 'http://localhost:3000/bondwala';
const TIMEOUT = 30000; // 30 seconds

async function validateBondWalaDeployment() {
  console.log('🚀 BondWala Deployment Validation');
  console.log('==================================\n');
  console.log(`Target URL: ${DEPLOYMENT_URL}\n`);

  let browser;
  let passedChecks = 0;
  let failedChecks = 0;
  const checks = [];

  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    console.log('📱 Loading page...');
    await page.goto(DEPLOYMENT_URL, {
      waitUntil: 'networkidle2',
      timeout: TIMEOUT
    });

    console.log('✅ Page loaded successfully\n');

    // Check 1: Page title
    console.log('🔍 Running validation checks...\n');
    try {
      const title = await page.title();
      if (title) {
        checks.push({ name: 'Page Title', status: 'PASS', details: title });
        passedChecks++;
      } else {
        checks.push({ name: 'Page Title', status: 'FAIL', details: 'No title found' });
        failedChecks++;
      }
    } catch (error) {
      checks.push({ name: 'Page Title', status: 'FAIL', details: error.message });
      failedChecks++;
    }

    // Check 2: "Coming Soon" text is present
    try {
      await page.waitForSelector('text/Coming Soon', { timeout: 5000 });
      checks.push({ name: '"Coming Soon" Text', status: 'PASS', details: 'Found in page' });
      passedChecks++;
    } catch (error) {
      checks.push({ name: '"Coming Soon" Text', status: 'FAIL', details: 'Not found' });
      failedChecks++;
    }

    // Check 3: Expected Launch Date section exists
    try {
      await page.waitForSelector('text/Expected Launch Date', { timeout: 5000 });
      checks.push({ name: 'Expected Launch Date Section', status: 'PASS', details: 'Found in page' });
      passedChecks++;
    } catch (error) {
      checks.push({ name: 'Expected Launch Date Section', status: 'FAIL', details: 'Not found' });
      failedChecks++;
    }

    // Check 4: Dynamic date is displayed (should contain current year + possibly next year)
    try {
      const bodyText = await page.evaluate(() => document.body.textContent);
      const currentYear = new Date().getFullYear();
      const nextYear = currentYear + 1;

      if (bodyText.includes(currentYear.toString()) || bodyText.includes(nextYear.toString())) {
        const dateMatch = bodyText.match(/([A-Z][a-z]+ \d{1,2}, \d{4})/);
        const foundDate = dateMatch ? dateMatch[0] : 'Date format found';
        checks.push({ name: 'Dynamic Launch Date', status: 'PASS', details: foundDate });
        passedChecks++;
      } else {
        checks.push({ name: 'Dynamic Launch Date', status: 'FAIL', details: 'Date not found' });
        failedChecks++;
      }
    } catch (error) {
      checks.push({ name: 'Dynamic Launch Date', status: 'FAIL', details: error.message });
      failedChecks++;
    }

    // Check 5: Download links are NOT present
    try {
      const playStoreLinks = await page.$$('a[href*="play.google.com/store"]');
      const appStoreLinks = await page.$$('a[href*="apps.apple.com"]');

      if (playStoreLinks.length === 0 && appStoreLinks.length === 0) {
        checks.push({ name: 'Download Links Hidden', status: 'PASS', details: 'No app store links found' });
        passedChecks++;
      } else {
        checks.push({
          name: 'Download Links Hidden',
          status: 'FAIL',
          details: `Found ${playStoreLinks.length} Play Store and ${appStoreLinks.length} App Store links`
        });
        failedChecks++;
      }
    } catch (error) {
      checks.push({ name: 'Download Links Hidden', status: 'FAIL', details: error.message });
      failedChecks++;
    }

    // Check 6: "Learn More" button exists
    try {
      await page.waitForSelector('a[href="#how-it-works"]', { timeout: 5000 });
      checks.push({ name: '"Learn More" Button', status: 'PASS', details: 'Found and links to #how-it-works' });
      passedChecks++;
    } catch (error) {
      checks.push({ name: '"Learn More" Button', status: 'FAIL', details: 'Not found' });
      failedChecks++;
    }

    // Check 7: FAQ section exists
    try {
      await page.waitForSelector('text/Frequently Asked Questions', { timeout: 5000 });
      checks.push({ name: 'FAQ Section', status: 'PASS', details: 'Found in page' });
      passedChecks++;
    } catch (error) {
      checks.push({ name: 'FAQ Section', status: 'FAIL', details: 'Not found' });
      failedChecks++;
    }

    // Check 8: Support section with email
    try {
      const bodyText = await page.evaluate(() => document.body.textContent);
      if (bodyText.includes('bondwala@wizardsofts.com')) {
        checks.push({ name: 'Support Email', status: 'PASS', details: 'bondwala@wizardsofts.com found' });
        passedChecks++;
      } else {
        checks.push({ name: 'Support Email', status: 'FAIL', details: 'Email not found' });
        failedChecks++;
      }
    } catch (error) {
      checks.push({ name: 'Support Email', status: 'FAIL', details: error.message });
      failedChecks++;
    }

    // Take a screenshot
    const screenshotPath = '/tmp/bondwala-deployment-validation.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 Screenshot saved to: ${screenshotPath}\n`);

  } catch (error) {
    console.error('❌ Fatal error during validation:', error.message);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  // Print results
  console.log('📊 Validation Results');
  console.log('====================\n');

  checks.forEach(check => {
    const emoji = check.status === 'PASS' ? '✅' : '❌';
    console.log(`${emoji} ${check.name}: ${check.status}`);
    console.log(`   Details: ${check.details}\n`);
  });

  console.log('====================');
  console.log(`Total Checks: ${checks.length}`);
  console.log(`Passed: ${passedChecks} ✅`);
  console.log(`Failed: ${failedChecks} ❌`);
  console.log('====================\n');

  if (failedChecks > 0) {
    console.log('❌ Validation failed! Some checks did not pass.');
    process.exit(1);
  } else {
    console.log('✅ All validation checks passed!');
    console.log('🎉 BondWala deployment is verified and working correctly.');
    process.exit(0);
  }
}

// Run validation
validateBondWalaDeployment().catch(error => {
  console.error('Unexpected error:', error);
  process.exit(1);
});
