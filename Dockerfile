# ============================================================
# Stage 1: Build the frontend (React + Vite + SSR prerender)
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

ARG VITE_CHATKIT_API_URL=/api/chatkit
ARG VITE_CHATKIT_DOMAIN_KEY=local-dev
ARG VITE_SEARCH_API_URL=/api/search

ENV VITE_CHATKIT_API_URL=$VITE_CHATKIT_API_URL
ENV VITE_CHATKIT_DOMAIN_KEY=$VITE_CHATKIT_DOMAIN_KEY
ENV VITE_SEARCH_API_URL=$VITE_SEARCH_API_URL

RUN npm run build

# ============================================================
# Stage 2: Combined runtime (nginx + Python backend)
# ============================================================
FROM python:3.13-alpine

RUN apk add --no-cache nginx && mkdir -p /run/nginx

COPY rag_server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir supervisor -r /tmp/requirements.txt && rm /tmp/requirements.txt

# nginx: remove default config, add ours
RUN rm -f /etc/nginx/http.d/default.conf
COPY nginx/default.conf /etc/nginx/http.d/app.conf

# Frontend static files
COPY --from=frontend-builder /build/dist /usr/share/nginx/html

# Backend code + sidebar.json
COPY rag_server/app /app/rag_server/app
COPY src/content/sidebar.json /app/src/content/sidebar.json

# Log directory (mount as a Docker volume to persist across restarts)
RUN mkdir -p /app/rag_server/logs
ENV LOG_DIR=/app/rag_server/logs
VOLUME ["/app/rag_server/logs"]

# supervisord config
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
