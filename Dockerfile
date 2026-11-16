# Build once, promote the same image through every environment (never rebuilt per env).
# Base pinned by digest so a rebuild cannot silently pick up different bytes; Dependabot bumps it.
ARG PYTHON_IMAGE=python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

FROM ${PYTHON_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first: this layer is cached until the lockfile changes.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM ${PYTHON_IMAGE}
# Fixed numeric UID so Kubernetes runAsNonRoot can verify it without resolving a name.
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid 10001 --no-create-home app
COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv
# The runtime needs no package manager. Removing pip and its bundled copies also removes the
# vendored urllib3 and msgpack inside pip, which otherwise show up as image vulnerabilities
# that the app itself never uses.
RUN rm -rf /usr/local/lib/python3*/ensurepip /usr/local/lib/python3*/site-packages/pip \
    /usr/local/lib/python3*/site-packages/pip-*.dist-info \
    /usr/local/lib/python3*/site-packages/setuptools* \
    /usr/local/lib/python3*/site-packages/_distutils_hack
# Upgrade only the one base package that has a published fix (zlib1g, HIGH). The pinned base
# digest is still the current python:3.14-slim, so bumping the base would not pick this up.
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade zlib1g \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080
USER 10001:10001
EXPOSE 8080
HEALTHCHECK NONE
ENTRYPOINT ["python", "-m", "payment_service"]
