# WizardSofts Megabuild - Future Scope & Roadmap

**Purpose:** Centralized index of all project roadmaps, planned features, and strategic initiatives across the WizardSofts ecosystem.

**Last Updated:** 2026-01-03

---

## Table of Contents

1. [GIBD (GreeNest Investment Bank of Dhaka)](#gibd-greenest-investment-bank-of-dhaka)
2. [WizardSofts Platform](#wizardsofts-platform)
3. [Infrastructure & DevOps](#infrastructure--devops)
4. [PadmaFoods](#padmafoods)
5. [Daily Deen](#daily-deen)
6. [Roadmap Summary](#roadmap-summary)

---

## GIBD (GreeNest Investment Bank of Dhaka)

### DivinerReturns - ML-Powered Stock Return Predictions

**Status:** ✅ Model Trained & API Ready | **Priority:** ⭐⭐⭐⭐⭐ High

**Brief:**
DivinerReturns is a quantile regression model that predicts 1-5 day stock returns with confidence intervals for 247 DSE (Dhaka Stock Exchange) stocks. The model achieves excellent backtest performance (5.53% RMSE, 75.39% coverage) and is ready for user-facing applications.

**Key Capabilities:**
- Multi-horizon predictions (1d, 2d, 3d, 4d, 5d)
- Confidence intervals (10th, 50th, 90th percentiles)
- REST API integration with existing FastAPI service
- CI/CD automated testing

**Next Logical Steps:**

| Phase | Feature | Timeline | Impact |
|-------|---------|----------|--------|
| **Phase 1** | Web Dashboard Stock Screener | 2-4 weeks | 🔥 High |
| **Phase 1** | Mobile Push Notifications | 1-2 weeks | 🔥 High |
| **Phase 2** | Portfolio Risk Analyzer | 3-4 weeks | 🔥 High |
| **Phase 3** | Paper Trading Mode | 4-6 weeks | 🔥 High |
| **Phase 4** | Prediction Tracking & Transparency | 1-2 weeks | 🔥 High |
| **Phase 5** | Multi-Model Ensemble | 12+ weeks | Medium |

**Full Roadmap:** [apps/gibd-quant-agent/docs/DIVINER_RETURNS_FUTURE_SCOPE.md](apps/gibd-quant-agent/docs/DIVINER_RETURNS_FUTURE_SCOPE.md)

**Technical Integration:**
- **Backend:** FastAPI endpoints already deployed (`/api/predict/returns`, `/api/predict/returns/batch`)
- **Frontend Target:** `gibd-quant-web` (Next.js)
- **Database:** PostgreSQL (Server 81) for prediction history
- **Orchestration:** Celery (Server 84) for daily updates

**Business Value:**
- Retail investor stock screening tool
- Portfolio risk management
- Trading strategy backtesting platform
- Potential premium subscription revenue

---

### TARP-DRL Portfolio Optimization

**Status:** ✅ Implementation Complete | **Priority:** ⭐⭐⭐⭐ High

**Brief:**
Time-Aware Reinforcement Learning with Predictive Integration for DSE portfolio optimization. Combines modified Diviner forecasts with PPO (Proximal Policy Optimization) agent using progressive reward curriculum (log returns → Sharpe → ICVaR).

**Key Capabilities:**
- 11-week implementation complete (~18,000 lines, 31 files)
- 70% code reuse from existing codebase
- Ray distributed training (Server 84: 9 nodes, 25 CPUs)
- Progressive curriculum (3 phases over 150 epochs)
- Dirichlet policy (automatic portfolio weight normalization)
- Comprehensive backtesting vs. 5 classical baselines

**Current Phase (Q1 2026):**
- [ ] Quick validation (5 epochs) - Today
- [ ] Full training (150 epochs) - Week 1
- [ ] Baseline comparison & statistical analysis - Week 1-2
- [ ] Hyperparameter tuning with Ray Tune - Week 3-4
- [ ] Ablation studies - Week 5-6

**Future Phases:**
- **Q2 2026:** Real-time portfolio management, paper trading mode
- **Q3 2026:** DivinerReturns dashboard integration, premium subscriptions
- **Q4 2026:** Auto-trading (regulatory approval required), GPU acceleration

**Full Roadmap:** [apps/gibd-quant-agent/docs/TARP_DRL_FUTURE_SCOPE.md](apps/gibd-quant-agent/docs/TARP_DRL_FUTURE_SCOPE.md)

**Technical Components:**
- **Data Pipeline:** PostgreSQL (ws_dse_daily_prices), 40 indicators, 20 time features
- **Forecasting:** Modified Diviner (80% code reuse)
- **RL Agent:** PPO with time-aware attention, Dirichlet policy
- **Environment:** Gymnasium-compatible with DSE constraints (±10% circuit breakers)
- **Baselines:** Equal-Weight, Markowitz, HRP, Black-Litterman, MinVar

**Research Success Criteria:**
- Sharpe ratio > 1.2 (20% better than best baseline)
- Max drawdown < 25%
- Statistical significance (p < 0.05)

**Business Value:**
- Premium subscription feature ($20/month)
- Portfolio optimization-as-a-service
- Automated rebalancing for retail investors
- Integration with existing DivinerReturns dashboard

---

### DivinerDirection - Stock Price Movement Classification

**Status:** 🚧 Model Trained, API Pending | **Priority:** ⭐⭐⭐ Medium

**Brief:**
Classification model predicting UP/DOWN/NEUTRAL price movements. Can be combined with DivinerReturns for ensemble predictions.

**Next Steps:**
- [ ] Add API endpoints to existing FastAPI service
- [ ] Integrate with DivinerReturns for ensemble recommendations
- [ ] Create combined confidence scoring system

---

### GIBD-News - News Scraping & Sentiment Analysis

**Status:** ✅ Production | **Priority:** ⭐⭐ Low

**Current Deployment:**
- Prometheus metrics exporters (Server 84)
- Automated news scrapers for DSE stocks

**Future Enhancements:**
- [ ] Sentiment analysis using LLMs (Ollama integration)
- [ ] News impact on stock predictions correlation
- [ ] Real-time alert system for market-moving news

---

### GIBD-Quant Services Ecosystem

**Components:**
- `gibd-quant-signal` - Technical indicators service
- `gibd-quant-nlq` - Natural language query service
- `gibd-quant-calibration` - Model calibration service
- `gibd-quant-celery` - Task orchestration

**Future Integration:**
- [ ] Unified prediction API combining all models
- [ ] Real-time data streaming from DSE
- [ ] Backtesting-as-a-Service platform
- [ ] API marketplace for quant strategies

---

## WizardSofts Platform

### Core Microservices

| Service | Status | Priority | Future Scope |
|---------|--------|----------|--------------|
| **ws-gateway** | ✅ Production | ⭐⭐⭐⭐⭐ | OAuth2 integration (Keycloak), rate limiting, circuit breakers |
| **ws-discovery** | ✅ Production | ⭐⭐⭐ | Health check dashboard, auto-scaling triggers |
| **ws-company** | ✅ Production | ⭐⭐ | Advanced search, company relationships graph |
| **ws-trades** | ✅ Production | ⭐⭐⭐ | Real-time trade notifications, trade analytics |
| **ws-news** | ✅ Production | ⭐⭐ | Content recommendation engine |

**Platform-Wide Initiatives:**
- [ ] Complete OAuth2/OIDC implementation (ws-gateway + Keycloak)
- [ ] Distributed tracing (Jaeger integration)
- [ ] GraphQL federation across services
- [ ] API versioning strategy

**Documentation:** [docs/WS_GATEWAY_HANDOFF.md](docs/WS_GATEWAY_HANDOFF.md)

---

### Frontend Applications

| Application | Status | Priority | Future Scope |
|-------------|--------|----------|--------------|
| **gibd-quant-web** | ✅ Production | ⭐⭐⭐⭐⭐ | DivinerReturns dashboard, portfolio analytics, social trading |
| **ws-wizardsofts-web** | ✅ Production | ⭐⭐⭐ | User profile system, notification center |
| **ws-daily-deen-web** | ✅ Production | ⭐⭐ | Prayer time widgets, Islamic content library |
| **pf-padmafoods-web** | 🚧 Development | ⭐⭐⭐ | E-commerce features, inventory management |

---

## Infrastructure & DevOps

### Distributed ML Infrastructure (Server 84)

**Status:** ✅ Production (Phase 1 & 2 Complete)

**Current Capabilities:**
- Ray cluster (9 nodes, 25 CPUs)
- Celery task queue (10 workers)
- Redis coordination
- Flower monitoring

**Future Enhancements:**
- [ ] GPU node integration for deep learning
- [ ] Auto-scaling based on workload
- [ ] Multi-tenant ML resource allocation
- [ ] Model serving with Ray Serve

### vLLM + Ray Serve for Distributed LLM Inference

**Status:** 📋 Planned | **Priority:** ⭐⭐⭐⭐ High

**Brief:**
Replace Ollama with vLLM for distributed LLM inference, leveraging the existing Ray cluster for auto-scaling. vLLM has native Ray integration and supports tensor/pipeline parallelism across multiple GPUs and nodes.

**Current Limitation:**
- Ollama runs single-threaded on one server (bottleneck for parallel extraction)
- Entity extraction for 50 hadiths took 9+ minutes with 14 Ray workers waiting on Ollama

**Proposed Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Ray Cluster (Existing)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Server 80│  │Server 81│  │Server 82│  │Server 84│        │
│  │ Worker  │  │ Worker  │  │ Worker  │  │  Head   │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                          │                                   │
│              ┌───────────▼───────────┐                      │
│              │     Ray Serve         │                      │
│              │  (Auto-scaling LLM)   │                      │
│              └───────────┬───────────┘                      │
│                          │                                   │
│              ┌───────────▼───────────┐                      │
│              │        vLLM           │                      │
│              │  Tensor Parallelism   │                      │
│              │  Pipeline Parallelism │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits:**
| Feature | Ollama (Current) | vLLM + Ray Serve |
|---------|------------------|------------------|
| Parallelism | Single instance | Multi-node distributed |
| Auto-scaling | Manual | Automatic based on load |
| GPU Utilization | Single GPU | Tensor parallel across GPUs |
| Ray Integration | None | Native |
| Throughput | ~5 req/min | 50+ req/min (estimated) |

**Implementation Steps:**
1. Install vLLM on Ray cluster nodes
2. Configure Ray Serve deployment for LLM inference
3. Update entity extraction code to use vLLM API
4. Enable auto-scaling based on request queue depth
5. Add Prometheus metrics for inference monitoring

**Example Configuration:**
```python
from vllm import LLM
from ray import serve

@serve.deployment(
    ray_actor_options={"num_gpus": 1},
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 4,
        "target_num_ongoing_requests_per_replica": 5,
    }
)
class LLMDeployment:
    def __init__(self):
        self.llm = LLM(model="mistralai/Mistral-7B-v0.1")

    async def __call__(self, request):
        return self.llm.generate(request.prompt)
```

**Resources:**
- [vLLM Distributed Serving](https://docs.vllm.ai/en/stable/serving/distributed_serving.html)
- [Ray Serve LLM Integration](https://docs.ray.io/en/latest/serve/tutorials/vllm-example.html)
- [Ray Data LLM Module](https://docs.ray.io/en/latest/data/working-with-llms.html)

**Documentation:**
- [infrastructure/distributed-ml/README.md](infrastructure/distributed-ml/README.md)
- [docs/PHASE2_CELERY_VALIDATION_REPORT.md](docs/PHASE2_CELERY_VALIDATION_REPORT.md)

---

### GitLab CI/CD Enhancements

**Status:** ✅ Production | **Priority:** ⭐⭐⭐⭐ High

**Current State:**
- Automated testing for all services
- Docker image builds
- Multi-stage deployments
- Security scanning

**Future Improvements:**
- [ ] Automated security dependency updates
- [ ] Performance benchmarking in CI
- [ ] Blue-green deployment strategy
- [ ] Automated rollback on failure
- [ ] Cost optimization (reduce build times)

---

### Monitoring & Observability

**Status:** ✅ Production | **Priority:** ⭐⭐⭐⭐ High

**Current Stack:**
- Prometheus (metrics collection)
- Grafana (dashboards)
- Alertmanager (notifications)
- fail2ban (intrusion prevention)

**Future Enhancements:**
- [ ] Centralized logging (ELK/Loki)
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] Application Performance Monitoring (APM)
- [ ] ML-based anomaly detection
- [ ] Cost tracking dashboard

**Recent Additions:**
- ✅ Server 82 metrics exporters deployed (2025-12-31)
- ✅ fail2ban security on Server 84 (2026-01-01)

**Documentation:** [docs/SECURITY_MONITORING.md](docs/SECURITY_MONITORING.md)

---

### Security & Compliance

**Status:** 🔒 Hardened | **Priority:** ⭐⭐⭐⭐⭐ Critical

**Recent Security Improvements (2025-12-31):**
- ✅ Next.js updated to 15.5.7 (CVE-2025-66478 patched)
- ✅ Rate limiting on all FastAPI services
- ✅ Input validation (SQL injection, path traversal)
- ✅ API key authentication for write operations
- ✅ Container hardening (no-new-privileges, memory limits)
- ✅ fail2ban intrusion prevention (Server 84)

**Future Security Initiatives:**
- [ ] Deploy fail2ban to all servers (80, 81, 82)
- [ ] Web Application Firewall (WAF) with ModSecurity
- [ ] Secrets rotation automation (Vault integration)
- [ ] SIEM (Security Information and Event Management)
- [ ] Compliance audit trail (GDPR, SOC 2)
- [ ] Penetration testing automation

**Documentation:** [docs/SECURITY_IMPROVEMENTS_CHANGELOG.md](docs/SECURITY_IMPROVEMENTS_CHANGELOG.md)

---

## PadmaFoods

**Status:** 🚧 Development | **Priority:** ⭐⭐⭐ Medium

**Application:** `pf-padmafoods-web` (Next.js)

**Future Scope:**
- [ ] E-commerce platform (product catalog, shopping cart)
- [ ] Inventory management system
- [ ] Order tracking and fulfillment
- [ ] Customer loyalty program
- [ ] Mobile app (React Native)
- [ ] Integration with payment gateways (bKash, Nagad)

---

## Daily Deen

**Status:** ✅ Production | **Priority:** ⭐⭐ Low

**Application:** `ws-daily-deen-web` (Next.js)

### Hadith Knowledge Graph

**Status:** ✅ Infrastructure Deployed | **Priority:** ⭐⭐⭐ Medium

**Current State:**
- Neo4j graph database (Server 84)
- ChromaDB vector store (Server 84)
- CI/CD deployment pipeline

**Future Development:**
- [ ] Hadith ingestion pipeline (Bukhari, Muslim, Abu Dawud, etc.)
- [ ] Semantic search with embeddings
- [ ] Hadith chain (Isnad) visualization
- [ ] Narrator reliability scoring
- [ ] Cross-reference detection
- [ ] Mobile app integration

**Documentation:** [apps/hadith-knowledge-graph/README.md](apps/hadith-knowledge-graph/README.md)

---

### Islamic Content Features

**Future Enhancements:**
- [ ] Prayer time widgets with location services
- [ ] Quran recitation with translations
- [ ] Islamic calendar and events
- [ ] Mosque finder with prayer times
- [ ] Daily Hadith notifications

---

## Roadmap Summary

### Q1 2026 (Jan-Mar) - Immediate Priorities

| Initiative | Team | Timeline | Status |
|------------|------|----------|--------|
| **DivinerReturns Web Dashboard** | GIBD Quant | 4 weeks | 🟡 Planning |
| **ws-gateway OAuth2 Completion** | Platform | 2 weeks | 🟡 Pending |
| **Security Hardening (fail2ban rollout)** | DevOps | 1 week | 🟢 In Progress |
| **Hadith Knowledge Graph Data Ingestion** | Daily Deen | 6 weeks | 🔴 Not Started |
| **PadmaFoods E-commerce MVP** | PadmaFoods | 8 weeks | 🔴 Not Started |

### Q2 2026 (Apr-Jun) - Growth Phase

| Initiative | Team | Timeline |
|------------|------|----------|
| **DivinerReturns Portfolio Analytics** | GIBD Quant | 4 weeks |
| **Multi-Model Ensemble (DivinerReturns + DivinerDirection)** | GIBD Quant | 8 weeks |
| **Distributed Tracing Rollout** | Platform | 6 weeks |
| **Mobile Apps (React Native)** | All Teams | 12 weeks |
| **API Marketplace Beta** | Platform | 10 weeks |

### Q3-Q4 2026 - Scale & Innovation

- **DivinerReturns Paper Trading & Auto-Trading** (regulatory approval required)
- **GPU Cluster for Deep Learning** (Server 84 expansion)
- **International Market Expansion** (beyond DSE)
- **Enterprise Features** (white-labeling, custom deployments)

---

## Contributing to Future Scope

**Process:**
1. Create detailed future scope document in your service's `docs/` directory
2. Update this global index with a brief summary and link
3. Assign priority (⭐-⭐⭐⭐⭐⭐) and status (🔴 Not Started, 🟡 Planning, 🟢 In Progress, ✅ Complete)
4. Create GitLab issues for tracking individual tasks
5. Update roadmap quarterly based on business priorities

**Template:** See [apps/gibd-quant-agent/docs/DIVINER_RETURNS_FUTURE_SCOPE.md](apps/gibd-quant-agent/docs/DIVINER_RETURNS_FUTURE_SCOPE.md) for reference structure.

---

## Strategic Priorities

### 2026 Focus Areas

1. **Revenue Generation** 🎯
   - DivinerReturns premium subscriptions
   - API marketplace
   - PadmaFoods e-commerce

2. **User Growth** 📈
   - Mobile apps across all platforms
   - Social trading features
   - Content recommendation engines

3. **Platform Maturity** 🏗️
   - Complete OAuth2/OIDC rollout
   - Distributed tracing
   - Advanced monitoring & alerting

4. **Innovation** 💡
   - Multi-model ML ensembles
   - Knowledge graphs (Hadith, Company relationships)
   - Real-time data streaming

---

**Document Maintainer:** Architecture Team
**Review Frequency:** Quarterly
**Next Review:** 2026-04-01
