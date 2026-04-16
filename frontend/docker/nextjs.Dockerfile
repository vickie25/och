# Build stage
FROM node:20-alpine AS builder

# Set build arguments for Next.js (hardcoded into client-side JS)
ARG NEXT_PUBLIC_DJANGO_API_URL
ARG NEXT_PUBLIC_FRONTEND_URL
ARG NEXT_PUBLIC_FASTAPI_API_URL

WORKDIR /app

# Copy package files
COPY frontend/nextjs_app/package.json frontend/nextjs_app/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/nextjs_app .

# Set environment variables for the build process
ENV NEXT_PUBLIC_DJANGO_API_URL=$NEXT_PUBLIC_DJANGO_API_URL
ENV NEXT_PUBLIC_FRONTEND_URL=$NEXT_PUBLIC_FRONTEND_URL
ENV NEXT_PUBLIC_FASTAPI_API_URL=$NEXT_PUBLIC_FASTAPI_API_URL
ENV NODE_OPTIONS=--max-old-space-size=3072
ENV NEXT_BUILD_LOW_MEMORY=1

# Build Next.js application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY frontend/nextjs_app/package.json frontend/nextjs_app/package-lock.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Start Next.js
CMD ["npm", "start"]
