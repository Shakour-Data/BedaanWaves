# Frontend Dockerfile — BedaanWaves Next.js 16 (standalone build)
FROM node:18-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# Install dependencies (leverages layer cache)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# Production image
# ---------------------------------------------------------------------------
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy the standalone server output and static assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Allow non-root execution
RUN addgroup -g 1001 -S nodejs && adduser -u 1001 -S -G nodejs nextjs
USER nextjs

EXPOSE 3005

# Next.js standalone reads PORT env var
ENV PORT=3005
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
