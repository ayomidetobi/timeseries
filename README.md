# Financial Data API

A FastAPI application for managing financial time-series data using TimescaleDB, SQLModel, and async database operations.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **TimescaleDB** - PostgreSQL extension optimized for time-series data
- **SQLModel** - SQL database in Python, designed for simplicity, compatibility, and robustness
- **Async Database** - Full async/await support using asyncpg
- **Alembic** - Database migration tool
- **RESTful API** - Complete CRUD operations for all entities

## Project Structure

```
bnp/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── meta_series.py
│   │       │   ├── value_data.py
│   │       │   ├── lookup_tables.py
│   │       │   └── dependencies.py
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── meta_series.py
│   │   ├── lookup_tables.py
│   │   ├── value_data.py
│   │   └── dependency.py
│   └── schemas/
├── alembic/
│   └── versions/
├── scripts/
├── main.py
├── requirements.txt
└── .env.example
```

## Database Schema

The application includes the following main entities:

- **META_SERIES** - Metadata for financial data series
- **ASSET_CLASS_LOOKUP** - Asset class reference data
- **PRODUCT_TYPE_LOOKUP** - Product type reference data
- **VALUE_DATA** - Unified time-series observation values (both raw and derived, with `is_derived` flag)
- **SERIES_DEPENDENCY_GRAPH** - Tracks dependencies between series
- **CALCULATION_LOG** - Logs for derived value calculations

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ with TimescaleDB extension
- pip

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd /Users/adekoyaayomide/Documents/bnp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Run migrations:
```bash
alembic upgrade head
```

Note: TimescaleDB hypertables are automatically created by TimescaleModel during migrations.

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Meta Series
- `GET /api/v1/meta-series/` - List all meta series
- `GET /api/v1/meta-series/{series_id}` - Get specific meta series
- `POST /api/v1/meta-series/` - Create new meta series
- `PUT /api/v1/meta-series/{series_id}` - Update meta series
- `DELETE /api/v1/meta-series/{series_id}` - Soft delete meta series

### Value Data
- `GET /api/v1/value-data/` - Get value data for a series
- `GET /api/v1/value-data/{series_id}/{observation_date}` - Get specific value
- `POST /api/v1/value-data/` - Create new value data
- `PUT /api/v1/value-data/{series_id}/{observation_date}` - Update value data
- `GET /api/v1/value-data/derived/` - Get derived value data

### Lookup Tables
- `GET /api/v1/lookup/asset-classes/` - List asset classes
- `POST /api/v1/lookup/asset-classes/` - Create asset class
- `GET /api/v1/lookup/product-types/` - List product types
- `POST /api/v1/lookup/product-types/` - Create product type

### Dependencies
- `GET /api/v1/dependencies/dependencies/` - List series dependencies
- `POST /api/v1/dependencies/dependencies/` - Create dependency
- `GET /api/v1/dependencies/calculations/` - List calculation logs
- `POST /api/v1/dependencies/calculations/` - Create calculation log

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

### Code Style
The project uses standard Python conventions. Consider using:
- `black` for code formatting
- `flake8` or `pylint` for linting
- `mypy` for type checking

## License

MIT

