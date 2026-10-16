FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# OpenShift's "restricted" SCC runs the container as an arbitrary, randomly
# assigned UID (ignoring the USER below) but always keeps it in group 0.
# Making /app and /data group-writable (not just owner-writable) is what
# actually makes this work there; the named user+fixed UID below is for
# plain Docker/Kubernetes, which does honor USER.
RUN mkdir -p /data \
    && useradd -u 1001 -g 0 -m -d /home/appuser appuser \
    && chgrp -R 0 /app /data /home/appuser \
    && chmod -R g=u /app /data /home/appuser

USER 1001

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
