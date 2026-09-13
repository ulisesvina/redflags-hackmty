# RedFlags

RedFlags turns company records into evidence-backed financial investigations. It waits for the full file set, follows suspicious peso flows, and reports only findings supported by source records.

## Run

```bash
docker compose up --build
```

Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

For local development, the launcher starts the frontend and the main API together:

```bash
cp .env.example .env
bun install
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
bun run dev:all
```

Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard). Press `Ctrl-C` to stop both services.

The main API runs the `PU-HackMTY` investigation engine in-process, so it does not need a third process. The separate evaluation API can be included when needed:

```bash
bun run dev:all -- --with-pu-api
```

That starts the evaluation API at `http://localhost:8765` and requires its own environment:

```bash
python3 -m venv PU-HackMTY/.venv
PU-HackMTY/.venv/bin/pip install -r PU-HackMTY/requirements.txt
```

For a containerized startup of the frontend and main API, use `docker compose up --build` instead.

## Flow

Upload → readiness check → investigation → result.

The result includes supported exposure in MXN, a money trail, cited evidence, affected suppliers, confidence, and leads that were not pursued. The two demo buttons reliably produce fraud and clean outcomes.

## Optional services

- Gemini answers questions from redacted case summaries.
- MongoDB stores finalized cases.
- Vultr hosts the web and API containers for a public demo. It is not part of fraud detection.
- Solana can timestamp the final evidence hash; local SHA-256 remains the default.

Credentials are optional. See `.env.example`.

## Verify

```bash
bun run lint
bun run test
bun run build
backend/.venv/bin/pytest backend/tests
```
