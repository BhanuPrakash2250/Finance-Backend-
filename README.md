# Finance Data Processing & Access Control System

A clean, production-ready REST API built with **Django REST Framework**, featuring
role-based access control (RBAC), JWT authentication, financial record management,
and an analytics dashboard.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Tech Stack](#tech-stack)
3. [Setup Instructions](#setup-instructions)
4. [Test Credentials](#test-credentials)
5. [API Endpoints](#api-endpoints)
6. [Sample Requests & Responses](#sample-requests--responses)
7. [Role Permissions Matrix](#role-permissions-matrix)
8. [Design Decisions](#design-decisions)

---

## Project Structure

```
finance_system/
│
├── finance_project/           # Django project config
│   ├── __init__.py
│   ├── settings.py            # All settings (JWT, DRF, DB, Swagger)
│   ├── urls.py                # Root URL dispatcher
│   └── wsgi.py
│
├── apps/                      # All Django applications
│   ├── users/                 # User & auth management
│   │   ├── models.py          # Custom User model with roles
│   │   ├── serializers.py     # Registration, login, profile, password
│   │   ├── views.py           # Auth + admin user CRUD endpoints
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── records/               # Financial records (CRUD)
│   │   ├── models.py          # FinancialRecord model
│   │   ├── serializers.py     # Read / write serializers
│   │   ├── views.py           # List, create, retrieve, update, delete
│   │   ├── filters.py         # django-filter FilterSet
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py   # Load sample data
│   │
│   └── dashboard/             # Analytics endpoints
│       ├── views.py           # Summary, category, trends, recent
│       ├── urls.py
│       └── apps.py
│
├── core/                      # Shared infrastructure
│   ├── middleware/
│   │   └── audit.py           # Request audit logging
│   ├── permissions/
│   │   └── rbac.py            # IsAdmin, IsAnalystOrAbove, IsViewerOrAbove
│   └── utils/
│       ├── pagination.py      # StandardResultsPagination
│       └── exceptions.py      # Custom error envelope handler
│
├── manage.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Tech Stack

| Component        | Technology                          |
|------------------|-------------------------------------|
| Language         | Python 3.10+                        |
| Framework        | Django 4.2 + Django REST Framework  |
| Authentication   | JWT via `djangorestframework-simplejwt` |
| Database         | SQLite (dev) / PostgreSQL (prod)    |
| Filtering        | django-filter                       |
| API Docs         | drf-yasg (Swagger + ReDoc)          |
| Config           | python-decouple (.env support)      |

---

## Setup Instructions

### Step 1 — Clone and enter the project

```bash
git clone <repo-url>
cd finance_system
```

### Step 2 — Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

```bash
cp .env.example .env
# Edit .env if needed (defaults work fine for development)
```

### Step 5 — Run database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6 — Seed sample data (users + records)

```bash
python manage.py seed_data

# To wipe and re-seed:
python manage.py seed_data --clear
```

### Step 7 — Start the development server

```bash
python manage.py runserver
```

The API is now running at: **http://127.0.0.1:8000**

### Step 8 — Open the interactive API docs

- **Swagger UI:** http://127.0.0.1:8000/swagger/
- **ReDoc:**      http://127.0.0.1:8000/redoc/

---

## Test Credentials

After running `seed_data`, these accounts are ready to use:

| Role     | Email                  | Password     | Access Level                    |
|----------|------------------------|--------------|----------------------------------|
| Admin    | admin@finance.com      | Admin@123    | Full CRUD + dashboard + users   |
| Analyst  | analyst@finance.com    | Analyst@123  | Read records + full dashboard   |
| Viewer   | viewer@finance.com     | Viewer@123   | Read own records only           |

---

## API Endpoints

### Authentication

| Method | Endpoint                      | Access  | Description                    |
|--------|-------------------------------|---------|--------------------------------|
| POST   | `/api/auth/login/`            | Public  | Login, returns JWT tokens      |
| POST   | `/api/auth/logout/`           | Any     | Blacklist refresh token        |
| POST   | `/api/auth/token/refresh/`    | Public  | Get new access token           |
| GET    | `/api/auth/me/`               | Any     | Get own profile                |
| PUT    | `/api/auth/me/`               | Any     | Update own name                |
| POST   | `/api/auth/me/password/`      | Any     | Change own password            |

### User Management (Admin only)

| Method | Endpoint                      | Access  | Description                    |
|--------|-------------------------------|---------|--------------------------------|
| GET    | `/api/auth/users/`            | Admin   | List all users (paginated)     |
| POST   | `/api/auth/users/`            | Admin   | Create a new user              |
| GET    | `/api/auth/users/<id>/`       | Admin   | Get user detail                |
| PUT    | `/api/auth/users/<id>/`       | Admin   | Update user role / status      |
| DELETE | `/api/auth/users/<id>/`       | Admin   | Deactivate user (soft)         |

### Financial Records

| Method | Endpoint                      | Access           | Description                    |
|--------|-------------------------------|------------------|--------------------------------|
| GET    | `/api/records/`               | Viewer+          | List records (filtered, paged) |
| POST   | `/api/records/`               | Admin            | Create a new record            |
| GET    | `/api/records/<id>/`          | Viewer+          | Get record detail              |
| PUT    | `/api/records/<id>/`          | Admin            | Update a record                |
| PATCH  | `/api/records/<id>/`          | Admin            | Partial update                 |
| DELETE | `/api/records/<id>/`          | Admin            | Soft-delete a record           |

**Record Filters (query params):**

| Param        | Example                      | Description              |
|--------------|------------------------------|--------------------------|
| `type`       | `?type=income`               | Filter by income/expense |
| `category`   | `?category=salary`           | Filter by category       |
| `date_from`  | `?date_from=2024-01-01`      | Records on or after date |
| `date_to`    | `?date_to=2024-03-31`        | Records on or before date|
| `amount_min` | `?amount_min=100`            | Minimum amount           |
| `amount_max` | `?amount_max=5000`           | Maximum amount           |
| `search`     | `?search=salary`             | Full-text search (notes, category) |
| `ordering`   | `?ordering=-amount`          | Sort by field            |
| `page`       | `?page=2`                    | Page number              |
| `page_size`  | `?page_size=10`              | Items per page (max 100) |

### Dashboard (Analyst + Admin)

| Method | Endpoint                           | Description                         |
|--------|------------------------------------|-------------------------------------|
| GET    | `/api/dashboard/summary/`          | Income, expenses, net balance       |
| GET    | `/api/dashboard/category-summary/` | Breakdown by category               |
| GET    | `/api/dashboard/monthly-trends/`   | Month-by-month trends               |
| GET    | `/api/dashboard/recent-records/`   | Last N records (`?limit=10`)        |

**Dashboard Filters:**
All dashboard endpoints accept `?date_from=` and `?date_to=` for date-range analytics.

---

## Sample Requests & Responses

### 1. Login

**Request:**
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "email": "admin@finance.com",
  "password": "Admin@123"
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "admin@finance.com",
      "first_name": "Alice",
      "last_name": "Administrator",
      "full_name": "Alice Administrator",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-03-01T10:00:00Z"
    },
    "tokens": {
      "access":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
}
```

---

### 2. Create a Financial Record (Admin)

**Request:**
```bash
POST /api/records/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": "3500.00",
  "type": "income",
  "category": "freelance",
  "date": "2024-03-15",
  "notes": "Mobile app development project"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "message": "Record created.",
  "data": {
    "id": 18,
    "amount": "3500.00",
    "type": "income",
    "category": "freelance",
    "date": "2024-03-15",
    "notes": "Mobile app development project",
    "created_by": 1,
    "created_by_name": "Alice Administrator",
    "created_at": "2024-03-15T14:30:00Z",
    "updated_at": "2024-03-15T14:30:00Z"
  }
}
```

---

### 3. List Records with Filters

**Request:**
```bash
GET /api/records/?type=expense&category=groceries&date_from=2024-01-01&ordering=-amount&page=1&page_size=5
Authorization: Bearer <access_token>
```

**Response `200 OK`:**
```json
{
  "pagination": {
    "count": 3,
    "total_pages": 1,
    "current_page": 1,
    "next": null,
    "previous": null
  },
  "results": [
    {
      "id": 7,
      "amount": "340.00",
      "type": "expense",
      "category": "groceries",
      "date": "2024-03-10",
      "notes": "Weekly grocery shopping",
      "created_by_name": "Alice Administrator",
      "created_at": "2024-03-10T09:00:00Z"
    }
  ]
}
```

---

### 4. Dashboard Summary

**Request:**
```bash
GET /api/dashboard/summary/?date_from=2024-01-01&date_to=2024-03-31
Authorization: Bearer <access_token>
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "total_income": 12750.00,
    "total_expenses": 2940.00,
    "net_balance": 9810.00,
    "total_records": 17,
    "income_count": 7,
    "expense_count": 10,
    "filters_applied": {
      "date_from": "2024-01-01",
      "date_to": "2024-03-31"
    }
  }
}
```

---

### 5. Monthly Trends

**Request:**
```bash
GET /api/dashboard/monthly-trends/
Authorization: Bearer <access_token>
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "total_months": 3,
    "monthly_trends": [
      {
        "month": "2024-01",
        "income": 5450.00,
        "expenses": 980.00,
        "net": 4470.00,
        "income_count": 3,
        "expense_count": 4
      },
      {
        "month": "2024-02",
        "income": 5000.00,
        "expenses": 1200.00,
        "net": 3800.00,
        "income_count": 2,
        "expense_count": 3
      },
      {
        "month": "2024-03",
        "income": 2300.00,
        "expenses": 760.00,
        "net": 1540.00,
        "income_count": 2,
        "expense_count": 3
      }
    ]
  }
}
```

---

### 6. Category Summary

**Request:**
```bash
GET /api/dashboard/category-summary/?type=expense
Authorization: Bearer <access_token>
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "grand_total": 2940.00,
    "breakdown": [
      { "category": "rent",       "type": "expense", "total": 1200.00, "count": 1, "percentage": 40.82 },
      { "category": "travel",     "type": "expense", "total": 890.00,  "count": 1, "percentage": 30.27 },
      { "category": "groceries",  "type": "expense", "total": 340.00,  "count": 1, "percentage": 11.56 },
      { "category": "shopping",   "type": "expense", "total": 200.00,  "count": 1, "percentage": 6.80  },
      { "category": "healthcare", "type": "expense", "total": 150.00,  "count": 1, "percentage": 5.10  },
      { "category": "transport",  "type": "expense", "total": 120.00,  "count": 1, "percentage": 4.08  }
    ]
  }
}
```

---

### 7. Validation Error Response

**Request:**
```bash
POST /api/records/
Authorization: Bearer <access_token>

{ "amount": -500, "type": "unknown" }
```

**Response `400 Bad Request`:**
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid request data. Please check the details and try again.",
    "details": {
      "amount":   ["Amount must be a positive number."],
      "type":     ["Type must be one of: income, expense."],
      "category": ["This field is required."],
      "date":     ["This field is required."]
    }
  }
}
```

---

### 8. Permission Denied (Viewer tries to create)

**Response `403 Forbidden`:**
```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "Only Administrators can modify records.",
    "details": { "detail": "Only Administrators can modify records." }
  }
}
```

---

## Role Permissions Matrix

| Endpoint                       | Viewer | Analyst | Admin |
|--------------------------------|:------:|:-------:|:-----:|
| Login / Logout / Token Refresh |   ✅   |   ✅    |  ✅   |
| View own profile               |   ✅   |   ✅    |  ✅   |
| Change own password            |   ✅   |   ✅    |  ✅   |
| List financial records         |   ✅*  |   ✅    |  ✅   |
| View record detail             |   ✅*  |   ✅    |  ✅   |
| Create financial record        |   ❌   |   ❌    |  ✅   |
| Update financial record        |   ❌   |   ❌    |  ✅   |
| Delete financial record        |   ❌   |   ❌    |  ✅   |
| Dashboard: Summary             |   ❌   |   ✅    |  ✅   |
| Dashboard: Category summary    |   ❌   |   ✅    |  ✅   |
| Dashboard: Monthly trends      |   ❌   |   ✅    |  ✅   |
| Dashboard: Recent records      |   ❌   |   ✅    |  ✅   |
| List / manage users            |   ❌   |   ❌    |  ✅   |

`*` Viewers see **only their own** records.

---

## Design Decisions

### 1. Custom User Model with TextChoices Roles
Rather than a separate `Role` table, roles are stored as a `CharField` with
`TextChoices` on the `User` model. This is simpler, performs better (no JOIN),
and is easy to extend. If roles need dynamic assignment with multiple roles per
user, the next step would be a `ManyToManyField` to a `Role` model.

### 2. Email as Login Identifier
`USERNAME_FIELD = 'email'` removes the need for a separate username. Emails are
unique, user-friendly, and match real-world finance system UX patterns.

### 3. Soft Deletes
Records are never physically removed — `is_deleted=True` hides them from all
queries. This preserves audit history and allows future restore functionality.

### 4. DecimalField for Money
`FloatField` causes floating-point rounding errors (e.g., `0.1 + 0.2 ≠ 0.3`).
`DecimalField(max_digits=12, decimal_places=2)` is exact — critical for
financial data.

### 5. Single DB Query for Dashboard Aggregations
The `SummaryView` uses Django's conditional aggregation (`Sum(..., filter=Q(...))`)
to compute income, expenses, and counts in a **single SQL query**, rather than
three separate queries. This is much more efficient at scale.

### 6. Consistent Error Envelope
Every error response follows:
```json
{ "success": false, "error": { "code": "...", "message": "...", "details": {} } }
```
This makes frontend error handling predictable — the client always knows exactly
where to find the error code and human-readable message.

### 7. Audit Logging Middleware
Every request is logged with method, path, user, status code, and duration. In
production, point the `audit` logger to a file or log aggregation service
(e.g., CloudWatch, Datadog) for security and compliance auditing.

### 8. Pagination by Default
`StandardResultsPagination` is applied globally in `DEFAULT_PAGINATION_CLASS`.
No endpoint can accidentally return unbounded result sets. The custom paginator
returns a `pagination` envelope with `total_pages`, `current_page`, and links.

### 9. Modular App Structure
Each domain (`users`, `records`, `dashboard`) is a self-contained Django app.
Shared infrastructure (`core/`) has no dependency on any app — apps depend on
core, never the other way around.
