# URL Shortener with Analytics

A minimal but complete REST API that shortens URLs and tracks click analytics
(count, timestamps, referrers, user agents). Built with **FastAPI**,
**SQLModel** and **SQLite**.

Portfolio project — junior-level, ~300 lines of code, fully tested.

---

## Features

- `POST /shorten` – takes a long URL, returns a short code + full short URL
- `GET /{code}` – 302 redirect to the original URL and records a click
- `GET /stats/{code}` – click count, creation time, last click, top referrers,
  top user agents
- Automatic OpenAPI docs at `/docs` (Swagger UI) and `/redoc`
- Config via `.env` (using `pydantic-settings`)
- Pytest suite with isolated in-memory database

## Tech stack

| Layer         | Choice                                            |
|---------------|---------------------------------------------------|
| Framework     | [FastAPI](https://fastapi.tiangolo.com/)          |
| Validation    | Pydantic v2                                       |
| ORM           | [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic) |
| Database      | SQLite (swap to Postgres by changing `DATABASE_URL`) |
| Server        | Uvicorn                                           |
| Tests         | Pytest + FastAPI TestClient                       |
| Config        | `pydantic-settings` + `.env`                      |

## Project structure

```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app + endpoints
│   ├── models.py       # SQLModel tables (ShortURL, Click)
│   ├── schemas.py      # Pydantic request/response models
│   ├── database.py     # Engine + session dependency
│   ├── shortener.py    # Collision-safe short code generator
│   └── config.py       # Settings loaded from .env
├── tests/
│   ├── conftest.py     # Pytest fixtures (in-memory DB)
│   └── test_api.py     # Endpoint tests
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── requirements-dev.txt
```

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/url-shortener.git
cd url-shortener

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Then edit .env if you want to change BASE_URL, DATABASE_URL, or CODE_LENGTH.
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Open your browser at:

- <http://localhost:8000/docs> – Swagger UI (interactive)
- <http://localhost:8000/redoc> – ReDoc

The SQLite database `shortener.db` will be created automatically on first run.

## Usage

### Create a short URL

```bash
curl -X POST http://localhost:8000/shorten \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.example.com/some/very/long/path?with=query"}'
```

Response (`201 Created`):

```json
{
  "code": "aZ4kPq",
  "short_url": "http://localhost:8000/aZ4kPq",
  "original_url": "https://www.example.com/some/very/long/path?with=query",
  "created_at": "2026-01-15T10:23:45.123456"
}
```

### Visit the short URL

```bash
curl -i http://localhost:8000/aZ4kPq
```

Response: `302 Found` with `Location: https://www.example.com/...`.

### Get click stats

```bash
curl http://localhost:8000/stats/aZ4kPq
```

Response (`200 OK`):

```json
{
  "code": "aZ4kPq",
  "original_url": "https://www.example.com/some/very/long/path?with=query",
  "created_at": "2026-01-15T10:23:45.123456",
  "click_count": 3,
  "last_clicked_at": "2026-01-15T10:31:02.987654",
  "top_referrers": [
    {"value": "https://twitter.com", "count": 2}
  ],
  "top_user_agents": [
    {"value": "Mozilla/5.0 ...", "count": 3}
  ]
}
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use an in-memory SQLite database via a fixture, so they never touch
`shortener.db` and are fully isolated from each other.

## Screenshots

Add screenshots of the Swagger UI here after cloning the repo:

```
docs/screenshots/swagger-overview.png
docs/screenshots/shorten-endpoint.png
docs/screenshots/stats-response.png
```

Then reference them in this section, e.g.:

```md
![Swagger UI overview](docs/screenshots/swagger-overview.png)
```

## Design notes

- **Route order matters.** `/stats/{code}` is declared before `/{code}` so
  the catch-all redirect route doesn't swallow it. There's a test that
  verifies `/docs` and `/openapi.json` still resolve.
- **Codes are generated with `secrets`**, not `random`, because it's a
  cryptographically secure PRNG. A uniqueness check + retry loop guards
  against the vanishingly small collision probability.
- **DB models and API schemas are separated.** SQLModel classes live in
  `models.py`, Pydantic request/response models live in `schemas.py`. This
  prevents accidentally leaking internal columns and lets each evolve
  independently.
- **Sync endpoints, not `async def`.** SQLModel's default session is
  synchronous. Mixing `async def` handlers with sync DB calls is a common
  footgun that blocks the event loop. Using plain `def` lets FastAPI run
  handlers in a threadpool, which is fine for I/O like SQLite.

## Roadmap (nice-to-haves)

- Custom aliases (`POST /shorten` with a desired code)
- Expiration (URL expires after N days)
- Rate limiting via `slowapi`
- Alembic migrations
- Dockerfile + `docker-compose.yml`
- Deploy to Fly.io / Railway / Render
- Swap SQLite for PostgreSQL

## License

MIT — see [LICENSE](./LICENSE).
