"""Factories for lookup table models."""
import factory
from faker import Faker
from datetime import datetime

from app.models.lookup_tables import (
    AssetClassLookup,
    ProductTypeLookup,
    SubAssetClassLookup,
    DataTypeLookup,
    StructureTypeLookup,
    MarketSegmentLookup,
    FieldTypeLookup,
)
from app.constants.lookup_enums import (
    AssetClassEnum,
    SubAssetClassEnum,
    ProductTypeEnum,
    DataTypeEnum,
    StructureTypeEnum,
    MarketSegmentEnum,
    FieldTypeEnum,
)

fake = Faker()


class AssetClassFactory(factory.Factory):
    """Factory for AssetClassLookup."""
    
    class Meta:
        model = AssetClassLookup
    
    asset_class_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in AssetClassEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class ProductTypeFactory(factory.Factory):
    """Factory for ProductTypeLookup."""
    
    class Meta:
        model = ProductTypeLookup
    
    product_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in ProductTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    is_derived = factory.LazyAttribute(
        lambda x: x.product_type_name == ProductTypeEnum.INDEX.value
        if hasattr(x, 'product_type_name') and x.product_type_name in [e.value for e in ProductTypeEnum]
        else fake.boolean()
    )
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class SubAssetClassFactory(factory.Factory):
    """Factory for SubAssetClassLookup."""
    
    class Meta:
        model = SubAssetClassLookup
    
    sub_asset_class_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in SubAssetClassEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    asset_class_id = None  # Will be set in tests
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class DataTypeFactory(factory.Factory):
    """Factory for DataTypeLookup."""
    
    class Meta:
        model = DataTypeLookup
    
    data_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in DataTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class StructureTypeFactory(factory.Factory):
    """Factory for StructureTypeLookup."""
    
    class Meta:
        model = StructureTypeLookup
    
    structure_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in StructureTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class MarketSegmentFactory(factory.Factory):
    """Factory for MarketSegmentLookup."""
    
    class Meta:
        model = MarketSegmentLookup
    
    market_segment_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in MarketSegmentEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().title() + " " + fake.word().title()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class FieldTypeFactory(factory.Factory):
    """Factory for FieldTypeLookup."""
    
    class Meta:
        model = FieldTypeLookup
    
    field_type_name = factory.LazyAttribute(
        lambda x: fake.random_element(elements=[e.value for e in FieldTypeEnum])
        if fake.boolean(chance_of_getting_true=70)
        else fake.word().upper()
    )
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
