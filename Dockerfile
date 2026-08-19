FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        zsh \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python 3.14 via uv
RUN uv python install 3.14

COPY . .

# Create .venv + install project dependencies + ensure-pip
RUN uv sync --python 3.14 && uv run python -m ensurepip --upgrade --default-pip

ENV PATH="/app/.venv/bin:$PATH"

CMD ["zsh"]
# apt-get update && apt-get install nmap -y && apt-get remove nmap -y