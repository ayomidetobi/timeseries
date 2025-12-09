"""Factories for MetaSeries model."""
import factory
from faker import Faker
from decimal import Decimal
from datetime import datetime

from app.models.meta_series import MetaSeries, DataSource

fake = Faker()


class MetaSeriesFactory(factory.Factory):
    """Factory for MetaSeries."""
    
    class Meta:
        model = MetaSeries
    
    series_name = factory.LazyAttribute(lambda x: fake.company() + " " + fake.word().title())
    asset_class_id = None  # Will be set in tests
    sub_asset_class_id = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=100) if fake.boolean() else None)
    product_type_id = None  # Will be set in tests
    data_type_id = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=50) if fake.boolean() else None)
    structure_type_id = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=50) if fake.boolean() else None)
    market_segment_id = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=50) if fake.boolean() else None)
    ticker = factory.LazyAttribute(lambda x: fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    flds_id = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=10) if fake.boolean() else None)
    valid_from = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-2y", end_date="now") if fake.boolean() else None)
    valid_to = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="now", end_date="+2y") if fake.boolean() else None)
    version_number = factory.LazyAttribute(lambda x: fake.random_int(min=1, max=10))
    is_active = factory.LazyAttribute(lambda x: fake.boolean(chance_of_getting_true=80))
    
    # Series metadata fields (moved from ValueData)
    is_derived = factory.LazyAttribute(lambda x: fake.boolean(chance_of_getting_true=30))
    calculation_method = factory.LazyAttribute(lambda x: fake.random_element(elements=("Weighted Average", "Sum", "Product", "Ratio")) if fake.boolean() else None)
    data_quality_score = factory.LazyAttribute(lambda x: Decimal(str(fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1))) if fake.boolean() else None)
    source = factory.LazyAttribute(lambda x: fake.random_element(elements=[DataSource.RAW, DataSource.DERIVED]) if fake.boolean() else None)

    confidence_level = factory.LazyAttribute(lambda x: fake.random_element(elements=("HIGH", "MEDIUM", "LOW")) if fake.boolean() else None)
    effective_date = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-1y", end_date="now") if fake.boolean() else None)
    as_of_date = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-1y", end_date="now") if fake.boolean() else None)
    
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

