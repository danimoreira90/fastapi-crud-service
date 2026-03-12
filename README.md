# FastAPI CRUD Service

Production-ready FastAPI service with PostgreSQL, JWT authentication, and full CRUD operations.

## Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 16 (CP — consistency + partition tolerance)
- **ORM**: SQLAlchemy 2.0 (async) + Alembic migrations
- **Auth**: JWT (access + refresh tokens) with bcrypt password hashing
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx (async) + aiosqlite (in-memory)
- **CI**: GitHub Actions (lint + typecheck + test + Docker build)

## Quick Start

### Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env — change JWT_SECRET_KEY!
docker compose up --build
```

API available at http://localhost:8000

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Start PostgreSQL (or use docker compose up db)
# Update DATABASE_URL in .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, get token pair |
| POST | `/api/v1/auth/refresh` | Refresh token pair |
| POST | `/api/v1/auth/logout` | Revoke refresh token |

### Users (requires auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PATCH | `/api/v1/users/me` | Update current user |
| DELETE | `/api/v1/users/me` | Delete current user |
| GET | `/api/v1/users` | List users (paginated) |
| GET | `/api/v1/users/{id}` | Get user by ID |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Testing

```bash
# Run all tests
pytest -v

# With coverage
coverage run -m pytest && coverage report
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `JWT_SECRET_KEY` | Yes | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | No | Default: HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: 15 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | Default: 7 |

## Architecture

- **12-Factor compliant**: config from env, stateless processes, logs to stdout, port binding, graceful shutdown
- **CAP**: PostgreSQL (CP) — consistency + partition tolerance. Under network partition, writes fail rather than risk inconsistency.
- **Security**: bcrypt password hashing, JWT with token rotation, refresh token revocation, no secrets in code
