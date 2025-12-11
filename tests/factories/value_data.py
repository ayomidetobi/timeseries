"""Factories for ValueData model."""

import factory
from faker import Faker
from decimal import Decimal
from datetime import datetime, date, timedelta

from app.models.value_data import valueData

fake = Faker()


class valueDataFactory(factory.Factory):
    """Factory for ValueData."""

    class Meta:
        model = valueData

    series_id = None  # Must be set in tests
    timestamp = factory.LazyFunction(
        lambda: date.today() - timedelta(days=fake.random_int(min=0, max=365))
    )
    value = factory.LazyAttribute(
        lambda x: Decimal(
            str(fake.pyfloat(left_digits=7, right_digits=8, positive=True))
        )
    )

    # Fields for derived values (only populated when series is_derived=True)
    # Set to None during seeding - will be populated when calculation logs are created
    dependency_calculation_id = None
    derived_flag = factory.LazyAttribute(
        lambda x: fake.word().upper()
        if fake.boolean(chance_of_getting_true=30)
        else None
    )

    # Value-specific versioning and audit fields
    version_number = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=5))
    is_latest = factory.LazyAttribute(lambda x: fake.boolean(chance_of_getting_true=90))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
