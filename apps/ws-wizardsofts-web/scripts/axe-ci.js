#!/usr/bin/env node

/**
 * Axe accessibility CI check script
 *
 * This script runs axe-core accessibility tests on key pages
 * and fails if critical violations are found.
 */

import { AxePuppeteer } from "@axe-core/puppeteer";
import puppeteer from "puppeteer";

const PAGES_TO_TEST = [
  { name: "Home", url: "http://localhost:3000" },
  { name: "Services", url: "http://localhost:3000/services" },
  { name: "Contact", url: "http://localhost:3000/contact" },
];

async function runAxeTests() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  let hasErrors = false;
  const results = [];

  for (const page of PAGES_TO_TEST) {
    console.log(`\nTesting ${page.name} (${page.url})...`);

    const browserPage = await browser.newPage();

    try {
      await browserPage.goto(page.url, { waitUntil: "networkidle2" });

      const axeResults = await new AxePuppeteer(browserPage).analyze();

      const criticalViolations = axeResults.violations.filter((v) => v.impact === "critical");
      const seriousViolations = axeResults.violations.filter((v) => v.impact === "serious");

      results.push({
        page: page.name,
        violations: axeResults.violations.length,
        critical: criticalViolations.length,
        serious: seriousViolations.length,
      });

      console.log(`  Total violations: ${axeResults.violations.length}`);
      console.log(`  Critical: ${criticalViolations.length}`);
      console.log(`  Serious: ${seriousViolations.length}`);

      if (criticalViolations.length > 0) {
        hasErrors = true;
        console.error("\n  Critical violations found:");
        criticalViolations.forEach((violation) => {
          console.error(`    - ${violation.description}`);
          console.error(`      Help: ${violation.helpUrl}`);
        });
      }
    } catch (error) {
      console.error(`  Error testing ${page.name}:`, error.message);
      hasErrors = true;
    } finally {
      await browserPage.close();
    }
  }

  await browser.close();

  // Print summary
  console.log("\n=== Accessibility Test Summary ===");
  results.forEach((result) => {
    console.log(
      `${result.page}: ${result.violations} violations (${result.critical} critical, ${result.serious} serious)`
    );
  });

  if (hasErrors) {
    console.error("\n❌ Accessibility tests failed. Critical violations found.");
    process.exit(1);
  } else {
    console.log("\n✅ Accessibility tests passed. No critical violations found.");
    process.exit(0);
  }
}

runAxeTests().catch((error) => {
  console.error("Fatal error running axe tests:", error);
  process.exit(1);
});
