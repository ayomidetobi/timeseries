# Setup Guide

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Create a `.env` file in the project root with:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/financial_db
SYNC_DATABASE_URL=postgresql://user:password@localhost:5432/financial_db
APP_NAME=Financial Data API
DEBUG=True
```

3. **Run migrations:**
```bash
alembic upgrade head
```

Note: TimescaleDB hypertables are automatically created by TimescaleModel during migrations.

6. **Start the server:**
```bash
uvicorn main:app --reload
```

## Database Schema

The application uses the following main tables:
- `meta_series` - Series metadata
- `asset_class_lookup` - Asset class reference
- `product_type_lookup` - Product type reference
- `value_data` - Time-series values (TimescaleDB hypertable, unified for both raw and derived values)
- `series_dependency_graph` - Series dependencies
- `calculation_log` - Calculation logs

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

