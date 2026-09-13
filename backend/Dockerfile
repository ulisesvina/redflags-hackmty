FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FORENSIC_ENGINE_ROOT=/app/engine
ENV FORENSIC_ENGINE_PYTHON=/usr/local/bin/python
ENV CASE_STORAGE_ROOT=/app/backend/runtime/cases

WORKDIR /app
COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY PU-HackMTY/requirements.txt /tmp/engine-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt -r /tmp/engine-requirements.txt

COPY backend ./backend
COPY PU-HackMTY ./engine
RUN mkdir -p /app/backend/runtime/cases

EXPOSE 8001
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
