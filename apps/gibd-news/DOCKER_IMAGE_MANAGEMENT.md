# Docker Image Management for GIBD News

## Problem
Building the gibd-news Docker image takes 15-20 minutes due to:
- Chrome installation (~10 minutes)
- Python dependencies including PyTorch (~5-10 minutes)
- Large image size (~1.5 GB)

## Solutions

---

## Option 1: Push to Container Registry (Recommended)

### A. Using GitLab Container Registry

**1. Login to GitLab Registry:**
```bash
# Login to your GitLab instance
docker login registry.wizardsofts.com
# OR for gitlab.com:
# docker login registry.gitlab.com
```

**2. Build and Tag Image:**
```bash
cd /Users/mashfiqurrahman/Workspace/guardianinvestmentbd/gibd-news

# Build with proper tag
docker build -t registry.wizardsofts.com/gibd/gibd-news:latest .
docker build -t registry.wizardsofts.com/gibd/gibd-news:v1.0.0 .

# Or if using gitlab.com:
# docker build -t registry.gitlab.com/your-username/gibd-news:latest .
```

**3. Push to Registry:**
```bash
docker push registry.wizardsofts.com/gibd/gibd-news:latest
docker push registry.wizardsofts.com/gibd/gibd-news:v1.0.0
```

**4. Pull on Any Machine:**
```bash
# On any machine (your laptop, server, CI/CD)
docker pull registry.wizardsofts.com/gibd/gibd-news:latest

# Use in docker-compose.yml:
# image: registry.wizardsofts.com/gibd/gibd-news:latest
```

**Benefits:**
- ✅ Team members can pull pre-built image (no 20-minute wait)
- ✅ CI/CD can use cached image
- ✅ Version control with tags
- ✅ Automatic cleanup of old images

---

### B. Using Docker Hub

**1. Login:**
```bash
docker login
# Enter your Docker Hub username and password
```

**2. Build and Push:**
```bash
# Tag with your Docker Hub username
docker build -t yourusername/gibd-news:latest .
docker push yourusername/gibd-news:latest

# Use in docker-compose:
# image: yourusername/gibd-news:latest
```

---

## Option 2: Save/Load Docker Image Locally

For offline use or sharing via file:

**1. Save Image to TAR File:**
```bash
# After successful build:
docker build -t gibd-news:latest .

# Save to file (~1.5 GB compressed)
docker save gibd-news:latest | gzip > gibd-news-latest.tar.gz

# Or save multiple tags:
docker save gibd-news:latest gibd-news:v1.0.0 | gzip > gibd-news-all.tar.gz
```

**2. Load Image from TAR File:**
```bash
# On another machine or after docker system prune:
docker load < gibd-news-latest.tar.gz

# Or from gzipped file:
gunzip -c gibd-news-latest.tar.gz | docker load

# Verify loaded:
docker images | grep gibd-news
```

**3. Share TAR File:**
```bash
# Copy to USB drive, network share, or cloud storage
cp gibd-news-latest.tar.gz /Volumes/USB/

# Or upload to S3/Google Drive for team access
aws s3 cp gibd-news-latest.tar.gz s3://your-bucket/docker-images/
```

**Benefits:**
- ✅ Works offline
- ✅ No registry needed
- ✅ Good for initial setup on air-gapped servers

**Drawbacks:**
- ❌ Large file size (~1.5 GB)
- ❌ Manual distribution
- ❌ No version management

---

## Option 3: Multi-Stage Build with Base Image

Create a reusable base image with heavy dependencies:

**Create `Dockerfile.base`:**
```dockerfile
# Base image with Chrome and system dependencies
FROM python:3.11-slim as gibd-news-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install Chrome and system dependencies (SLOW - 10 minutes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libxcomposite1 libxdamage1 libxfixes3 \
    libxkbcommon0 libxrandr2 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && mkdir -p /etc/apt/keyrings \
    && gpg --dearmor < /tmp/google-chrome-key.pub > /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/google-chrome-key.pub

# Install Python dependencies (SLOW - 5 minutes)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
```

**Build and Push Base Image (Once):**
```bash
# Build base (takes 15-20 minutes, but only once!)
docker build -f Dockerfile.base -t registry.wizardsofts.com/gibd/gibd-news-base:latest .
docker push registry.wizardsofts.com/gibd/gibd-news-base:latest
```

**Update Main `Dockerfile` to Use Base:**
```dockerfile
# Use pre-built base image (FAST - 1 minute!)
FROM registry.wizardsofts.com/gibd/gibd-news-base:latest

WORKDIR /app

# Only copy application code (fast!)
COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs

ENV ACTIVE_PROFILE=docker

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from scripts.config_loader import get_api_keys; print('Config OK')" || exit 1

CMD ["python", "-m", "scripts.news_summarizer"]
```

**Rebuild Main Image (Fast!):**
```bash
# Now rebuilds in ~1 minute instead of 20!
docker build -t gibd-news:latest .
```

**When to Rebuild Base:**
- Only when `requirements.txt` changes
- Or when Chrome needs updating (rarely)

---

## Option 4: Docker Build Cache

Use BuildKit cache mounting for faster rebuilds:

**Enable BuildKit:**
```bash
export DOCKER_BUILDKIT=1
```

**Update Dockerfile with Cache Mounts:**
```dockerfile
# In pip install step:
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
```

**Build with Cache:**
```bash
DOCKER_BUILDKIT=1 docker build --cache-from gibd-news:latest -t gibd-news:latest .
```

---

## Recommended Workflow

### For Development (Local Machine):

```bash
# 1. First time: Build and save base image
docker build -f Dockerfile.base -t gibd-news-base:latest .
docker save gibd-news-base:latest | gzip > gibd-news-base.tar.gz

# 2. Daily work: Use base image for fast rebuilds
docker build -t gibd-news:latest .  # Takes 1 minute instead of 20!
```

### For Production (Team/CI/CD):

```bash
# 1. Build and push base image (once, or when dependencies change)
docker build -f Dockerfile.base -t registry.wizardsofts.com/gibd/gibd-news-base:latest .
docker push registry.wizardsofts.com/gibd/gibd-news-base:latest

# 2. Update main Dockerfile to use base image (see above)

# 3. Build and push main image (fast!)
docker build -t registry.wizardsofts.com/gibd/gibd-news:latest .
docker push registry.wizardsofts.com/gibd/gibd-news:latest

# 4. Anyone can pull and use:
docker pull registry.wizardsofts.com/gibd/gibd-news:latest
```

### For CI/CD (.gitlab-ci.yml):

```yaml
stages:
  - build-base
  - build
  - deploy

# Only run when requirements.txt changes
build-base:
  stage: build-base
  script:
    - docker build -f Dockerfile.base -t $CI_REGISTRY_IMAGE/base:latest .
    - docker push $CI_REGISTRY_IMAGE/base:latest
  only:
    changes:
      - requirements.txt
      - Dockerfile.base

# Run on every commit (fast because base is cached)
build:
  stage: build
  script:
    - docker pull $CI_REGISTRY_IMAGE/base:latest || true
    - docker build --cache-from $CI_REGISTRY_IMAGE/base:latest -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest
```

---

## Quick Command Reference

### Save/Load Commands
```bash
# Save single image
docker save gibd-news:latest > gibd-news.tar
docker save gibd-news:latest | gzip > gibd-news.tar.gz

# Load image
docker load < gibd-news.tar
gunzip -c gibd-news.tar.gz | docker load

# Save multiple images
docker save gibd-news:latest gibd-news:v1.0.0 > gibd-news-all.tar

# Export/Import (for containers, not recommended)
docker export <container-id> > container.tar
docker import container.tar new-image:latest
```

### Registry Commands
```bash
# Login
docker login registry.wizardsofts.com

# Tag
docker tag gibd-news:latest registry.wizardsofts.com/gibd/gibd-news:latest

# Push
docker push registry.wizardsofts.com/gibd/gibd-news:latest

# Pull
docker pull registry.wizardsofts.com/gibd/gibd-news:latest

# List tags
curl -u username:password https://registry.wizardsofts.com/v2/gibd/gibd-news/tags/list
```

### Cleanup Commands
```bash
# Remove unused images
docker image prune

# Remove all stopped containers and unused images
docker system prune -a

# Remove specific image
docker rmi gibd-news:latest

# Keep only last 3 images
docker images | grep gibd-news | tail -n +4 | awk '{print $3}' | xargs docker rmi
```

---

## Comparison Table

| Method | Build Time | Storage | Team Access | Versioning | Offline |
|--------|------------|---------|-------------|------------|---------|
| **Registry (GitLab)** | 1 min* | Cloud | ✅ Excellent | ✅ Tags | ❌ No |
| **Registry (Docker Hub)** | 1 min* | Cloud | ✅ Good | ✅ Tags | ❌ No |
| **Save/Load TAR** | 20 min | ~1.5 GB local | ❌ Manual | ❌ Manual | ✅ Yes |
| **Multi-stage Base** | 1 min* | Cloud + Local | ✅ Excellent | ✅ Tags | ⚠️ Partial |
| **BuildKit Cache** | 5-10 min | Local | ❌ No | ❌ No | ✅ Yes |

*After initial base image build

---

## Recommendation for Your Setup

**Best Approach: Multi-stage Base + GitLab Registry**

```bash
# 1. Create Dockerfile.base (see above)
cd /Users/mashfiqurrahman/Workspace/guardianinvestmentbd/gibd-news

# 2. Build base image (once, 20 minutes)
docker build -f Dockerfile.base -t registry.wizardsofts.com/gibd/gibd-news-base:latest .
docker push registry.wizardsofts.com/gibd/gibd-news-base:latest

# 3. Update Dockerfile to use base (see above)

# 4. Fast daily builds (1 minute!)
docker build -t registry.wizardsofts.com/gibd/gibd-news:latest .
docker push registry.wizardsofts.com/gibd/gibd-news:latest

# 5. In megabuild docker-compose.yml:
#   image: registry.wizardsofts.com/gibd/gibd-news:latest
```

**Why This Works Best:**
- ✅ Team can pull pre-built images instantly
- ✅ CI/CD rebuilds take 1 minute instead of 20
- ✅ Proper version control with tags
- ✅ Only rebuild base when dependencies change
- ✅ Works with megabuild integration

---

## Next Steps

1. **Immediate**: Save current image locally while testing
   ```bash
   docker save gibd-news:latest | gzip > ~/gibd-news-backup.tar.gz
   ```

2. **Short-term**: Create Dockerfile.base and push to registry

3. **Long-term**: Add to CI/CD pipeline for automatic builds

---

**Questions? Check:**
- GitLab Container Registry docs: https://docs.gitlab.com/ee/user/packages/container_registry/
- Docker save/load: https://docs.docker.com/engine/reference/commandline/save/
- Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
