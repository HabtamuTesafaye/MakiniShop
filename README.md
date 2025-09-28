# MakiniShop

MakiniShop is a modular, scalable, AI-powered e-commerce backend built with Django. It supports product catalog, personalized recommendations, orders, payments, notifications, and more—ready for production and extensibility.

---

## 🏗️ Monorepo Structure

```
makinishop/
├── ai/              # AI, recommendations, embeddings, feedback
├── audit/           # Audit logs for admin/user actions
├── catalog/         # Products, categories, variants, reviews, wishlists
├── makinishop/      # Django project config (settings, URLs, celery)
├── notifications/   # Notification templates, queue, delivery (email/SMS)
├── orders/          # Carts, orders, payments, shipping, discounts
├── user_events/     # User event tracking (views, carts, purchases)
├── users/           # User accounts, RBAC, profiles, addresses
├── ...
```

### App/Module Overview

- **ai/**: Product/user embeddings, personalized recommendations, feedback, hybrid ranking logic.
- **audit/**: Tracks admin and user actions for compliance and debugging.
- **catalog/**: Product catalog, categories, variants, reviews, wishlists, featured products.
- **notifications/**: Notification templates, user preferences, async queue, Celery tasks for email/SMS.
- **orders/**: Cart, order, payment, shipping, discount, refund logic.
- **user_events/**: Tracks user behavior for analytics and AI.
- **users/**: Custom user model (email login), RBAC (roles/permissions), profiles, addresses.

---

## ⚙️ Tech Stack

| Layer         | Technology                | Purpose/Role                                      |
|---------------|---------------------------|---------------------------------------------------|
| Backend       | Django 4.x                | Main web framework, ORM, admin                     |
| API           | Django REST Framework     | RESTful APIs, permissions, serialization           |
| Auth          | SimpleJWT, django-guardian| JWT auth, RBAC, object-level permissions           |
| Database      | PostgreSQL 15+            | Relational DB, pgvector for embeddings, pg_trgm    |
| Async/Queue   | Celery 5+, RabbitMQ, Redis| Background tasks (emails, AI, notifications)       |
| Caching       | Redis                     | Caching, Celery result backend                     |
| Media         | Cloudinary                | Image upload, CDN, optimization                    |
| Docs          | drf-yasg                  | Swagger/OpenAPI docs                               |
| Security      | django-csp, bleach        | CSP headers, HTML sanitization                     |
| Monitoring    | Sentry                    | Error monitoring                                   |
| DevOps        | Docker, Docker Compose    | Local/prod orchestration                           |
| CI/CD         | Jenkins                   | Automated builds, tests, deploy                    |
| Testing       | pytest, pytest-django     | Automated testing                                  |

---

## 📦 Environment Variables

All required keys are documented in [`.env.example`](.env.example).  
**You must copy this file to `.env` and fill in your secrets.**

**Key variables (see `.env.example` for full list):**
- `POSTGRES_*` (DB config)
- `REDIS_*` (cache/broker config)
- `RABBITMQ_*` (broker config)
- `DJANGO_SECRET_KEY`
- `ALLOWED_HOSTS`
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `SENTRY_DSN`
- `BASE_URL`
- Email provider keys (e.g., `SENDGRID_API_KEY`)
- `CORS_ALLOWED_ORIGINS`

---

## 🚀 Quickstart

1. **Clone and configure:**
    ```bash
    git clone https://github.com/your-org/makinishop.git
    cd makinishop
    cp .env.example .env
    # Edit .env with your secrets
    ```

2. **Start infrastructure:**
    ```bash
    docker-compose up -d postgres redis rabbitmq jenkins celery_worker celery_beat
    ```

3. **Run Django locally:**
    ```bash
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
    ```

4. **Run tests:**
    ```bash
    pytest
    ```

---

## 🔒 Security & Permissions

- **JWT authentication** for all APIs (except signup/login/password reset).
- **RBAC**: Role-based access for admin/management endpoints.
- **Rate limiting** and **IP blocking** on sensitive endpoints.
- **CSP** and **bleach** for XSS protection.
- **Sentry** for error monitoring.

---

## 📚 API & Docs

- **REST**: `/api/` endpoints for all resources.
- **Swagger**: `/swagger/` (public by default, can be restricted).

---

## 🧩 Extending & Contributing

- Each app is modular and can be extended independently.
- Add new endpoints, Celery tasks, or models as needed.
- PRs and issues welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 Project Status

- **Production-ready**: All core features implemented, security best practices enforced.
- **Deployment**: Add Django service to Docker Compose when ready for production.
- **Monitoring**: Sentry enabled if `SENTRY_DSN` is set.

---

