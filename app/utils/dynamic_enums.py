"""Dynamic enum generation from lookup tables with fallback to constants."""

from typing import Type, Optional, Dict, cast, TypedDict
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.models.lookup_tables import (
    assetClassLookup,
    subAssetClassLookup,
    productTypeLookup,
    structureTypeLookup,
    marketSegmentLookup,
    dataTypeLookup,
    fieldTypeLookup,
    tickerSourceLookup,
)
from app.constants.lookup_enums import (
    assetClassEnum as staticAssetClassEnum,
    subAssetClassEnum as staticSubAssetClassEnum,
    productTypeEnum as staticProductTypeEnum,
    structureTypeEnum as staticStructureTypeEnum,
    marketSegmentEnum as staticMarketSegmentEnum,
    dataTypeEnum as staticDataTypeEnum,
    fieldTypeEnum as staticFieldTypeEnum,
    tickerSourceEnum as staticTickerSourceEnum,
    tickerSourceCodeEnum as staticTickerSourceCodeEnum,
)
from app.core.database import get_session_context
from app.core.logger import logger


# Cache for dynamically created enums
_enum_cache: Dict[str, Type[Enum]] = {}


class LookupTableConfig(TypedDict):
    """Configuration for a lookup table."""

    model: Type[SQLModel]
    name_field: str
    fallback_enum: Type[Enum]


# Mapping of lookup table models to their name fields and fallback enums
LOOKUP_TABLE_CONFIG: Dict[str, LookupTableConfig] = {
    "asset_class": {
        "model": assetClassLookup,
        "name_field": "asset_class_name",
        "fallback_enum": staticAssetClassEnum,
    },
    "sub_asset_class": {
        "model": subAssetClassLookup,
        "name_field": "sub_asset_class_name",
        "fallback_enum": staticSubAssetClassEnum,
    },
    "product_type": {
        "model": productTypeLookup,
        "name_field": "product_type_name",
        "fallback_enum": staticProductTypeEnum,
    },
    "structure_type": {
        "model": structureTypeLookup,
        "name_field": "structure_type_name",
        "fallback_enum": staticStructureTypeEnum,
    },
    "market_segment": {
        "model": marketSegmentLookup,
        "name_field": "market_segment_name",
        "fallback_enum": staticMarketSegmentEnum,
    },
    "data_type": {
        "model": dataTypeLookup,
        "name_field": "data_type_name",
        "fallback_enum": staticDataTypeEnum,
    },
    "field_type": {
        "model": fieldTypeLookup,
        "name_field": "field_type_name",
        "fallback_enum": staticFieldTypeEnum,
    },
    "ticker_source": {
        "model": tickerSourceLookup,
        "name_field": "ticker_source_name",
        "fallback_enum": staticTickerSourceEnum,
    },
    "ticker_source_code": {
        "model": tickerSourceLookup,
        "name_field": "ticker_source_code",
        "fallback_enum": staticTickerSourceCodeEnum,
    },
}


async def _fetchLookupValues(
    session: AsyncSession,
    model: Type[SQLModel],
    name_field: str,
) -> list[str]:
    """Fetch all values from a lookup table.

    Args:
        session: Database session
        model: SQLModel class for the lookup table
        name_field: Name of the field containing the enum value

    Returns:
        List of string values from the lookup table
    """
    try:
        query = select(getattr(model, name_field))
        result = await session.execute(query)
        values = [row[0] for row in result.fetchall() if row[0] is not None]
        return sorted(set(values))  # Remove duplicates and sort
    except Exception as e:
        logger.warning(f"Error fetching lookup values from {model.__name__}: {e}")
        return []


def _normalizeEnumKey(value: str) -> str:
    """Normalize a string value to a valid Python enum key.

    Args:
        value: The string value to normalize

    Returns:
        A valid Python identifier for use as an enum key
    """
    # Convert value to valid Python identifier
    # Replace spaces and special chars with underscores, remove invalid chars
    key = value.upper().replace(" ", "_").replace("-", "_").replace(".", "_")
    # Remove any remaining invalid characters
    key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)
    # Ensure it doesn't start with a number
    if key and key[0].isdigit():
        key = f"VALUE_{key}"
    # Ensure it's not empty
    if not key:
        key = "UNKNOWN"
    return key


def _createDynamicEnum(
    enum_name: str,
    values: list[str],
    fallback_enum: Type[Enum],
) -> Type[Enum]:
    """Create a dynamic enum from values, falling back to fallback_enum if values are empty.

    Args:
        enum_name: Name for the new enum class
        values: List of string values to create enum members from
        fallback_enum: Enum to use if values list is empty

    Returns:
        A new Enum class with the provided values or fallback enum values
    """
    if not values:
        logger.info(f"Lookup table for {enum_name} is empty, using fallback enum")
        return fallback_enum

    # Create enum members from values as a list of tuples
    enum_members_list: list[tuple[str, str]] = []
    for value in values:
        key = _normalizeEnumKey(value)
        enum_members_list.append((key, value))

    # Create the enum class using functional API with list of tuples
    # Type ignore needed because Enum() functional API has type checking limitations
    # with dynamic names, but this is safe at runtime
    dynamic_enum = Enum(enum_name, enum_members_list, type=str)  # type: ignore[misc]
    return cast(Type[Enum], dynamic_enum)


async def _getOrCreateEnum(
    lookup_key: str,
    session: Optional[AsyncSession] = None,
) -> Type[Enum]:
    """Get or create a dynamic enum for a lookup table.

    Args:
        lookup_key: Key from LOOKUP_TABLE_CONFIG
        session: Optional database session. If None, creates a new one.

    Returns:
        Enum class (either from cache, database, or fallback)
    """
    # Check cache first
    if lookup_key in _enum_cache:
        return _enum_cache[lookup_key]

    config = LOOKUP_TABLE_CONFIG[lookup_key]
    model = config["model"]
    name_field = config["name_field"]
    fallback_enum = config["fallback_enum"]

    # Try to fetch from database
    values = []
    if session:
        values = await _fetchLookupValues(session, model, name_field)
    else:
        try:
            async with get_session_context() as db_session:
                values = await _fetchLookupValues(db_session, model, name_field)
        except Exception as e:
            logger.warning(f"Could not fetch {lookup_key} from database: {e}")

    # Create enum (will use fallback if values is empty)
    enum_name = f"Dynamic{fallback_enum.__name__}"
    dynamic_enum = _createDynamicEnum(enum_name, values, fallback_enum)

    # Cache it
    _enum_cache[lookup_key] = dynamic_enum

    return dynamic_enum


async def getDynamicEnum(
    lookup_key: str,
    session: Optional[AsyncSession] = None,
) -> Type[Enum]:
    """Get a dynamic enum for a lookup table.

    Args:
        lookup_key: One of: "asset_class", "sub_asset_class", "product_type",
                   "structure_type", "market_segment", "data_type", "field_type",
                   "ticker_source", "ticker_source_code"
        session: Optional database session. If None, creates a new one.

    Returns:
        Enum class that can be used for Pydantic validation

    Example:
        ```python
        assetClassEnum = await getDynamicEnum("asset_class")
        # Use in Pydantic model:
        class MyModel(BaseModel):
            asset_class: AssetClassEnum
        ```
    """
    if lookup_key not in LOOKUP_TABLE_CONFIG:
        raise ValueError(
            f"Invalid lookup_key: {lookup_key}. "
            f"Must be one of: {list(LOOKUP_TABLE_CONFIG.keys())}"
        )

    return await _getOrCreateEnum(lookup_key, session)


async def refreshEnumCache(lookup_key: Optional[str] = None) -> None:
    """Refresh the enum cache for one or all lookup tables.

    Args:
        lookup_key: Specific lookup key to refresh, or None to refresh all
    """
    if lookup_key:
        if lookup_key in _enum_cache:
            del _enum_cache[lookup_key]
        # Re-fetch and cache
        await _getOrCreateEnum(lookup_key)
    else:
        # Clear all cache
        _enum_cache.clear()
        # Re-fetch all
        async with get_session_context() as session:
            for key in LOOKUP_TABLE_CONFIG.keys():
                await _getOrCreateEnum(key, session)


# Global enum instances (initialized at startup)
# These will be replaced with dynamic enums from the database at startup
_initialized = False
assetClassEnum: Type[Enum] = staticAssetClassEnum
subAssetClassEnum: Type[Enum] = staticSubAssetClassEnum
productTypeEnum: Type[Enum] = staticProductTypeEnum
structureTypeEnum: Type[Enum] = staticStructureTypeEnum
marketSegmentEnum: Type[Enum] = staticMarketSegmentEnum
dataTypeEnum: Type[Enum] = staticDataTypeEnum
fieldTypeEnum: Type[Enum] = staticFieldTypeEnum
tickerSourceEnum: Type[Enum] = staticTickerSourceEnum
tickerSourceCodeEnum: Type[Enum] = staticTickerSourceCodeEnum


async def initializeDynamicEnums(session: Optional[AsyncSession] = None) -> None:
    """Initialize all dynamic enums at application startup.

    This should be called during app startup to populate the enum cache
    and set the global enum variables.

    Args:
        session: Optional database session. If None, creates a new one.
    """
    global _initialized
    global assetClassEnum, subAssetClassEnum, productTypeEnum
    global \
        structureTypeEnum, \
        marketSegmentEnum, \
        dataTypeEnum, \
        fieldTypeEnum, \
        tickerSourceEnum, \
        tickerSourceCodeEnum

    if _initialized:
        return

    try:
        if session:
            # Initialize all enums with provided session
            assetClassEnum = await _getOrCreateEnum("asset_class", session)
            subAssetClassEnum = await _getOrCreateEnum("sub_asset_class", session)
            productTypeEnum = await _getOrCreateEnum("product_type", session)
            structureTypeEnum = await _getOrCreateEnum("structure_type", session)
            marketSegmentEnum = await _getOrCreateEnum("market_segment", session)
            dataTypeEnum = await _getOrCreateEnum("data_type", session)
            fieldTypeEnum = await _getOrCreateEnum("field_type", session)
            tickerSourceEnum = await _getOrCreateEnum("ticker_source", session)
            tickerSourceCodeEnum = await _getOrCreateEnum("ticker_source_code", session)
        else:
            # Initialize all enums with new session
            async with get_session_context() as db_session:
                assetClassEnum = await _getOrCreateEnum("asset_class", db_session)
                subAssetClassEnum = await _getOrCreateEnum(
                    "sub_asset_class", db_session
                )
                productTypeEnum = await _getOrCreateEnum("product_type", db_session)
                structureTypeEnum = await _getOrCreateEnum("structure_type", db_session)
                marketSegmentEnum = await _getOrCreateEnum("market_segment", db_session)
                dataTypeEnum = await _getOrCreateEnum("data_type", db_session)
                fieldTypeEnum = await _getOrCreateEnum("field_type", db_session)
                tickerSourceEnum = await _getOrCreateEnum("ticker_source", db_session)
                tickerSourceCodeEnum = await _getOrCreateEnum(
                    "ticker_source_code", db_session
                )

        _initialized = True
        logger.info("Dynamic enums initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize dynamic enums, using fallback enums: {e}")
        # Enums already default to fallback values, so we're good
        _initialized = True


# Convenience functions to get enums synchronously (for use in Pydantic models)
# These will use cached values or fallback enums
def getAssetClassEnum() -> Type[Enum]:
    """Get asset class enum (synchronous, uses cache or fallback)."""
    return assetClassEnum


def getSubAssetClassEnum() -> Type[Enum]:
    """Get sub-asset class enum (synchronous, uses cache or fallback)."""
    return subAssetClassEnum


def getProductTypeEnum() -> Type[Enum]:
    """Get product type enum (synchronous, uses cache or fallback)."""
    return productTypeEnum


def getStructureTypeEnum() -> Type[Enum]:
    """Get structure type enum (synchronous, uses cache or fallback)."""
    return structureTypeEnum


def getMarketSegmentEnum() -> Type[Enum]:
    """Get market segment enum (synchronous, uses cache or fallback)."""
    return marketSegmentEnum


def getDataTypeEnum() -> Type[Enum]:
    """Get data type enum (synchronous, uses cache or fallback)."""
    return dataTypeEnum


def getFieldTypeEnum() -> Type[Enum]:
    """Get field type enum (synchronous, uses cache or fallback)."""
    return fieldTypeEnum


def getTickerSourceEnum() -> Type[Enum]:
    """Get ticker source enum (synchronous, uses cache or fallback)."""
    return tickerSourceEnum


def getTickerSourceCodeEnum() -> Type[Enum]:
    """Get ticker source code enum (synchronous, uses cache or fallback)."""
    return tickerSourceCodeEnum
