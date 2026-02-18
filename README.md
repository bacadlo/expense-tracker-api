# Expense Tracker API

A RESTful API for personal finance management that tracks transactions, manages budgets, and analyzes spending habits. Built with FastAPI and PostgreSQL.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (async via asyncpg)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Validation:** Pydantic

## Getting Started

### Prerequisites

- Python 3.14+
- PostgreSQL

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd expense-tracker-api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .

# Configure environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### Database Setup

```bash
# Create the database
createdb budget_tracker

# Run migrations
alembic upgrade head
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs are at `/docs` (Swagger UI) and `/redoc`.

## API Endpoints

### Categories

| Method | Endpoint                  | Description         |
| ------ | ------------------------- | ------------------- |
| POST   | `/api/categories`         | Create a category   |
| GET    | `/api/categories`         | List all categories |
| GET    | `/api/categories/{id}`    | Get category by ID  |
| PUT    | `/api/categories/{id}`    | Update a category   |
| DELETE | `/api/categories/{id}`    | Delete a category   |

### Transactions

| Method | Endpoint                    | Description          |
| ------ | --------------------------- | -------------------- |
| POST   | `/api/transactions`         | Create a transaction |
| GET    | `/api/transactions`         | List transactions    |
| GET    | `/api/transactions/{id}`    | Get transaction      |
| PUT    | `/api/transactions/{id}`    | Update a transaction |
| DELETE | `/api/transactions/{id}`    | Delete a transaction |

**Query filters for listing transactions:**
- `category_id` — filter by category
- `type` — `INCOME` or `EXPENSE`
- `start_date` / `end_date` — date range
- `page` / `per_page` — pagination (default 20, max 100)

### Budgets

| Method | Endpoint                | Description       |
| ------ | ----------------------- | ----------------- |
| POST   | `/api/budgets`          | Create a budget   |
| GET    | `/api/budgets`          | List all budgets  |
| GET    | `/api/budgets/{id}`     | Get budget detail |
| PUT    | `/api/budgets/{id}`     | Update a budget   |
| DELETE | `/api/budgets/{id}`     | Delete a budget   |

Budget details include `spent`, `remaining`, and `percentage_used` fields.

### Analytics

| Method | Endpoint                          | Description                            |
| ------ | --------------------------------- | -------------------------------------- |
| GET    | `/api/analytics/balance`          | Total income, expenses, and net balance |
| GET    | `/api/analytics/spending-by-category` | Spending breakdown by category     |
| GET    | `/api/analytics/monthly-summary`  | Month-by-month income and expenses     |
| GET    | `/api/analytics/budget-status`    | Status of all active budgets           |
| GET    | `/api/analytics/trends`           | Period-over-period spending comparison |

## Project Structure

```
app/
├── main.py              # Application entry point
├── config.py            # Settings and configuration
├── database.py          # Async database setup
├── exceptions.py        # Custom exception handlers
├── models/              # SQLAlchemy models
│   ├── base.py          # Base model with timestamps
│   ├── transaction.py
│   ├── category.py
│   └── budget.py
├── schemas/             # Pydantic request/response schemas
│   ├── transaction.py
│   ├── category.py
│   ├── budget.py
│   └── analytics.py
├── routers/             # Route handlers
│   ├── transactions.py
│   ├── categories.py
│   ├── budgets.py
│   └── analytics.py
└── services/            # Business logic
    ├── transaction_service.py
    ├── budget_service.py
    └── analytics_service.py
```

## Configuration

Environment variables (set in `.env`):

| Variable       | Default                                                        | Description          |
| -------------- | -------------------------------------------------------------- | -------------------- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/budget_tracker` | PostgreSQL connection string |
| `APP_ENV`      | `development`                                                  | Application environment |
| `DEBUG`        | `true`                                                         | Debug mode           |
