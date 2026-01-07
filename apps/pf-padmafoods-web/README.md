# PadmaFoods Web

Next.js web application for PadmaFoods business.

## Purpose

Corporate website and management dashboard for PadmaFoods.

## Quick Start

```bash
# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build
npm start

# Docker
docker build -t pf-padmafoods-web .
docker run --rm -p 3000:3000 pf-padmafoods-web
```

## Structure

```
app/               # Next.js App Router pages
components/        # React components
```

## Configuration

See `.env.local` for environment configuration.

## Related

- [CLAUDE.md](CLAUDE.md) - AI coding instructions
