# URL Shortener — FastAPI + SQLite

A clean, production-ready-ish URL shortener with a web interface and JSON API.

## Features
- Shorten long URLs into `/<code>` and redirect
- Click tracking: total clicks, last accessed
- Optional custom alias and expiry date
- Copy button + QR code download
- Recent links dashboard
- JSON API (`POST /api/shorten`, `GET /api/{code}`)
- Dockerized: one command start via `docker compose up --build`

## Quickstart (Local)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Visit http://127.0.0.1:8000

## Docker
```bash
docker compose up --build
```

## Configuration
Configure via env vars:
- `APP_BASE_URL` (default: `http://127.0.0.1:8000`) — used for building full short URLs.
- `DATABASE_URL` (default: `sqlite:///data/urls.db`)
- `CODE_LENGTH` (default: 6)

## API
- `POST /api/shorten`
  ```json
  {
    "url": "https://example.com/very/long",
    "custom_alias": "hello",       // optional
    "expires_in_days": 7           // optional
  }
  ```
  Response:
  ```json
  { "short_url": "http://127.0.0.1:8000/hello", "code":"hello" }
  ```

- `GET /api/{code}`
  Returns metadata for the code (does not redirect).

## Notes
SQLite file stored under `data/urls.db` by default; the folder is created if missing.
