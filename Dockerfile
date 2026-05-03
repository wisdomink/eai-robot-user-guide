# ============================================================
# Stage 1: Build the frontend (React + Vite + SSR prerender)
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy package manifests for all workspaces first (enables layer caching)
COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/
COPY packages/chat-sdk/package.json packages/chat-sdk/
RUN npm ci

COPY . .

ARG VITE_CHAT_SERVICE_ORIGIN=http://127.0.0.1:8000
ARG VITE_CHATKIT_DOMAIN_KEY=local-dev
ARG VITE_SEARCH_API_URL=/api/search

ENV VITE_CHAT_SERVICE_ORIGIN=$VITE_CHAT_SERVICE_ORIGIN
ENV VITE_CHATKIT_DOMAIN_KEY=$VITE_CHATKIT_DOMAIN_KEY
ENV VITE_SEARCH_API_URL=$VITE_SEARCH_API_URL

RUN npm run build -w web

# ============================================================
# Stage 2: Combined runtime (nginx + Python backend)
# ============================================================
FROM python:3.13-alpine

RUN apk add --no-cache nginx && mkdir -p /run/nginx

COPY apps/rag-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir supervisor -r /tmp/requirements.txt && rm /tmp/requirements.txt

# nginx: remove default config, add ours
RUN rm -f /etc/nginx/http.d/default.conf
COPY nginx/default.conf /etc/nginx/http.d/app.conf

# Frontend static files
COPY --from=frontend-builder /build/apps/web/dist /usr/share/nginx/html

# Backend code + sidebar.json (CONTENT_DIR=/app/src/content in container)
COPY apps/rag-api/app /app/rag-api/app
COPY apps/web/src/content/sidebar.json /app/src/content/sidebar.json
COPY ["input/FF Assist_QA_CN.md", "/app/rag-api/fast-answer/ff_assist_preset_faq_cn.md"]
COPY ["input/FF_Assist_QA_EN.md", "/app/rag-api/fast-answer/ff_assist_preset_faq_en.md"]

# Match sidebar path for FastAPI (see app/core/config.py CONTENT_DIR)
ENV CONTENT_DIR=/app/src/content
ENV PRESET_FAQ_PATHS=/app/rag-api/fast-answer/ff_assist_preset_faq_cn.md,/app/rag-api/fast-answer/ff_assist_preset_faq_en.md
ENV ANSWER_MEMORY_DATA_PATH=/app/rag-api/data/answer_memory.jsonl

# Data/log directories (mount as Docker volumes to persist across restarts)
RUN mkdir -p /app/rag-api/logs /app/rag-api/data /app/rag-api/fast-answer
ENV LOG_DIR=/app/rag-api/logs
VOLUME ["/app/rag-api/logs", "/app/rag-api/data"]

# supervisord config
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
