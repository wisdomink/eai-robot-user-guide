# ============================================================
# Stage 1: Build the frontend (React + Vite + SSR prerender)
# ============================================================
# Alpine-based Node images can terminate `npm ci` with npm's
# "Exit handler never called" error. Use the Debian-based build image.
FROM node:20.19.5-bookworm-slim AS frontend-builder

WORKDIR /build

# Copy package manifests for all workspaces first (enables layer caching)
COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/
COPY packages/chat-sdk/package.json packages/chat-sdk/
RUN npm ci --no-audit --no-fund && test -x node_modules/.bin/tsc

COPY . .

ARG VITE_CHAT_SERVICE_ORIGIN=http://127.0.0.1:8000
ARG VITE_CHATKIT_DOMAIN_KEY=local-dev
ARG VITE_SEARCH_API_URL=/api/search

ENV VITE_CHAT_SERVICE_ORIGIN=$VITE_CHAT_SERVICE_ORIGIN
ENV VITE_CHATKIT_DOMAIN_KEY=$VITE_CHATKIT_DOMAIN_KEY
ENV VITE_SEARCH_API_URL=$VITE_SEARCH_API_URL

# Images are copied into their own runtime layer below. Remove Vite's copy
# from dist so frequently changing HTML/JS does not invalidate the large,
# otherwise stable image layer on every deployment.
RUN npm run build -w web \
    && test -d apps/web/dist/images \
    && rm -rf apps/web/dist/images \
    && touch /build/.frontend-build-complete

# ============================================================
# Stage 2: Combined runtime (nginx + Python backend)
# ============================================================
FROM python:3.13-alpine

# Wait for the frontend build before downloading Python dependencies without
# copying the frequently changing frontend output yet. The stable marker keeps
# npm/pip installs serialized while allowing the dependency layers below to be
# reused when only frontend code changes.
COPY --from=frontend-builder /build/.frontend-build-complete /tmp/.frontend-build-complete

RUN apk add --no-cache nginx && mkdir -p /run/nginx

COPY apps/rag-api/requirements.txt apps/rag-api/requirements.lock /tmp/
RUN pip install --no-cache-dir --require-hashes --retries 10 --timeout 60 \
        -r /tmp/requirements.lock \
    && rm /tmp/requirements.txt /tmp/requirements.lock

# nginx: remove default config, add ours
RUN rm -f /etc/nginx/http.d/default.conf
COPY nginx/default.conf /etc/nginx/http.d/app.conf

# Keep manual images in a dedicated layer. When the images are unchanged, ECR
# reuses this layer and only the much smaller HTML/JS layer is uploaded.
COPY apps/web/public/images /usr/share/nginx/html/images

# dist no longer contains images, so this is a small application layer.
COPY --from=frontend-builder /build/apps/web/dist /usr/share/nginx/html

# Backend code + sidebar.json + active manuals release manifest.
# The manifest is image-versioned so every task in one deployment reads the
# same release snapshot; /app/rag-api/data is an ephemeral runtime volume.
COPY apps/rag-api/app /app/rag-api/app
COPY apps/web/src/content/sidebar.json /app/src/content/sidebar.json
COPY apps/rag-api/data/manuals-releases.json /app/rag-api/config/manuals-releases.json
COPY ["input/FF Assist_QA_CN.md", "/app/rag-api/fast-answer/ff_assist_preset_faq_cn.md"]
COPY ["input/FF_Assist_QA_EN.md", "/app/rag-api/fast-answer/ff_assist_preset_faq_en.md"]

# Match sidebar path for FastAPI (see app/core/config.py CONTENT_DIR)
ENV CONTENT_DIR=/app/src/content
ENV MANUALS_RELEASE_MANIFEST=/app/rag-api/config/manuals-releases.json
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
