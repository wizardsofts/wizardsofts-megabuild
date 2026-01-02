# Multi-stage build for Next.js frontend

FROM node:18-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@10.24.0

# Copy workspace files
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web ./apps/web
COPY packages ./packages

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build frontend
RUN pnpm turbo run build --filter=web

# Runtime stage
FROM node:18-alpine AS runtime

WORKDIR /app

# Copy built app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
USER nextjs

EXPOSE 3000

ENV NODE_ENV=production

CMD ["node", "apps/web/server.js"]
