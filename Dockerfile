# Klimabot web app (web/web.py via main.py) on port 7860.
# One process only: sessions, rate limits and the spend ledger live in memory.
#   docker compose up -d --build        (see docker-compose.yml and README → Docker)
# Secrets (ANTHROPIC_API_KEY, SMTP_*) come from the environment at run time, never from the image.
# Pinned by digest: a rebuild uses exactly this base. To take Debian/Python security updates,
# bump the tag and the digest together (docker buildx imagetools inspect python:<tag>).
FROM python:3.13.16-slim-trixie@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf

# Hugging Face Spaces run the container as uid 1000; the model cache and /data belong to it.
RUN useradd --create-home --uid 1000 app \
 && mkdir -p /opt/hf /data \
 && chown app:app /opt/hf /data

WORKDIR /app

# Dependencies before the code, so a code change doesn't reinstall PyTorch. The CPU-only
# build first: pip's default on Linux is the CUDA one (several GB the bot doesn't use).
COPY pyproject.toml ./
RUN pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install .

# Both HuggingFace models go into the image, so a new container doesn't download ~1.5 GB.
USER app
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('intfloat/multilingual-e5-base'); \
CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')"
USER root
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY . .

# Embed the knowledge base now (a few minutes on CPU) instead of at every container start.
# Importing bot does it. The key is a dummy (the import makes no API call), and the session
# the import opens is logged to a throwaway data dir.
RUN ANTHROPIC_API_KEY=build-time-dummy KLIMABOT_DATA_DIR=/tmp/build-data \
    KLIMABOT_KB_CACHE_DIR=/app/.kb_cache LEAD_MAIL_TO= SMTP_HOST= \
    python -c "import bot" \
 && rm -rf /tmp/build-data

USER app
ENV HOST=0.0.0.0 \
    PORT=7860 \
    KLIMABOT_DATA_DIR=/data \
    KLIMABOT_KB_CACHE_DIR=/app/.kb_cache
EXPOSE 7860

# Startup imports PyTorch and loads the KB (about a minute).
HEALTHCHECK --interval=60s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '7860') + '/api/config', timeout=4)"

# Exec form, so python is PID 1 and receives docker stop's SIGTERM: web.py turns it into a
# clean exit that ends the open conversations and e-mails their leads to the PM.
CMD ["python", "main.py"]
