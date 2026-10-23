# The Lopper API for Render (or any container host). The scanner clones repos, so git has to be in the image.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY lopper ./lopper
RUN pip install --no-cache-dir ".[postgres,prod]"

RUN useradd --create-home lopper
USER lopper

# One worker with threads: scans run in a thread pool inside the process and the rate limit is kept in memory,
# so more than one worker would split both. Render sets PORT.
CMD ["sh", "-c", "lopper db-init && exec gunicorn 'lopper.api:create_app()' --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 8 --timeout 120"]
