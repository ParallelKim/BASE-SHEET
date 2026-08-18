# Hugging Face Spaces (Docker, free CPU). Slow torchcrepe is OK for personal phone use.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY web ./web
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install resampy tqdm \
    && pip install torchcrepe --no-deps \
    && pip install -e .

EXPOSE 7860
CMD ["sh", "-c", "python3 scripts/serve_midi_viewer.py --host 0.0.0.0 --port ${PORT:-7860} --no-open"]
