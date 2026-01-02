## Autoscaler Codebase Review

Location: `/auto-scaling`

Goal: compare the implementation and files in this folder against the PRD (`prd.md`) and Implementation Plan (`plan.md`) and surface gaps, ambiguities, and improvement opportunities. Provide prioritized, actionable fixes and quick next steps.

---

### Summary

The repository contains a mostly complete control-plane scaffold for the small-scale autoscaling platform described in `prd.md` and `plan.md`. Key artifacts exist: FastAPI app (`app/main.py`), scaling logic (`app/autoscaler.py`), docker manager, HAProxy config, Prometheus/Grafana configs, helper scripts, and Dockerfiles. Overall structure matches the PRD and Plan, but there are gaps, configuration discrepancies, and opportunities to harden the system for reliability, security, and maintainability.

This review lists: (A) Gaps / mismatches vs PRD & Plan, (B) Confusions and ambiguous areas, (C) Improvements and quick wins (prioritized), and (D) Suggested next steps and small automated checks.

### A. Gaps and mismatches (PRD / Plan → code)

1) Config parity and validation
   - `config.yaml` exists but appears to be a template and may not contain all fields shown in `prd.md` (e.g. per-service `business_hours_only`, `cooldown_period`, `volumes`, `environment`). The PRD requires a single source-of-truth with validation.
   - No explicit config schema (Pydantic model / JSON Schema) or validation routine found. Without validation, malformed configs will break runtime behavior.

2) Business-hours enforcement
   - PRD requires business-hours-only scaling (09:00–17:00 UTC by default). There is `scheduler.py` in `app/` but it must be checked to ensure it implements timezone-aware windows and respects `business_hours_only` per-service. NOTE: business-hours should be configurable per-deployment and support different timezones (e.g., Dhaka, Melbourne, USA zones) — the control plane must accept a timezone string in the config and evaluate windows accordingly.

3) HAProxy dynamic backend updates
   - `haproxy_manager.py` exists. Ensure it updates backend server entries atomically and triggers HAProxy reload gracefully. The `haproxy/haproxy.cfg` must be a template with placeholders; confirm autoscaler writes valid server entries and runs soft reload (e.g., `service haproxy reload` or `haproxy -f ... -p ... -sf $(cat /var/run/haproxy.pid)`).

4) Health checks and removal of unhealthy containers
   - PRD requires health checks every 10s and auto-removal of unhealthy containers. The codebase includes `health_check.sh` and some health logic, but there is no centralized health-checker service evident; the autoscaler must subscribe to health results (via cAdvisor/Prometheus or direct HTTP checks).

5) Monitoring integrations
   - Prometheus config exists but needs scrape targets for cAdvisor on each server and for autoscaler metrics. Confirm `monitoring/prometheus/prometheus.yml` includes those jobs.
   - Grafana dashboard JSONs are present. Verify they match metric names produced by the app.

   Note: user indicated they already use `ngnix` as the public reverse proxy for hosted domains. We should decide whether to keep `ngnix` for public routing and continue using HAProxy only internally for autoscaling, or switch to HAProxy as the public-facing load balancer. Both are possible:

   - Keep nginx public reverse proxy and run HAProxy as an internal L4/L7 balancer for autoscaled services (recommended for minimal public-facing change).
   - Or replace nginx with HAProxy for both public and autoscaling responsibilities (simpler single LB but requires DNS / TLS migration).

   Recommendation: keep `ngnix` for public reverse proxy and use HAProxy internally for autoscaler-managed backends unless you want to consolidate to a single load balancer. Update design decision in docs.

6) CI/CD pipeline completeness
   - `.gitlab-ci.yml` exists in `/auto-scaling` and in root. The plan expects GitLab to push new images and call autoscaler API for rolling updates. Confirm the image tagging, registry credentials, and SSH private keys handling conform to security best practices (masked variables, protected branches).
   - Note: you said CI is "not configured". The repo contains CI pipeline templates but no verified setup in your GitLab instance; completing CI configuration is required before automated deployments will work.

7) Container naming and limits
   - PRD: min 1 replica, max 3 per service per server (max replicas per service global). Code must enforce these constraints; verify logic in `autoscaler.py` respects per-service `min_replicas`/`max_replicas` and `servers[].max_containers`.

8) Backups and retention
   - `scripts/backup.sh` exists but must be validated for scheduling and that backup targets exist (e.g., `/opt/autoscaler/config.yaml` path). PRD expects daily backups and retention; ensure cron installs properly.

9) Systemd service / auto-start
   - `setup_systemd_service.sh` exists and plan includes a systemd unit. Verify path assumptions for `docker-compose` and `USER` substitution; prefer using absolute paths and a dedicated service user.

10) Secrets handling
   - PRD suggests storing secrets in GitLab CI variables. Code should not contain plaintext secrets. Confirm no secrets are hard-coded in repository (e.g., Grafana admin password in `monitoring/grafana` files).

11) Documentation parity
   - `QUICKREF.md`, `DEPLOYMENT_CHECKLIST.md`, and `README.md` may be present, but quick-start steps differ slightly between `plan.md` and repository helper scripts. Ensure the user flows are consistent.


### B. Confusions and ambiguous areas

1) Timezone handling: PRD uses `UTC` example; plan suggests user timezone edits. The code must clearly document and validate timezone names. Ambiguity: Are business hours local to control server or per-server timezone?

2) Scaling triggers: PRD states CPU avg >75% across what scope? Per-container, per-server, or cluster-wide? The implementation should clarify which metric triggers scale decisions and how it's aggregated (mean/median/percentile).

3) Placement strategy: How do we choose which server to start a new container on? The PRD implies even distribution; code should describe tie-breakers (free slots, least CPU, prefer non-control servers).

4) Update/rolling-update semantics: Plan uses simple `curl` API to trigger rolling updates. It's unclear whether rolling updates are image-pull + restart or new containers launched and old removed; need explicit behavior and health-check gating.

5) Max replicas semantics: PRD has global max and per-server max. Clarify mapping and enforcement details.


### C. Improvements and quick wins (prioritized)

P0 — Must-fix / High priority

- Add config schema and validation using Pydantic models (app/config_model.py). Validate `config.yaml` at startup and on reload. Fail fast with clear error messages.
- Implement and verify timezone-aware business-hours gating in `scheduler.py`. Add unit tests.
- Ensure autoscaler respects min/max replica limits and per-server container capacity.
- Add a health-check worker (or ensure autoscaler runs HTTP probes) that removes unhealthy containers and updates HAProxy immediately.
- Make HAProxy reloads safe (use `-sf` for master process) and update `haproxy_manager.py` to write temp file + atomic move + graceful reload.

P1 — Medium priority

- Harden CI pipeline: Use protected variables, avoid echoing secrets in logs, and verify `.gitlab-ci.yml` uses masked variables. Add a job that lints `config.yaml` and runs unit tests.
- Add Prometheus scrape configs for autoscaler and cAdvisor targets. Ensure metrics endpoints are instrumented in the FastAPI app (Prometheus client).
- Implement basic RBAC for autoscaler API (token-based) to avoid open endpoints.

P2 — Nice-to-have

- Add automated integration tests (small harness) that spin up containers and assert scaling decisions.
- Add logging rotation and structured logs (JSON) for better observability.
- Provide example systemd unit template with variables replaced by `envsubst` during setup.


### D. Suggested next steps (actionable)

1) Create a small branch and implement config model + validation. Files to add/modify:
   - `app/config_model.py` (Pydantic models)
   - `app/main.py` to load and validate `config.yaml` on startup and `/config/reload` endpoint
   - Add unit tests under `tests/test_config.py`

2) Verify `autoscaler.py` enforces cooldown and per-service cooldown_periods. Add tests for throttling behavior.

3) Add Prometheus metrics in `app/main.py` and `app/autoscaler.py` using `prometheus_client` (counters/gauges for scaling events and container counts).

4) Review `.gitlab-ci.yml` for secure handling of `SSH_PRIVATE_KEY` (masked/protected). Add a lint job to run `yamllint` and `ruff`/`black`.

5) Add a README note and `QUICKREF.md` update clarifying timezone behavior and scaling aggregation logic.


---

### Files inspected

From `/auto-scaling`:
- `app/` (main.py, autoscaler.py, docker_manager.py, haproxy_manager.py, Dockerfile, requirements.txt, scheduler.py)
- `haproxy/haproxy.cfg`
- `monitoring/` (prometheus.yml, grafana dashboards)
- `scripts/` (setup.sh, backup.sh, health_check.sh)
- `docker-compose.yml`
- `config.yaml` (template)
- CI and deployment helpers: `deploy_control_plane.sh`, `deploy_ollama.sh`, `.gitlab-ci.yml`, `setup_systemd_service.sh`


### Quick checklist to close gaps

- [ ] Add config schema + validation (P0)
- [ ] Implement/verify business-hours timezone-aware gating (P0)
- [ ] Ensure HAProxy updates are atomic and graceful (P0)
- [ ] Add/verify health-check worker and auto-removal (P0)
- [ ] Add Prometheus scrape jobs for autoscaler and cAdvisor (P1)
- [ ] Harden CI for secrets and linting (P1)
- [ ] Create unit tests for core autoscaler logic and config (P1)
- [ ] Ensure documentation updates reflect reality (plan & PRD parity)


---

### Notes about Codacy analysis (repo instructions)

Per repository instructions in `.github/instructions/codacy.instructions.md`, after any file edits we must run the Codacy MCP `codacy_cli_analyze` tool for changed files. If the Codacy CLI is not installed, follow the guidance in that instruction file before proceeding. If you want, I can implement the config validation and tests now and run the required analysis. Let me know if you'd like me to proceed with code changes.

---

Prepared by: automated review (actionable checklist provided). If you want, I can open a branch and start implementing the P0 fixes now (config model + validation + tests).
