# Security Vulnerabilities Report

**Date:** 2026-01-03
**Scan Tool:** pip-audit (PyPA official)
**Status:** 🔴 CRITICAL - 29 vulnerabilities found in 11 packages

---

## 🚨 Critical Vulnerabilities (Immediate Fix Required)

### 1. LangChain (Multiple CVEs)

**Package:** `langchain==0.1.0`, `langchain-community==0.0.10`, `langchain-core==0.1.12`

| CVE | Severity | Description | Fix Version |
|-----|----------|-------------|-------------|
| CVE-2025-68664 | HIGH | Arbitrary code execution via prompt injection | langchain-core 0.3.81 |
| CVE-2025-65106 | HIGH | Remote code execution | langchain-core 0.3.80 |
| CVE-2025-6984 | HIGH | Path traversal in file loader | langchain-community 0.3.27 |
| CVE-2024-7774 | MEDIUM | Sensitive data exposure | No fix yet |

**Impact:** LLM-based extraction vulnerable to prompt injection attacks.

**Action:**
```bash
pip install langchain==0.3.0 \
  langchain-community==0.3.27 \
  langchain-core==0.3.81
```

**Note:** This requires updating entity_extractor.py for API changes.

---

### 2. Ray (Distributed Processing)

**Package:** `ray==2.9.0`

| CVE | Severity | Description | Fix Version |
|-----|----------|-------------|-------------|
| CVE-2025-62593 | CRITICAL | Unauthenticated remote code execution | ray 2.52.0 |
| CVE-2025-34351 | HIGH | Denial of service | No fix |
| CVE-2023-48022 | MEDIUM | Information disclosure | No fix |

**Impact:** Ray cluster on Server 84 vulnerable to RCE.

**Action:**
```bash
# On Server 84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray
# Update docker-compose.yml: ray:2.52.0
docker-compose pull
docker-compose up -d
```

**URGENT:** This affects production Ray cluster (9 nodes)!

---

### 3. urllib3 (HTTP Library)

**Package:** `urllib3==2.3.0`

| CVE | Severity | Description | Fix Version |
|-----|----------|-------------|-------------|
| CVE-2025-66418 | HIGH | CRLF injection | urllib3 2.6.0 |
| CVE-2025-66471 | HIGH | Request smuggling | urllib3 2.6.0 |
| CVE-2025-50182 | MEDIUM | Header injection | urllib3 2.5.0 |

**Impact:** HTTP requests to Ollama, ChromaDB vulnerable to injection.

**Action:**
```bash
pip install urllib3==2.6.0
```

---

### 4. requests (HTTP Library)

**Package:** `requests==2.31.0`

| CVE | Severity | Description | Fix Version |
|-----|----------|-------------|-------------|
| CVE-2024-47081 | HIGH | Cookie header leak | requests 2.32.4 |
| CVE-2024-35195 | MEDIUM | Header injection | requests 2.32.0 |

**Action:**
```bash
pip install requests==2.32.4
```

---

## ⚠️ Medium Priority Vulnerabilities

### 5. setuptools

**Package:** `setuptools==65.5.0`

| CVE | Severity | Fix |
|-----|----------|-----|
| CVE-2024-6345 | MEDIUM | setuptools 70.0.0 |

**Action:** `pip install setuptools==78.1.1`

### 6. black (Code Formatter)

**Package:** `black==23.12.1`

| CVE | Fix |
|-----|-----|
| PYSEC-2024-48 | black 24.3.0 |

**Action:** `pip install black==24.3.0`

### 7. tqdm (Progress Bar)

**Package:** `tqdm==4.66.1`

| CVE | Fix |
|-----|-----|
| CVE-2024-34062 | tqdm 4.66.3 |

**Action:** `pip install tqdm==4.66.3`

### 8. virtualenv

**Package:** `virtualenv==20.21.0`

| CVE | Fix |
|-----|-----|
| PYSEC-2024-187 | virtualenv 20.26.6 |

**Action:** `pip install virtualenv==20.26.6`

---

## 🔧 Fix All Vulnerabilities

### Updated requirements.txt

```txt
# SECURITY PATCHES APPLIED - 2026-01-03

# Core dependencies
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
psycopg2-binary==2.9.9
SQLAlchemy==2.0.25
alembic==1.13.1
neo4j==5.15.0
chromadb==0.4.22
redis==5.0.1

# Vector embeddings
openai==1.6.1
sentence-transformers==2.2.2
tiktoken==0.5.2

# LangChain ecosystem - UPDATED FOR SECURITY
langchain==0.3.0  # was 0.1.0
langchain-community==0.3.27  # was 0.0.10
langchain-core==0.3.81  # was 0.1.12
langgraph==0.0.20
langsmith==0.0.77

# Distributed processing - UPDATED FOR SECURITY
ray[default]==2.52.0  # was 2.9.0 - CRITICAL RCE FIX
celery==5.3.4
flower==2.0.1

# NLP & Text processing
spacy==3.7.2
python-Levenshtein==0.23.0
phonetics==1.0.5
unidecode==1.3.7
arabic-reshaper==3.0.0
python-bidi==0.4.2

# Utilities - UPDATED FOR SECURITY
tqdm==4.66.3  # was 4.66.1
pandas==2.1.4
numpy==1.26.2
requests==2.32.4  # was 2.31.0
httpx==0.25.2
urllib3==2.6.0  # was 2.3.0

# Logging & Monitoring
loguru==0.7.2
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development - UPDATED FOR SECURITY
black==24.3.0  # was 23.12.1
ruff==0.1.8
mypy==1.7.1
ipython==8.19.0
jupyter==1.0.0
setuptools==78.1.1  # was 65.5.0
virtualenv==20.26.6  # was 20.21.0
```

### Apply Fixes

```bash
cd apps/hadith-knowledge-graph

# Backup current requirements
cp requirements.txt requirements.txt.backup

# Update requirements.txt with patched versions above

# Recreate venv to ensure clean state
rm -rf venv
python -m venv venv
source venv/bin/activate

# Install patched dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify no vulnerabilities
pip-audit --desc
```

---

## 🔒 Security Best Practices (Going Forward)

### 1. Automated Security Scanning

**Pre-commit Hook:** `.git/hooks/pre-commit`
```bash
#!/bin/bash
cd apps/hadith-knowledge-graph
./scripts/security_scan.sh || exit 1
```

### 2. Weekly Dependency Updates

**Cron Job (Server 84):**
```cron
# Every Monday 2 AM
0 2 * * 1 cd /opt/wizardsofts-megabuild && ./scripts/weekly_security_scan.sh
```

### 3. Dependency Pinning

Always pin exact versions in `requirements.txt`:
```
✅ langchain==0.3.0
❌ langchain>=0.3.0
```

### 4. Security Scanning in CI/CD

**GitLab CI (.gitlab-ci.yml):**
```yaml
security-scan:
  stage: test
  script:
    - pip install pip-audit safety
    - pip-audit --desc
    - safety check --json
  allow_failure: false
```

---

## 📋 Action Items

**Immediate (Today):**
- [ ] Update Ray to 2.52.0 on Server 84 (CRITICAL RCE)
- [ ] Update urllib3, requests, langchain packages
- [ ] Run security scan: `./scripts/security_scan.sh`
- [ ] Commit updated requirements.txt

**This Week:**
- [ ] Set up pre-commit security hooks
- [ ] Add security scanning to GitLab CI/CD
- [ ] Review code for hardcoded secrets (bandit scan)

**Ongoing:**
- [ ] Weekly `pip-audit` scans
- [ ] Subscribe to security advisories (GitHub, CVE feeds)
- [ ] Quarterly dependency updates

---

## 📚 Resources

**Security Tools:**
- pip-audit: https://pypi.org/project/pip-audit/
- Safety: https://pyup.io/safety/
- Bandit: https://bandit.readthedocs.io/
- Trivy: https://aquasecurity.github.io/trivy/

**CVE Databases:**
- NVD: https://nvd.nist.gov/
- PyPI Advisory: https://github.com/pypa/advisory-database
- Snyk: https://security.snyk.io/

**Best Practices:**
- OWASP: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

**Last Updated:** 2026-01-03
**Next Scan:** After applying fixes
