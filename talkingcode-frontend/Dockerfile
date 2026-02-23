# Stage 1: Builder
FROM node:22-slim AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Stage 2: Runtime
FROM node:22-slim

WORKDIR /app

# Install pnpm (needed for some run commands if any, but we use node directly)
RUN npm install -g pnpm

# Copy build output and scripts
COPY --from=builder /app/build ./build
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Ensure production environment
ENV NODE_ENV=production

EXPOSE 3000

# Start through the launcher
CMD ["node", "scripts/server.js"]
