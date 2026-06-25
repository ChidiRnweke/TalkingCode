# syntax=docker/dockerfile:1.7

FROM node:22-slim AS base

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

# Stage 1: Dependencies
FROM base AS deps

WORKDIR /app

# Copy package files and pnpm build-script approvals
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy Svelte config so the prepare script can sync during install
COPY svelte.config.js ./

# Install dependencies
RUN --mount=type=cache,target=/pnpm/store \
    pnpm install --frozen-lockfile

# Stage 2: Builder
FROM deps AS builder

WORKDIR /app

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Keep only production dependencies for runtime
RUN pnpm prune --prod

# Stage 3: Runtime
FROM node:22-slim

WORKDIR /app

# Copy build output and scripts
COPY --from=builder /app/build ./build
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Ensure production environment
ENV NODE_ENV=production

EXPOSE 3000

# Start through the launcher
CMD ["node", "--import", "./scripts/otel-instrumentation.js", "--import", "./scripts/secrets.js", "build"]
