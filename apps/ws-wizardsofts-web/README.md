Frontend docker notes

## Persistent storage

The contact submissions are stored in /app/data/submissions.json inside the container. To persist submissions across container restarts, mount a host directory at /app/data when running the container:

docker run -v /path/on/host:/app/data -p 3000:3000 wizardsofts/frontend:latest

## Smoke test

There is a convenience smoke-test script at scripts/docker-smoke-test.sh which builds the image, runs a container, posts a test submission, and prints the submissions file. Optionally pass a host directory to persist the data:

./scripts/docker-smoke-test.sh /tmp/frontend-data

# WizardSofts Corporate Website

A modern, performant corporate marketing website built with Next.js, Tailwind CSS, and SQLite.

## Features

- 🚀 **Fast & Performant**: Built with Next.js 15 and optimized for Core Web Vitals
- ♿ **Accessible**: Meets WCAG 2.1 AA standards with automated axe-core testing
- 🎨 **Modern UI**: Tailwind CSS v4 with custom theming
- 📝 **Contact Form**: Server-side validated contact submissions with anti-spam protection
- 📝 **Contact Form**: Server-side validated contact submissions with anti-spam protection
- 🗄️ **Storage**: File-backed JSON store (no ORM). Contact submissions are persisted to /app/data/submissions.json inside the container.
- 🐳 **Containerized**: Multi-stage Docker build for production

## Getting Started

### Prerequisites

- Node.js 20 or higher
- No database server required (uses SQLite)

### Installation

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`

Open [http://localhost:3000](http://localhost:3000)

## Storage

This project no longer uses Prisma or a relational database by default. Submissions are stored in a file inside the container:

- File: `/app/data/submissions.json`
- To persist across container restarts, mount a host directory at `/app/data` when running the container.

Example:

```bash
docker run -v /path/on/host:/app/data -p 3000:3000 wizardsofts/frontend:latest
```

## Docker

### Prerequisites for Docker Registry

Before building and pushing images, configure Docker to allow the insecure HTTP registry:

**Docker Desktop Configuration:**

1. Open **Docker Desktop**
2. Click **Settings** (gear icon)
3. Go to **Docker Engine** tab
4. Add the registry to `insecure-registries`:

```json
{
  "insecure-registries": [
    "10.0.0.80:5050"
  ]
}
```

5. Click **Apply & Restart**

### Building and Pushing to Registry

Build multi-platform Docker images (supports both linux/amd64 and linux/arm64):

```bash
# Build and push with default tag (latest)
./build-and-push.sh

# Or build and push with a specific tag
./build-and-push.sh v1.0.0
```

The script builds for both architectures and pushes to `10.0.0.80:5050/wizardsofts/www.wizardsofts.com`.

### Verify Image in Registry

Check if the image was successfully pushed:

```bash
# List all repositories
curl -X GET http://10.0.0.80:5050/v2/_catalog

# List tags for this image
curl -X GET http://10.0.0.80:5050/v2/wizardsofts/www.wizardsofts.com/tags/list

# Inspect image manifest
docker manifest inspect 10.0.0.80:5050/wizardsofts/www.wizardsofts.com:latest
```

### Running from Registry

Run the container with persistent storage:

```bash
# Run in detached mode with auto-restart
docker run -d --restart unless-stopped \
  -p 3000:3000 \
  --name wizardsofts-web \
  -v /path/on/host:/app/data \
  10.0.0.80:5050/wizardsofts/www.wizardsofts.com:latest

# View logs
docker logs -f wizardsofts-web

# Stop container
docker stop wizardsofts-web

# Remove container
docker rm wizardsofts-web
```

### Smoke Test

Test the Docker build and functionality:

```bash
./scripts/docker-smoke-test.sh [/path/to/persistent/data]
```

### Troubleshooting

**Error: "http: server gave HTTP response to HTTPS client"**
- Docker is trying to use HTTPS for an HTTP registry
- Solution: Add `10.0.0.80:5050` to Docker Desktop's insecure registries (see Prerequisites above)

**Error: "no matching manifest for linux/amd64"**
- Image was built for wrong architecture
- Solution: Use the `build-and-push.sh` script which builds for both amd64 and arm64

**Error: "npm ci can only install packages when package.json and package-lock.json are in sync"**
- Lockfile is out of sync with package.json
- Solution: Run `npm install` locally and commit the updated `package-lock.json`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm test` - Run tests
- `npm run lint` - Run linting
- `./build-and-push.sh [tag]` - Build and push multi-platform Docker image

## Documentation

See `/specs/001-build-a-corporate/` for complete documentation.

## License

Proprietary - WizardSofts © 2025
