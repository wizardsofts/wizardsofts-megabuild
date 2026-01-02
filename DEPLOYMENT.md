# Deployment Guide - Wizardsofts Megabuild

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL databases created:
  - `ws_gibd_dse_daily_trades`
  - `ws_gibd_dse_company_info`
- Environment variables configured (see below)

### Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```bash
   # Required
   DB_PASSWORD=your_actual_password

   # Optional (for NLQ and Agent services)
   OPENAI_API_KEY=sk-your-key

   # Optional (for analytics)
   GA_MEASUREMENT_ID=G-XXXXXXXXXX
   ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
   ```

## Deployment Profiles

The monorepo uses Docker Compose profiles for flexible deployment:

### Profile: `shared` (Shared Infrastructure)

Deploys core infrastructure services:
- ws-discovery (Eureka) - Port 8761
- ws-gateway (API Gateway) - Port 8080
- ws-trades (Data API) - Port 8182
- ws-company (Company API) - Port 8183
- ws-news (News API) - Port 8184
- postgres - Port 5432
- redis - Port 6379

```bash
docker-compose --profile shared up -d
```

**Use case**: Deploy shared services that multiple projects can use.

### Profile: `gibd-quant` (GIBD Quant-Flow Ecosystem)

Deploys all shared services + GIBD-specific Quant-Flow services:
- All `shared` profile services (above)
- gibd-quant-signal - Port 5001
- gibd-quant-nlq - Port 5002
- gibd-quant-calibration - Port 5003
- gibd-quant-agent - Port 5004
- gibd-quant-celery (background worker)
- gibd-quant-web (frontend) - Port 3001

```bash
docker-compose --profile gibd-quant up -d
```

**Use case**: Complete GIBD Quant-Flow trading analysis platform.

### Profile: `all` (Everything)

Deploys all services in the monorepo.

```bash
docker-compose --profile all up -d
```

## Testing Checklist

### 1. Infrastructure Services

#### Start Services
```bash
docker-compose --profile gibd-quant up -d
```

#### Verify Eureka Dashboard
```bash
# Open browser
open http://localhost:8761

# Should show all registered services:
# - ws-gateway
# - ws-trades
# - ws-company
# - ws-news
# - gibd-quant-signal
# - gibd-quant-nlq
# - gibd-quant-calibration
# - gibd-quant-agent
```

#### Check Service Health
```bash
# Discovery service
curl http://localhost:8761/actuator/health

# Gateway service
curl http://localhost:8080/actuator/health

# Spring Boot data services
curl http://localhost:8182/actuator/health  # ws-trades
curl http://localhost:8183/actuator/health  # ws-company
curl http://localhost:8184/actuator/health  # ws-news

# Python ML services
curl http://localhost:5001/health  # gibd-quant-signal
curl http://localhost:5002/health  # gibd-quant-nlq
curl http://localhost:5003/health  # gibd-quant-calibration
curl http://localhost:5004/health  # gibd-quant-agent
```

### 2. Gateway Routing Tests

#### Test Signal Generation via Gateway
```bash
curl -X POST http://localhost:8080/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"ticker": "GP"}'
```

#### Test NLQ via Gateway
```bash
curl -X POST http://localhost:8080/api/nlq/query \
  -H "Content-Type: application/json" \
  -d '{"query": "stocks with RSI above 70", "limit": 10}'
```

#### Test Calibration via Gateway
```bash
curl -X POST http://localhost:8080/api/calibrate/GP
```

### 3. Frontend Integration Test

#### Access Frontend
```bash
open http://localhost:3001
```

#### Manual Testing Checklist
- [ ] Fixed header visible at top
- [ ] Fixed footer visible at bottom
- [ ] Header stays fixed while scrolling
- [ ] Footer stays fixed while scrolling
- [ ] Navigation links work
- [ ] Google Analytics script loads (check Network tab)
- [ ] Click tracking works (check browser console for gtag events)
- [ ] Ticker search works
- [ ] Signal generation returns results
- [ ] NLQ queries return results
- [ ] No console errors

### 4. Playwright Automated Tests

#### Install Playwright (if not installed)
```bash
cd tests/e2e
npm install
npx playwright install
```

#### Run All E2E Tests
```bash
npx playwright test
```

#### Run Specific Tests
```bash
# Test Eureka dashboard
npx playwright test tests/e2e/eureka.spec.ts

# Test frontend
npx playwright test tests/e2e/frontend.spec.ts

# Test analytics
npx playwright test tests/e2e/analytics.spec.ts

# Test API routing
npx playwright test tests/e2e/api-routing.spec.ts
```

#### View Test Report
```bash
npx playwright show-report
```

## Monitoring and Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gibd-quant-signal

# Last 100 lines
docker-compose logs --tail=100 gibd-quant-nlq
```

### Restart Service

```bash
docker-compose restart gibd-quant-signal
```

### Stop All Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

## Troubleshooting

### Service Not Registering with Eureka

1. Check Eureka server is running:
   ```bash
   curl http://localhost:8761/actuator/health
   ```

2. Check service logs for Eureka connection errors:
   ```bash
   docker-compose logs gibd-quant-signal | grep -i eureka
   ```

3. Verify EUREKA_SERVER environment variable is correct:
   ```bash
   docker-compose exec gibd-quant-signal env | grep EUREKA
   ```

### Gateway Not Routing to Service

1. Verify service is registered in Eureka dashboard
2. Check gateway logs:
   ```bash
   docker-compose logs ws-gateway
   ```
3. Test direct service endpoint (bypass gateway):
   ```bash
   curl http://localhost:5001/health
   ```

### Database Connection Issues

1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Test database connection:
   ```bash
   docker-compose exec postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "SELECT 1;"
   ```

3. Verify DATABASE_URL environment variable:
   ```bash
   docker-compose exec gibd-quant-signal env | grep DATABASE_URL
   ```

### Frontend Can't Connect to API

1. Verify Gateway is running and healthy
2. Check NEXT_PUBLIC_API_URL in frontend container:
   ```bash
   docker-compose exec gibd-quant-web env | grep NEXT_PUBLIC_API_URL
   ```
3. Test API from host machine:
   ```bash
   curl http://localhost:8080/api/signals/generate \
     -H "Content-Type: application/json" \
     -d '{"ticker": "GP"}'
   ```

## Production Deployment

### Security Considerations

1. **Change default credentials**:
   - PostgreSQL password
   - Redis (add password if exposing externally)

2. **Update CORS settings**:
   - Edit `apps/ws-gateway/src/main/resources/application.properties`
   - Set specific allowed origins instead of `*`

3. **Use HTTPS**:
   - Add reverse proxy (nginx, traefik) with SSL certificates
   - Update NEXT_PUBLIC_API_URL to HTTPS endpoint

4. **Environment variables**:
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Never commit .env file to git

### Performance Optimization

1. **Resource limits**:
   Add to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
       reservations:
         cpus: '1'
         memory: 1G
   ```

2. **Scaling**:
   ```bash
   docker-compose up -d --scale gibd-quant-signal=3
   ```

3. **Database optimization**:
   - Add connection pooling
   - Create indexes on frequently queried columns
   - Configure PostgreSQL memory settings

### Monitoring

Consider adding:
- Prometheus + Grafana for metrics
- ELK stack (Elasticsearch, Logstash, Kibana) for logs
- Zipkin or Jaeger for distributed tracing

## Support

For issues, check:
1. Service logs: `docker-compose logs [service-name]`
2. Eureka dashboard: http://localhost:8761
3. Service health endpoints: `/health` or `/actuator/health`

## Next Steps

After successful deployment and testing:
1. Set up CI/CD pipeline
2. Configure monitoring and alerting
3. Implement database backups
4. Add integration tests
5. Performance testing and optimization
