FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=server.py \
    HF_HOME=/home/app/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url "$TORCH_INDEX_URL" 'torch>=2.6,<3' \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /home/app/.cache/huggingface \
    && chown -R app:app /home/app/.cache
COPY --chown=app:app server.py config.yaml VERSION ./
USER app

EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=5s --start-period=300s --retries=3 \
    CMD python -c "import os, urllib.request, yaml; config = yaml.safe_load(open(os.environ.get('SIMILARSTRING_CONFIG', '/app/config.yaml'))); port = config.get('server', {}).get('port', 5000); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=4)"

CMD ["python", "server.py"]
