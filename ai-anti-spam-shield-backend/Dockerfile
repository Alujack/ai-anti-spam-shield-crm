# ===========================================
# Stage 1: Dependencies
# ===========================================
FROM node:20-slim AS deps

WORKDIR /app

# Install dependencies for native modules
RUN apt-get update && apt-get install -y python3 make g++ curl openssl && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci --only=production

# Generate Prisma client
RUN npx prisma generate

# ===========================================
# Stage 2: Production
# ===========================================
FROM node:20-slim AS runner

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl openssl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 --gid nodejs aishield

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/prisma ./prisma

# Copy application code
COPY src ./src
COPY package*.json ./
COPY docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Set ownership
RUN chown -R aishield:nodejs /app

# Switch to non-root user
USER aishield

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Entrypoint runs migrations then starts app
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["node", "src/app.js"]
