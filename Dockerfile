# syntax=docker/dockerfile:1

# Build the site image in CI; production only pulls the published image.

ARG UID=10001
ARG GID=10001


# Build CSS separately so the runtime image does not need Node.
FROM node:26-alpine AS css

ARG UID
ARG GID

ENV HOME=/home/site \
    npm_config_cache=/tmp/.npm

RUN addgroup -g ${GID} site \
    && adduser -D -u ${UID} -G site -h /home/site site \
    && mkdir -p /app/static/css \
    && chown -R site:site /app

WORKDIR /app
USER site

COPY --chown=site:site package.json package-lock.json ./
RUN npm ci

COPY --chown=site:site src/ ./src/
COPY --chown=site:site templates/ ./templates/
COPY --chown=site:site static/js/ ./static/js/

RUN npm run build:css


# Render the resume during the image build.
FROM python:3.14-slim AS pdf

ARG UID
ARG GID

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/site \
    XDG_CACHE_HOME=/tmp/.cache

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-build.txt ./
RUN pip install --no-cache-dir -r requirements-build.txt

RUN groupadd --gid ${GID} site \
    && useradd --uid ${UID} --gid ${GID} --home-dir /home/site --create-home site \
    && chown -R site:site /app

USER site

COPY --chown=site:site app.py music.py build_pdf.py ./
COPY --chown=site:site templates/ ./templates/
COPY --chown=site:site static/ ./static/
COPY --from=css --chown=site:site /app/static/css/tailwind.css ./static/css/tailwind.css

ARG SITE_URL=https://bensonc.how
RUN SITE_URL=${SITE_URL} python build_pdf.py


# Development image with livereload and PDF build dependencies.
FROM pdf AS dev

USER root
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

USER site

CMD ["python", "app.py"]


# Production image: only the app and its static files.
FROM python:3.14-slim AS runtime

ARG UID
ARG GID

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --gid ${GID} site \
    && useradd --system --uid ${UID} --gid ${GID} --no-create-home site \
    && chown -R site:site /app

USER site

COPY --chown=site:site app.py music.py ./
COPY --chown=site:site templates/ ./templates/
# The /licence routes read these off the repo root.
COPY --chown=site:site LICENSE LICENSE-CONTENT ./
COPY --from=pdf --chown=site:site /app/static/ ./static/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/').read(1)"

CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--max-requests", "500", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
