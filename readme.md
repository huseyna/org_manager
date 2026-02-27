# 🏢 Org Manager API

A **Department & Employee Management REST API** built. Features recursive department trees, strict validation, and a Docker-first startup pipeline that won't serve traffic until migrations and tests pass.

---

## 🛠 Tech Stack

Python 3.12 · Django 6 · Django REST Framework · PostgreSQL 16 · Pytest · drf-spectacular (OpenAPI 3) · Docker · `django-stubs` (strict type safety)

---

## 🚀 Getting Started

```bash
git clone <repo-url>
cd org_manager
cp .env.example .env      # adjust values if needed
docker compose up --build
```

The pipeline runs automatically — visit **`http://localhost:8000/`** and you'll be redirected to the Swagger UI.

---

## 🔒 Startup Pipeline (Gatekeeper Flow)

The `web` server **only starts if all prior stages succeed** — no broken builds ever reach traffic.

```
db (healthcheck) → migrate (check + migrate) → test (pytest) → web (runserver)
```

| Stage | Condition | Action |
|---|---|---|
| `db` | `pg_isready` healthcheck | Starts PostgreSQL 16 |
| `migrate` | `db` healthy | Runs `manage.py check` then `migrate --noinput` |
| `test` | `migrate` completed successfully | Runs full `pytest` suite |
| `web` | `test` completed successfully | Starts Django on port `8000` |

---

## 📡 API Overview

Interactive docs at **`/docs/`** (Swagger UI) — auto-generated via drf-spectacular.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/departments/` | Create a department |
| `GET` | `/departments/{id}/` | Get department + employees + subtree |
| `PATCH` | `/departments/{id}/` | Rename or move department |
| `DELETE` | `/departments/{id}/` | Delete (cascade or reassign employees) |
| `POST` | `/departments/{id}/employees/` | Add employee to department |

### Query Parameters

| Param | Endpoint | Default | Description |
|---|---|---|---|
| `depth` | `GET /departments/{id}/` | `1` (max `5`) | Levels of nested `children` to return |
| `include_employees` | `GET /departments/{id}/` | `true` | Set to `false` to omit employee lists |
| `mode` | `DELETE /departments/{id}/` | — | `cascade` or `reassign` |
| `reassign_to_department_id` | `DELETE /departments/{id}/` | — | Required when `mode=reassign` |

---

## ✅ Validation & Business Logic

- **Unique names per parent** — enforced at both the serializer and DB level (`UniqueConstraint`). Root-level names are also globally unique.
- **Whitespace trimming** — `trim_whitespace=True` on all `CharField`s; lengths validated 1–200.
- **Self-parent guard** — a department cannot be set as its own parent (`400`).
- **Cycle detection** — on every `PATCH`, the ancestor chain of the proposed parent is walked upward; if the current instance is found, the move is rejected (`409 Conflict`).
- **Recursive depth** — children are serialized up to `depth=5` via a `current_lvl` counter threaded through serializer context.
- **Field-targeted errors** — validation uses `validate()` instead of `validate_<field>()` to return errors under specific keys (e.g. `{"name": "..."}`) rather than `non_field_errors`.

---

## 🔧 Useful Commands

```bash
# Run tests
docker compose exec web pytest -v

# Django shell
docker compose exec web python manage.py shell

# Create migrations
docker compose exec web python manage.py makemigrations

# Export OpenAPI schema
docker compose exec web python manage.py spectacular --output schema.yaml
```



