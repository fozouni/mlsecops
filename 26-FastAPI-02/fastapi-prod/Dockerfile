FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install -i https://mirror-pypi.runflare.com/simple --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

RUN useradd -m appuser && mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

COPY app ./app
COPY seed.py ./seed.py
COPY weights.json ./weights.json

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "--forwarded-allow-ips", "*", "app.main:app"]

#🚩 Uvicorn: The actual ASGI server that runs your FastAPI code.
# It handles the async Python and is very fast, but by default it only runs as a single process on one CPU core.

#🚩 Gunicorn: A process manager. It doesn't speak FastAPI's language natively,
# but it is excellent at managing multiple worker processes, restarting them if they crash,
# and utilizing all CPU cores.

#🤔 Why both? we use Gunicorn to manage multiple Uvicorn workers.
# This gives you the speed of Uvicorn with the stability and multi-core power of Gunicorn.

# The --forwarded-allow-ips "*" flag only tells FastAPI/Redis who the client really is
# (the user's real IP instead of 127.0.0.1). 