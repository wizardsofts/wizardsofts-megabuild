#!/usr/bin/env node

/**
 * Purge old contact submissions based on retention policy
 *
 * Usage:
 *   node scripts/purge-old-submissions.js [retentionDays]
 *
 * Default retention: 90 days
 *
 * This script should be run periodically via cron or CI/CD scheduler
 */

import { purgeOldSubmissions } from "../lib/contactRepo.js";

async function main() {
  const retentionDays = parseInt(process.argv[2]) || 90;

  console.log(`Starting purge of submissions older than ${retentionDays} days...`);

  try {
    const deletedCount = await purgeOldSubmissions(retentionDays);
    console.log(`Successfully deleted ${deletedCount} old submission(s)`);
    process.exit(0);
  } catch (error) {
    console.error("Error purging old submissions:", error);
    process.exit(1);
  }
}

main();
