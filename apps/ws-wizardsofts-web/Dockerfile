# Multi-stage Dockerfile for Next.js production build

# Stage 1: Dependencies
FROM node:20-bullseye-slim AS deps
WORKDIR /app

# Install dependencies needed for build
COPY package.json package-lock.json ./
# Install all dependencies (including devDependencies) for the build step
RUN npm install --legacy-peer-deps --no-audit --no-fund --silent

# Stage 2: Builder
FROM node:20-bullseye-slim AS builder
WORKDIR /app

COPY package.json ./
# Install dependencies directly in builder (ignoring lockfile to ensure clean install)
RUN npm install --legacy-peer-deps --no-audit --no-fund

# Copy source code
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

# Build the application
RUN npm run build

# Stage 3: Runner
FROM node:20-bullseye-slim AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Install wget for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
# Automatically leverages output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Ensure a writable data directory exists for the file-backed store
RUN mkdir -p /app/data && \
    echo '[]' > /app/data/submissions.json && \
    chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
