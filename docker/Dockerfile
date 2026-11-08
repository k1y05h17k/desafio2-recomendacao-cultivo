FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project
COPY src/ ./src/
RUN uv sync --locked \
    && mkdir -p /workspace/.cache \
    && chown -R app:app /opt/venv /workspace

USER app
CMD ["uv", "run", "--locked", "pytest", "-m", "smoke", "-q"]

