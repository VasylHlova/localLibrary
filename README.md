# 📚 Local Library

A full-featured library management system built with Django 6. Users can browse books, borrow or reserve copies, and track their loan history. Librarians get a separate permission layer to manage inventory, renewals, and returns.

---

## ✨ Features

- **Book & Author catalog** — CRUD with image uploads (auto-resized via Pillow)
- **Borrow / Reserve system** — atomic transactions, overdue tracking, loan history
- **Celery scheduled tasks** — daily reminders for expiring loans, automatic reservation cleanup
- **Authentication** — email-based login, Google & GitHub OAuth via `django-allauth`
- **Custom User model** — email as USERNAME_FIELD, extended profile with avatar & role
- **Redis caching** — versioned list cache with automatic invalidation
- **Cloudflare R2** — static & media file storage (S3-compatible)
- **Django Silk** — query profiling in development
- **Docker-first** — separate Compose configs for dev (hot-reload) and prod (Gunicorn)

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Python 3.12 |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task queue | Celery 5 + Celery Beat |
| Auth | django-allauth (Google, GitHub) |
| Storage | Cloudflare R2 (django-storages / boto3) |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Containerization | Docker, Docker Compose |
| Linting | Ruff |

---

## 📁 Project Structure

```
.
├── compose.yaml                    # Dev environment
├── compose.prod.yaml               # Prod environment
├── Dockerfile
├── Dockerfile.prod
├── pyproject.toml
├── uv.lock
└── locallibrary/
    ├── manage.py
    ├── locallibrary/               # Project config (settings, urls, wsgi, asgi)
    ├── infrastructure/             # Celery app init
    ├── catalog/                    # Books, Authors, BookInstances, Loans
    │   ├── models.py
    │   ├── views.py
    │   ├── forms.py
    │   ├── signals.py
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
    │       ├── tasks/              # Task tests
    │       └── tests_views/        # View tests per entity
    ├── user/                       # CustomUser, UserProfile, OAuth
    │   ├── models.py
    │   ├── adapters.py             # django-allauth social adapter
    │   ├── managers.py
    │   ├── signals.py
    │   ├── tasks/
    │   │   └── profile_picture_tasks.py
    │   └── tests/
    │       ├── test_models.py
    │       ├── test_views.py
    │       ├── test_adapters.py
    │       ├── test_managers.py
    │       ├── test_signals.py
    │       ├── test_forms.py
    │       └── test_tasks.py
    └── utils/                      # Shared helpers
        ├── cache.py                # Versioned cache mixin
        ├── choices.py
        ├── image_proccess.py
        └── validators.py
```

---

## 🚀 Getting Started (Development)

### Prerequisites

- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (optional, for local runs without Docker)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/local-library.git
cd local-library
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
- Start PostgreSQL, Redis
- Run migrations and seed the database (`seed_db`)
- Start the Django dev server on [http://localhost:8000](http://localhost:8000)
- Start Celery worker and Celery Beat

Hot-reload is enabled — changes to source files are synced automatically. Rebuilds only trigger on changes to `pyproject.toml` or `uv.lock`.

---

## 🏭 Production Deployment

```bash
docker compose -f compose.prod.yaml up -d
```

Production uses `Dockerfile.prod` with Gunicorn. Make sure `.env.prod` is configured with `DEBUG=False` and proper secrets.

---

## 🔑 Environment Variables

Create a `.env` file based on the table below:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

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

> ⚠️ Never commit `.env` or `.env.prod` to version control.

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
| `catalog.view_bookinstance` | View all borrowed books (staff) |

---

## 🧷 Testing

Tests are written with Django's built-in `TestCase` and `factory-boy` for generating test data. Both `catalog` and `user` apps have dedicated test suites with full coverage across all layers.

**What's tested:**

- **Models** — field labels, max lengths, `full_clean()` validation (image extensions, file size, date logic), DB-level `CheckConstraint` and `UniqueConstraint`, `borrow_book()` / `return_book()` / `close_loan()` business logic
- **Views** — all CRUD views, borrow/reserve/return flows, permission checks
- **Forms** — form validation and field behaviour
- **Signals** — signal handlers fire correctly
- **Celery tasks** — image processing, email notifications, periodic cleanup tasks
- **Auth** — custom managers, social account adapter, allauth integration

```bash
# Run all tests
docker compose exec server python locallibrary/manage.py test

# Run specific app
docker compose exec server python locallibrary/manage.py test catalog
docker compose exec server python locallibrary/manage.py test user
```

---

## 🧪 Development Tools

```bash
# Linting
uv run ruff check .
uv run ruff format .

# Django shell
docker compose exec server python locallibrary/manage.py shell

# Create superuser
docker compose exec server python locallibrary/manage.py createsuperuser

# Collect static (prod)
docker compose exec server python locallibrary/manage.py collectstatic --noinput
```

Django Silk is enabled in development. Access the profiling dashboard at [http://localhost:8000/silk/](http://localhost:8000/silk/).

---

## 📄 License

MIT
