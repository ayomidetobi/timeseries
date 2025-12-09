# Test Suite

Comprehensive test suite for the Financial Data API using pytest, factory_boy, and faker.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── factories/               # Factory_boy factories for test data
│   ├── lookup_tables.py
│   ├── meta_series.py
│   ├── value_data.py
│   └── dependencies.py
├── test_crud/               # CRUD operation tests
│   ├── test_meta_series.py
│   └── test_value_data.py
└── test_api/                # API endpoint tests
    ├── test_meta_series_endpoints.py
    └── test_value_data_endpoints.py
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test categories:
```bash
pytest -m crud          # CRUD tests only
pytest -m api           # API tests only
pytest -m integration   # Integration tests
```

### Run specific test file:
```bash
pytest tests/test_crud/test_meta_series.py
```

## Test Features

- **In-memory SQLite database** for fast, isolated tests
- **Factory_boy factories** for generating test data
- **Faker** for realistic fake data
- **Proper setup/teardown** - database is created and cleaned up for each test
- **Async support** - Full async/await support for database operations
- **FastAPI test client** - Both sync and async test clients

## Test Fixtures

- `test_engine` - Creates test database engine
- `test_session` - Creates test database session
- `client` - FastAPI TestClient (sync)
- `async_client` - FastAPI AsyncClient (async)

## Factory Usage

Factories use `.build()` to create instances without saving, then you manually add to session:

```python
# Create instance
asset_class = AssetClassFactory.build()
test_session.add(asset_class)
await test_session.commit()
await test_session.refresh(asset_class)
```

