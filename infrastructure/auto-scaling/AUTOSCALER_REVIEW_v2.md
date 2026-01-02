## Autoscaler Review — v2 (concise)

Location: `/auto-scaling`

Purpose: quick re-evaluation after clarifications. This version is minimal and pragmatic (no overengineering). It focuses on the essential fixes needed to make the system match the PRD and plan while honouring your inputs: timezone must be configurable, you use `ngnix` as public reverse proxy (recommend keep it), and CI is not yet configured.

---

Top-level verdict
- The folder contains the expected components (FastAPI app, autoscaler logic, haproxy template, monitoring, scripts). With a few small, prioritized changes the implementation will meet the PRD for a 4-server local deployment.

Key assumptions taken for v2
- Scaling decisions: default to cluster-wide average CPU per service, unless you request otherwise.
- Placement policy: default is "least containers, then lowest CPU" to keep distribution even while avoiding control-plane overload.
- Timezone: configurable per deployment via a timezone string in `config.yaml` (e.g., `Asia/Dhaka`, `Australia/Melbourne`, `America/New_York`).
- Load balancing: keep `ngnix` as public reverse proxy and use HAProxy internally for autoscaler-managed services (recommended for minimal disruption).

Minimal prioritized checklist (v2) — implement these first

1) Config validation (small)
   - Add a lightweight Pydantic config model that validates required fields and types on startup and on `/config/reload`. Fail fast with clear error message. (File: `app/config_model.py`, small tests.)

2) Timezone-aware scheduler (small)
   - Make `scheduler.py` read a `timezone` field from `config.yaml` and evaluate business-hours windows in that timezone. Add a basic unit test to ensure DST/offset behavior uses `pytz` or `zoneinfo` correctly.

3) Health checks + HAProxy update (minimal reliable behavior)
   - Ensure autoscaler runs an HTTP probe per service (path + timeout in config). If a container fails probe for N checks, mark unhealthy and remove backend from HAProxy. Implement HAProxy reload as graceful soft-reload (atomic config write + `haproxy -f cfg -p pidfile -sf <oldpid>`). This avoids replacing public nginx configuration.

4) CI checklist (operational)
   - Mark CI as "not configured" in repo notes. Add a simple `.gitlab-ci.yml` lint job to the repo that runs `yamllint` and config validation so future CI config is easier. Do not enable deployments yet until credentials are present.

Low-effort extras (optional)
- Prometheus: ensure `prometheus.yml` scrapes the autoscaler metrics endpoint and cAdvisor on server IPs. Add one gauge/counter in `app/main.py` for container counts and scaling events.
- Add a README snippet explaining: timezone config, placement policy, and recommended production choice to keep `ngnix` public + HAProxy internal.

Notes / rationale
- These items are intentionally small and low-risk — they reduce operational surprises (bad config), ensure business-hours behave across timezones, make scaling decisions observable and safe, and keep public ingress unchanged (ngnix stays in front).

Next immediate action I can take for you (pick one)
- Implement the 4 minimal checklist items now and add unit tests and a short README snippet. I will not change public routing; HAProxy reload will be internal and graceful. After edits I'll run tests and follow the Codacy guidance described in the repo instructions.
- Or, I can create small PR patches for each checklist item so you can review before merge.

---

Saved as: `/auto-scaling/AUTOSCALER_REVIEW_v2.md`
