"""Factories for lookup table models."""

import factory
from faker import Faker
from datetime import datetime

from app.models.lookup_tables import (
    assetClassLookup,
    productTypeLookup,
    subAssetClassLookup,
    dataTypeLookup,
    structureTypeLookup,
    marketSegmentLookup,
    fieldTypeLookup,
    tickerSourceLookup,
)
from app.constants.lookup_enums import (
    assetClassEnum,
    subAssetClassEnum,
    productTypeEnum,
    dataTypeEnum,
    structureTypeEnum,
    marketSegmentEnum,
    fieldTypeEnum,
    tickerSourceEnum,
)

fake = Faker()


class assetClassFactory(factory.Factory):
    """Factory for AssetClassLookup."""

    class Meta:
        model = assetClassLookup

    asset_class_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in assetClassEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class productTypeFactory(factory.Factory):
    """Factory for ProductTypeLookup."""

    class Meta:
        model = productTypeLookup

    product_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in productTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    is_derived = factory.LazyAttribute(
        lambda x: x.product_type_name == productTypeEnum.INDEX.value
        if hasattr(x, "product_type_name")
        and x.product_type_name in [e.value for e in productTypeEnum]
        else fake.boolean()
    )
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class subAssetClassFactory(factory.Factory):
    """Factory for SubAssetClassLookup."""

    class Meta:
        model = subAssetClassLookup

    sub_asset_class_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in subAssetClassEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    asset_class_id = None  # Will be set in tests
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class dataTypeFactory(factory.Factory):
    """Factory for DataTypeLookup."""

    class Meta:
        model = dataTypeLookup

    data_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in dataTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class structureTypeFactory(factory.Factory):
    """Factory for StructureTypeLookup."""

    class Meta:
        model = structureTypeLookup

    structure_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in structureTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class marketSegmentFactory(factory.Factory):
    """Factory for MarketSegmentLookup."""

    class Meta:
        model = marketSegmentLookup

    market_segment_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in marketSegmentEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class fieldTypeFactory(factory.Factory):
    """Factory for FieldTypeLookup."""

    class Meta:
        model = fieldTypeLookup

    field_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in fieldTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().upper()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class tickerSourceFactory(factory.Factory):
    """Factory for TickerSourceLookup."""

    class Meta:
        model = tickerSourceLookup

    ticker_source_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in tickerSourceEnum])
        if fake.boolean(chance_of_getting_true=80)
        else fake.company() + " Source"
    )
    ticker_source_code = factory.LazyAttribute(
        lambda x: fake.random_element(elements=["BBG", "HWK", "RMP", "LSE"])
        if fake.boolean(chance_of_getting_true=60)
        else None
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
