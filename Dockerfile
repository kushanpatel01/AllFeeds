# Multi-stage Dockerfile for My Unified Feed

FROM python:3.12-slim as backend

# Install backend dependencies
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

FROM node:18-alpine as frontend-build

# Build frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ .
RUN yarn build

FROM python:3.12-slim

# Install Node.js for serving frontend and MongoDB
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org \
    && rm -rf /var/lib/apt/lists/*

# Install serve for frontend
RUN npm install -g serve

# Copy backend
WORKDIR /app
COPY --from=backend /app/backend ./backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create MongoDB data directory
RUN mkdir -p /data/db

# Copy supervisor configuration
COPY <<EOF /etc/supervisor/conf.d/unified-feed.conf
[program:mongodb]
command=/usr/bin/mongod --dbpath /data/db --bind_ip 0.0.0.0
autostart=true
autorestart=true
stderr_logfile=/var/log/mongodb.err.log
stdout_logfile=/var/log/mongodb.out.log

[program:backend]
command=python -m uvicorn server:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/backend.err.log
stdout_logfile=/var/log/backend.out.log

[program:frontend]
command=serve -s build -l 3000
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/frontend.err.log
stdout_logfile=/var/log/frontend.out.log
EOF

# Expose ports
EXPOSE 3000 8001

# Environment variables
ENV MONGO_URL=mongodb://localhost:27017
ENV REACT_APP_BACKEND_URL=http://localhost:8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
