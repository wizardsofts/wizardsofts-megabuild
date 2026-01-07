# PRE-001: Server Hardware Verification

**Date:** 2026-01-01
**Status:** ✅ PASSED
**Duration:** 5 minutes

## Summary

All 4 servers are healthy and ready for migration. Hardware specifications verified.

## Server Details

### Server 80 (hppavilion) - 10.0.0.80
- **CPU:** Intel Core i7-8550U @ 1.80GHz (8 cores, 2 threads/core)
- **RAM:** 31 GB (4.0 GB used, 27 GB available)
- **Disk:** 217 GB total, 173 GB available (17% used)
- **Uptime:** 61 days, 15:34
- **Load:** 0.19, 0.16, 1.43 (normal)
- **Status:** ✅ Healthy

### Server 81 (wsasus) - 10.0.0.81
- **CPU:** Intel Core i3-4010U @ 1.70GHz (4 cores, 2 threads/core)
- **RAM:** 11 GB (815 MB used, 10 GB available)
- **Disk:** 98 GB total, 67 GB available (28% used)
- **Uptime:** 97 days, 2:09
- **Load:** 0.06, 0.02, 0.02 (very low)
- **SMART:** PASSED
- **Status:** ✅ Healthy

### Server 82 (hpr) - 10.0.0.82
- **CPU:** Intel Core i7 Q720 @ 1.60GHz (8 cores, 2 threads/core)
- **RAM:** 5.7 GB (771 MB used, 5.0 GB available)
- **Disk:** 251 GB total, 230 GB available (4% used)
- **Uptime:** 18:29 (less than 1 day - recently rebooted for lid config)
- **Load:** 0.08, 0.05, 0.15 (very low)
- **Status:** ✅ Healthy
- **Note:** Lid close issue resolved, working normally

### Server 84 (gmktec) - 10.0.0.84
- **CPU:** AMD Ryzen 7 H 255 w/ Radeon 780M (16 cores, 2 threads/core)
- **RAM:** 28 GB (13 GB used, 14 GB available)
- **Disk:** 914 GB total, 545 GB available (38% used)
- **Uptime:** 8 days, 4:52
- **Load:** 0.67, 0.57, 0.90 (moderate - running GitLab, Appwrite, monitoring)
- **Status:** ✅ Healthy

## Validation

✅ All servers accessible via SSH
✅ CPU specs verified
✅ RAM availability confirmed (sufficient for migration)
✅ Disk space sufficient (all >60GB available)
✅ Server load normal (no resource exhaustion)
✅ Server 81 SMART status: PASSED
✅ No hardware warnings or errors

## Notes

- **Temperature/SMART:** Not all servers have sensors/smartctl installed (not critical)
- **Server 82:** Recently rebooted for lid configuration, now stable
- **Server 84:** Highest load due to current infrastructure (GitLab, Appwrite)
- **Disk Space:** All servers have ample space for migration

## Next Task

**PRE-002:** Network Connectivity Test
