"""Factories for dependency models."""
import factory
from faker import Faker
from decimal import Decimal
from datetime import datetime

from app.models.dependency import seriesDependencyGraph, calculationLog

fake = Faker()


class dependencyFactory(factory.Factory):
    """Factory for SeriesDependencyGraph."""
    
    class Meta:
        model = seriesDependencyGraph
    
    parent_series_id = None  # Must be set in tests
    child_series_id = None  # Must be set in tests
    dependency_type = factory.LazyAttribute(lambda x: fake.random_element(elements=("DERIVED", "AGGREGATED", "TRANSFORMED")))
    weight = factory.LazyAttribute(lambda x: Decimal(str(fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1))) if fake.boolean() else None)
    formula = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200) if fake.boolean() else None)
    is_active = factory.LazyAttribute(lambda x: fake.boolean(chance_of_getting_true=90))
    valid_from = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-1y", end_date="now") if fake.boolean() else None)
    valid_to = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="now", end_date="+1y") if fake.boolean() else None)
    created_at = factory.LazyFunction(datetime.utcnow)


class calculationLogFactory(factory.Factory):
    """Factory for CalculationLog."""
    
    class Meta:
        model = calculationLog
    
    derived_series_id = None  # Must be set in tests
    calculation_method = factory.LazyAttribute(lambda x: fake.random_element(elements=("SUM", "AVG", "MULTIPLY", "DIVIDE", "CUSTOM")))
    input_series_ids = factory.LazyAttribute(lambda x: [fake.random_int(min=1, max=100) for _ in range(fake.random_int(min=1, max=5))])
    calculation_parameters = factory.LazyAttribute(lambda x: {
        "param1": fake.word(),
        "param2": fake.random_int(min=1, max=100),
        "param3": fake.pyfloat()
    } if fake.boolean() else None)
    calculation_status = factory.LazyAttribute(lambda x: fake.random_element(elements=("Success", "Failed", "Active", "Stale", "Pending recomputation")))
    error_message = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200) if fake.boolean() else None)
    execution_time_ms = factory.LazyAttribute(lambda x: fake.random_int(min=10, max=5000) if fake.boolean() else None)
    calculated_at = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-1y", end_date="now") if fake.boolean() else None)
    last_calculated = factory.LazyAttribute(lambda x: fake.date_time_between(start_date="-1y", end_date="now") if fake.boolean() else None)
    calculated_by = factory.LazyAttribute(lambda x: fake.word() if fake.boolean() else None)
    calculation_policy = factory.LazyAttribute(lambda x: fake.random_element(elements=("Manual", "Scheduled", "Trigger-based")) if fake.boolean() else None)

