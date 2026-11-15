# Astro Health dashboard — production image.
#
# Build from this directory (frontend/):
#   docker build -t astro-health-frontend .
# Or from the project root with docker compose (see docker-compose.yml).
# Run:
#   docker run -p 8080:80 astro-health-frontend
#
# VITE_API_BASE is baked into the bundle at build time (Vite reads it
# when compiling). Override it for deployments where the API lives
# somewhere other than http://localhost:8000:
#   docker build --build-arg VITE_API_BASE=https://api.example.com/api/v1 .

# Stage 1: build the React/Vite bundle.
FROM docker.io/library/node:20-alpine AS build

ARG VITE_API_BASE=http://localhost:8000/api/v1
ENV VITE_API_BASE=$VITE_API_BASE

WORKDIR /app

# Install dependencies first so the layer is cached when only source changes.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY index.html ./
COPY src/ ./src/
RUN npm run build

# Stage 2: serve the static bundle with nginx.
FROM docker.io/library/nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
