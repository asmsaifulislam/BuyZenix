# BuyZenix

A modern e-commerce platform built with **Django**, **PostgreSQL**, **Redis**, **Celery**, **Nginx** and **Docker**.

Brand theme: dark background with an electric-blue accent (derived from the supplied brand images).

## Stack
- **Django 5.1** — web framework & admin
- **PostgreSQL 16** — primary database
- **Redis 7** — cache + Celery message broker
- **Celery** — async order confirmation emails
- **Nginx** — reverse proxy + static/media serving
- **Gunicorn** — WSGI server
- **Docker Compose** — full orchestration

## Features
- Product catalog with categories, search and detail pages
- Session-based shopping cart
- Checkout flow + order creation
- User accounts (register, login, profile, order history)
- Async order confirmation email via Celery + Redis
- Django admin for catalog & order management
- Responsive dark UI

## Quick start (Docker)

```bash
# 1. (optional) adjust .env values
cp .env .env.local   # edit as needed

# 2. Build and run
docker compose up --build

# 3. Open the app
http://localhost:8000
```

The app seeds a sample catalog on first run and creates a superuser:

- Admin: `http://localhost:8000/admin/` — `admin` / `admin12345`
- Storefront: `http://localhost:8000/`

> Nginx exposes port **8000** on the host (mapped to container port 80) to avoid
> clashing with common local services. Change the `ports` mapping in
> `docker-compose.yml` if you prefer `80:80`.

## Useful commands

```bash
docker compose exec web python manage.py seed      # re-seed sample data
docker compose exec web python manage.py createsuperuser
docker compose logs -f celery                       # watch async tasks
```

## Run locally (no Docker / Postgres / Redis required)

The project can run on localhost using SQLite + an in-memory cache. A Celery
worker is optional (order emails simply queue in memory and are skipped if no
worker is running).

```bash
cd app
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
set RUN_LOCAL=1                  # use SQLite + LocMem cache
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` (storefront) and `http://127.0.0.1:8000/admin/`.


## Project layout

```
BuyZenix/
├── docker-compose.yml
├── .env
├── nginx/nginx.conf
└── app/
    ├── Dockerfile
    ├── entrypoint.sh
    ├── requirements.txt
    ├── manage.py
    ├── buyzenix/        # settings, urls, wsgi, celery
    ├── core/            # categories & products
    ├── cart/            # session-based cart
    ├── accounts/        # auth & profiles
    ├── orders/          # checkout & orders (+ Celery task)
    ├── templates/
    └── static/
```

## Notes
- Email backend is set to the console backend by default (emails print to logs).
  Configure `EMAIL_*` settings for real delivery.
- `DEBUG=1` in `.env`; set `DEBUG=0` and a real `SECRET_KEY` for production.
