# API

The API validates uploads, enforces readiness, runs investigations, and returns the result view.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8001
```

Routes:

- `POST /extract-books`
- `POST /investigate/start`
- `GET /demo-books/{fraud|clean}`
- `POST /cases/{runId}/ask`
- `POST /cases/{runId}/anchor`
- `GET /integrations/status`
- `GET /health`
