# 📚 Local Library

A full-featured library management system built with **Django 6** and **Django REST Framework**. Users can browse books, borrow or reserve copies, and track their loan history through both a classic web UI and a REST API. Librarians get a fine-grained permission layer to manage inventory, renewals, and returns.

🌐 **Live demo:** [https://locallibrary.me/](https://locallibrary.me/)  
📖 **API docs (Swagger):** [https://locallibrary.me/api/schema/swagger/](https://locallibrary.me/api/schema/swagger/)  
📄 **API docs (ReDoc):** [https://locallibrary.me/api/schema/redoc/](https://locallibrary.me/api/schema/redoc/)

---

## ✨ Features

- **Book & Author catalog** — CRUD with image uploads (auto-resized via Pillow)
- **Borrow / Reserve system** — atomic transactions, overdue tracking, loan history
- **REST API** — full DRF-based API with JWT authentication, filtering, pagination, and throttling
- **OpenAPI schema** — auto-generated docs via `drf-spectacular` (Swagger UI & ReDoc)
- **Celery scheduled tasks** — daily reminders for expiring loans, automatic reservation cleanup
- **Authentication** — email-based login, Google & GitHub OAuth via `django-allauth`; JWT cookies via `dj-rest-auth`
- **Custom User model** — email as `USERNAME_FIELD`, extended profile with avatar & role
- **Redis caching** — versioned list cache with automatic invalidation (web UI & DRF views)
- **Cloudflare R2** — static & media file storage (S3-compatible, served via CDN)
- **Docker-first** — separate Compose configs for dev (hot-reload) and prod (Gunicorn + Caddy)
- **CI/CD** — GitHub Actions pipeline: lint → type-check → security scan → tests → deploy to DigitalOcean
- **Django Silk** — query profiling in development only

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Python 3.12 |
| REST API | Django REST Framework, dj-rest-auth, drf-spectacular |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task queue | Celery 5 + Celery Beat |
| Auth | django-allauth (Google, GitHub), JWT (SimpleJWT) |
| Storage | Cloudflare R2 (django-storages / boto3) |
| Reverse proxy | Caddy 2 (automatic HTTPS) |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Containerization | Docker, Docker Compose |
| Linting / Formatting | Ruff |
| Type checking | Mypy |
| Security | Bandit |
| Testing | pytest, pytest-django, factory-boy |
| CI/CD | GitHub Actions → DigitalOcean |

---

## 📁 Project Structure

```
.
├── compose.yaml                    # Dev environment
├── compose.prod.yaml               # Prod environment (Gunicorn + Caddy)
├── Dockerfile
├── Dockerfile.prod
├── Caddyfile                       # Caddy reverse proxy config
├── pyproject.toml
├── uv.lock
└── locallibrary/
    ├── manage.py
    ├── locallibrary/               # Project config (settings, urls, celery_app, wsgi, asgi)
    ├── catalog/                    # Books, Authors, BookInstances, Loans
    │   ├── models.py
    │   ├── views.py                # Server-rendered views
    │   ├── services.py             # Business logic (borrow, return, renew)
    │   ├── forms.py
    │   ├── signals.py
    │   ├── api/                    # REST API (ViewSets, serializers, filters, permissions)
    │   │   ├── views.py
    │   │   ├── serializers/
    │   │   ├── filters.py
    │   │   ├── permissions.py
    │   │   └── urls.py
    │   ├── tasks/
    │   │   ├── image_tasks.py      # Async image processing
    │   │   ├── notification_tasks.py
    │   │   └── periodic_tasks.py   # Celery Beat scheduled tasks
    │   ├── management/commands/
    │   │   └── seed_db.py          # Dev database seeder
    │   └── tests/
    │       ├── helper/             # Factories & mixins
    │       ├── test_models.py
    │       ├── test_forms.py
    │       ├── test_signals.py
    │       ├── tasks/
    │       └── tests_views/
    ├── user/                       # CustomUser, UserProfile, OAuth
    │   ├── models.py
    │   ├── adapters.py             # django-allauth social adapter
    │   ├── managers.py
    │   ├── signals.py
    │   ├── api/                    # User REST API
    │   └── tests/
    │       ├── test_models.py
    │       ├── test_views.py
    │       ├── test_adapters.py
    │       ├── test_managers.py
    │       ├── test_signals.py
    │       ├── test_forms.py
    │       └── test_tasks.py
    └── common/                     # Shared helpers
        ├── cache.py                # Versioned cache mixin (web + DRF)
        ├── image.py                # Image processing utilities
        ├── mixins.py               # MultiSerializerMixin, MultiPermissionMixin
        ├── pagination.py           # Custom DRF pagination
        ├── permissions.py          # StrictDjangoModelPermissions
        ├── tasks.py
        └── validators.py
```

---

## 🌐 REST API

The API is available at `/api/catalog/` and `/api/users/`. Authentication endpoints live at `/api/auth/`.

| Resource | Endpoint | Notes |
|---|---|---|
| Books | `GET/POST /api/catalog/books/` | Public read, staff write |
| Book detail | `GET/PUT/DELETE /api/catalog/books/{id}/` | |
| Authors | `/api/catalog/authors/` | Protected delete (cascades) |
| Genres | `/api/catalog/genres/` | |
| Languages | `/api/catalog/languages/` | |
| Book Instances | `/api/catalog/instances/` | Filtered by user role |
| My loans | `GET /api/catalog/instances/my/` | Authenticated users only |
| Borrow / Reserve | `POST /api/catalog/actions/{id}/borrow_or_reserve/` | |
| Borrow reserved | `POST /api/catalog/actions/{id}/borrow_reserved/` | |
| Return | `POST /api/catalog/actions/{id}/return_book/` | Requires `can_mark_returned` |
| Extend loan | `PATCH /api/catalog/actions/{id}/extend_loan/` | Requires `can_change_due_back` |
| Loans (read-only) | `/api/catalog/loans/` | Staff only |
| Login / Logout | `/api/auth/login/`, `/api/auth/logout/` | JWT cookie |
| Registration | `/api/auth/registration/` | |

**Authentication:** JWT stored in HttpOnly cookies (`local-library-auth` / `local-library-refresh-token`).  
**Throttling:** Anonymous — 100 req/day; Authenticated — 1000 req/day.  
**Filtering:** Available on books (title, author, genre, language), authors, instances, and loans.

---

## 🚀 Getting Started (Development)

### Prerequisites

- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (optional, for local runs without Docker)

### 1. Clone the repo

```bash
git clone https://github.com/VasylHlova/localLibrary.git
cd localLibrary
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values (see [Environment Variables](#-environment-variables)).

### 3. Start with Docker Compose

```bash
docker compose up
```

This will:
- Start PostgreSQL and Redis
- Run migrations and seed the database (`seed_db`)
- Start the Django dev server on [http://localhost:8001](http://localhost:8001)
- Start Celery worker and Celery Beat

Hot-reload is enabled via Docker Compose Watch — changes to source files are synced automatically. Rebuilds only trigger on changes to `pyproject.toml` or `uv.lock`.

---

## 🏭 Production Deployment

The production stack runs on **DigitalOcean** and is deployed automatically via GitHub Actions on every push to `master`.

**Services (compose.prod.yaml):**

| Service | Description |
|---|---|
| `server` | Gunicorn (3 workers, WSGI) |
| `caddy` | Reverse proxy with automatic HTTPS (ports 80/443) |
| `prod_db` | PostgreSQL 16 |
| `redis` | Redis 7 |
| `celery_worker` | Celery worker |
| `celery_beat` | Celery Beat scheduler |

**Manual deploy:**

```bash
docker compose -f compose.prod.yaml up -d --build
docker compose -f compose.prod.yaml exec server python manage.py migrate
docker compose -f compose.prod.yaml exec server python manage.py collectstatic --noinput
```

> ⚠️ Make sure `.env` is configured with `DEBUG=False` and proper secrets before deploying.

---

## ⚙️ CI/CD (GitHub Actions)

The pipeline in `.github/workflows/ci-cd.yaml` runs on every push/PR to `master`:

1. **Ruff format check** — `ruff format --check`
2. **Ruff lint** — `ruff check`
3. **Mypy type check** — `mypy locallibrary/`
4. **Bandit security scan** — `bandit -r locallibrary/`
5. **Migration check** — `makemigrations --check --dry-run`
6. **Pytest** — full test suite with PostgreSQL + Redis services
7. **Deploy** *(master only)* — SSH into DigitalOcean, pull, rebuild containers, migrate, collectstatic

---

## 🔑 Environment Variables

Create a `.env` file based on the table below:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
SITE_URL=http://localhost:8001
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# PostgreSQL
ENGINE=django.db.backends.postgresql
POSTGRES_DB=library
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=db

# Cloudflare R2
CLOUDFLARE_R2_BUCKET=your-bucket-name
CLOUDFLARE_R2_ACCESS_KEY=your-access-key
CLOUDFLARE_R2_SECRET_KEY=your-secret-key
CLOUDFLARE_R2_BUCKET_ENDPOINT=https://<account>.r2.cloudflarestorage.com
CLOUDFLARE_R2_DOMAIN=your-public-domain.r2.dev

# Google OAuth
GOOGLE_CLIENT=your-google-client-id
GOOGLE_SECRET=your-google-secret

# GitHub OAuth
GITHUB_CLIENT=your-github-client-id
GITHUB_SECRET=your-github-secret

# Email (Gmail SMTP)
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL_CACHE=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/2
CELERY_RESULT_BACKEND=redis://redis:6379/3
```

> ⚠️ Never commit `.env` to version control.

---

## ⚙️ Celery Scheduled Tasks

| Task | Schedule | Description |
|---|---|---|
| `catalog.check_expiring_loans` | Daily at 08:00 | Sends email reminders for loans due soon |
| `catalog.update_status_on_exipiring_reservetion_date` | Daily at 01:00 | Cancels expired reservations |

---

## 🔐 Permissions

| Permission | Description |
|---|---|
| `catalog.add_book` / `catalog.change_book` | Create / edit books |
| `catalog.add_author` / `catalog.change_author` | Create / edit authors |
| `catalog.can_mark_returned` | Mark a book as returned |
| `catalog.can_change_status` | Change any book instance status |
| `catalog.can_change_due_back` | Extend a loan's due date |
| `catalog.view_bookinstance` | View all borrowed books (staff) |

---

## 🧷 Testing

Tests are written with **pytest** + **pytest-django** and **factory-boy** for generating test data. Both `catalog` and `user` apps have dedicated test suites with full coverage across all layers.

**What's tested:**

- **Models** — field labels, max lengths, `full_clean()` validation (image extensions, file size, date logic), DB-level `CheckConstraint` and `UniqueConstraint`, `borrow_book()` / `return_book()` / `close_loan()` business logic
- **Views** — all CRUD views, borrow/reserve/return flows, permission checks (web UI)
- **API** — DRF ViewSets, serializers, permissions, filters (REST API)
- **Forms** — form validation and field behaviour
- **Signals** — signal handlers fire correctly
- **Celery tasks** — image processing, email notifications, periodic cleanup tasks
- **Auth** — custom managers, social account adapter, allauth integration

```bash
# Run all tests (inside Docker)
docker compose exec server pytest

# Run specific app
docker compose exec server pytest catalog/tests/
docker compose exec server pytest user/tests/

# Run with coverage
docker compose exec server pytest --cov
```

---

## 🧪 Development Tools

```bash
# Linting & formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy locallibrary/

# Security scan
uv run bandit -c pyproject.toml -r locallibrary/

# Django shell
docker compose exec server python locallibrary/manage.py shell

# Create superuser
docker compose exec server python locallibrary/manage.py createsuperuser

# Collect static (prod)
docker compose exec server python locallibrary/manage.py collectstatic --noinput
```

Django Silk is enabled in development. Access the profiling dashboard at [http://localhost:8001/silk/](http://localhost:8001/silk/).

Pre-commit hooks (Ruff + Mypy) are configured in `.pre-commit-config.yaml`:

```bash
pre-commit install
```

---

## 📄 License

MIT
