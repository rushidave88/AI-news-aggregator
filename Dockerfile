# Dockerfile

# ─── BASE IMAGE ───────────────────────────────────────────────────────
# Official Python 3.11 slim image — smaller than full Python image
FROM python:3.11-slim

# ─── SET WORKING DIRECTORY ────────────────────────────────────────────
# All commands below run from /app inside the container
WORKDIR /app

# ─── INSTALL uv ───────────────────────────────────────────────────────
# Copy uv binary directly from its official Docker image
# Faster than pip-installing uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ─── COPY DEPENDENCY FILES FIRST ─────────────────────────────────────
# Copy ONLY pyproject.toml and uv.lock before copying code
# WHY: Docker caches layers — if these files haven't changed,
#      Docker reuses the cached package install layer (very fast!)
COPY pyproject.toml uv.lock ./

# ─── INSTALL DEPENDENCIES ─────────────────────────────────────────────
# --no-dev:    skip development packages
# --frozen:    use exact versions from uv.lock (reproducible)
# --no-install-project: don't install our app yet, just dependencies
RUN uv sync --no-dev --frozen --no-install-project

# ─── COPY APPLICATION CODE ────────────────────────────────────────────
# Now copy the rest of the project
COPY src/ ./src/
COPY main.py ./

# ─── INSTALL PROJECT ITSELF ───────────────────────────────────────────
# Now install our app as a package (so imports work)
RUN uv sync --no-dev --frozen

# ─── ENVIRONMENT VARIABLES ────────────────────────────────────────────
# Tell Python not to write .pyc files (cleaner container)
ENV PYTHONDONTWRITEBYTECODE=1
# Tell Python not to buffer stdout (logs appear immediately)
ENV PYTHONUNBUFFERED=1
# Add src/ to Python path
ENV PYTHONPATH=/app/src

# ─── RUN THE APP ──────────────────────────────────────────────────────
# This command runs when the container starts
CMD ["uv", "run", "python", "main.py"]