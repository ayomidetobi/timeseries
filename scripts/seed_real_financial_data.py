#!/usr/bin/env python3
"""Database seeding script with real financial instrument data using Factory Boy."""

import asyncio
import sys
import random
from pathlib import Path
from typing import List, Dict, Optional
from datetime import date, timedelta, datetime
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import logger - will use global configuration from app.core.logger
from app.core.logger import logger

from app.core.database import init as init_db, get_session_context
from app.core.clickhouse_conn import (
    init as init_clickhouse,
    close as close_clickhouse,
    _clickhouse_connection_manager,
)
from app.models.meta_series import metaSeries, dataSource
from app.crud.value_data import get_crud_value_data
from tests.factories import (
    assetClassFactory,
    productTypeFactory,
    subAssetClassFactory,
    dataTypeFactory,
    structureTypeFactory,
    marketSegmentFactory,
    fieldTypeFactory,
    tickerSourceFactory,
    metaSeriesFactory,
)
from faker import Faker
from app.constants.lookup_enums import (
    assetClassEnum,
    subAssetClassEnum,
    productTypeEnum,
    structureTypeEnum,
    marketSegmentEnum,
    dataTypeEnum,
    fieldTypeEnum,
    tickerSourceEnum,
    TICKER_SUFFIX_MAP,
    COMMODITY_NAMES,
    COMMODITY_SUB_ASSET_MAP,
    ASSET_CLASS_SUB_ASSET_MAP,
    FX_MARKET_SUB_ASSET_MAP,
)

fake = Faker()
random.seed()  # Initialize random seed


# ============================================================================
# Utility Functions
# ============================================================================


def generate_fx_pair() -> str:
    """Generate a currency pair using fake currency codes."""
    currency1 = fake.currency_code()
    currency2 = fake.currency_code()
    # Ensure they're different
    while currency1 == currency2:
        currency2 = fake.currency_code()
    return f"{currency1}{currency2}"


def generate_ticker(
    asset_class: assetClassEnum, product: productTypeEnum, series_name: str
) -> str:
    """Generate ticker based on asset class, product type, and series name."""
    suffix = TICKER_SUFFIX_MAP.get((asset_class, product), "Index")
    # Use series name as ticker code, clean it up for ticker format
    ticker_code = series_name.replace(",", "").replace(" ", "").upper()
    return f"{ticker_code} {suffix}"


# ============================================================================
# Lookup Table Creation Helpers
# ============================================================================


async def _fetch_existing_lookup_ids(
    session, table_name: str, id_column: str, name_column: str
) -> Dict[str, int]:
    """Fetch existing lookup table IDs from database."""
    from sqlalchemy import text

    result = await session.execute(
        text(f"SELECT {id_column}, {name_column} FROM {table_name}")
    )
    return {row[0]: row[1] for row in result}


async def _create_lookup_table_entry(
    session, factory_class, name: str, existing_ids: Dict[str, int], **factory_kwargs
) -> Optional[int]:
    """Create a single lookup table entry if it doesn't exist."""
    if name in existing_ids:
        return existing_ids[name]

    entry = factory_class.build(**factory_kwargs)
    session.add(entry)
    return None  # Will be fetched after commit


async def _ensure_lookup_entries(
    session,
    table_name: str,
    id_column: str,
    name_column: str,
    factory_class,
    enum_values: List,
    existing_ids: Dict[str, int],
    build_kwargs_fn=None,
) -> Dict[str, int]:
    """Ensure all enum values exist in a lookup table."""
    # Create missing entries
    for enum_value in enum_values:
        name = enum_value.value if hasattr(enum_value, "value") else enum_value
        if name not in existing_ids:
            kwargs = (
                build_kwargs_fn(enum_value)
                if build_kwargs_fn
                else {"description": f"{name} {table_name.replace('_lookup', '')}"}
            )
            await _create_lookup_table_entry(
                session, factory_class, name, existing_ids, **kwargs
            )

    await session.commit()

    # Refresh to get all IDs including newly created ones
    from sqlalchemy import text

    result = await session.execute(
        text(f"SELECT {id_column}, {name_column} FROM {table_name}")
    )
    return {row[1]: row[0] for row in result}


async def create_asset_classes(session) -> Dict[str, int]:
    """Create asset classes lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT asset_class_id, asset_class_name FROM asset_class_lookup")
    )
    existing = {row.asset_class_name: row.asset_class_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "asset_class_lookup",
        "asset_class_id",
        "asset_class_name",
        assetClassFactory,
        list(assetClassEnum),
        existing,
        lambda e: {
            "asset_class_name": e.value,
            "description": f"{e.value} asset class",
        },
    )


async def create_product_types(session) -> Dict[str, int]:
    """Create product types lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT product_type_id, product_type_name FROM product_type_lookup")
    )
    existing = {row.product_type_name: row.product_type_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "product_type_lookup",
        "product_type_id",
        "product_type_name",
        productTypeFactory,
        list(productTypeEnum),
        existing,
        lambda e: {
            "product_type_name": e.value,
            "description": f"{e.value} product type",
            "is_derived": (e == productTypeEnum.INDEX),
        },
    )


async def create_sub_asset_classes(
    session, asset_classes: Dict[str, int]
) -> Dict[str, int]:
    """Create sub-asset classes lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text(
            "SELECT sub_asset_class_id, sub_asset_class_name FROM sub_asset_class_lookup"
        )
    )
    existing = {row.sub_asset_class_name: row.sub_asset_class_id for row in result}

    # Create missing sub-asset classes
    for asset_class_enum, sub_asset_list in ASSET_CLASS_SUB_ASSET_MAP.items():
        for sub_asset_enum in sub_asset_list:
            if sub_asset_enum.value not in existing:
                asset_class_id = asset_classes.get(asset_class_enum.value)
                sac = subAssetClassFactory.build(
                    sub_asset_class_name=sub_asset_enum.value,
                    asset_class_id=asset_class_id,
                    description=f"{sub_asset_enum.value} sub-asset class",
                )
                session.add(sac)

    await session.commit()

    # Refresh to get all IDs
    result = await session.execute(
        text(
            "SELECT sub_asset_class_id, sub_asset_class_name FROM sub_asset_class_lookup"
        )
    )
    return {row.sub_asset_class_name: row.sub_asset_class_id for row in result}


async def create_data_types(session) -> Dict[str, int]:
    """Create data types lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT data_type_id, data_type_name FROM data_type_lookup")
    )
    existing = {row.data_type_name: row.data_type_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "data_type_lookup",
        "data_type_id",
        "data_type_name",
        dataTypeFactory,
        list(dataTypeEnum),
        existing,
        lambda e: {"data_type_name": e.value, "description": f"{e.value} data type"},
    )


async def create_structure_types(session) -> Dict[str, int]:
    """Create structure types lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT structure_type_id, structure_type_name FROM structure_type_lookup")
    )
    existing = {row.structure_type_name: row.structure_type_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "structure_type_lookup",
        "structure_type_id",
        "structure_type_name",
        structureTypeFactory,
        list(structureTypeEnum),
        existing,
        lambda e: {
            "structure_type_name": e.value,
            "description": f"{e.value} structure type",
        },
    )


async def create_market_segments(session) -> Dict[str, int]:
    """Create market segments lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT market_segment_id, market_segment_name FROM market_segment_lookup")
    )
    existing = {row.market_segment_name: row.market_segment_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "market_segment_lookup",
        "market_segment_id",
        "market_segment_name",
        marketSegmentFactory,
        list(marketSegmentEnum),
        existing,
        lambda e: {
            "market_segment_name": e.value,
            "description": f"{e.value} market segment",
        },
    )


async def create_field_types(session) -> Dict[str, int]:
    """Create field types lookup table."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT field_type_id, field_type_name FROM field_type_lookup")
    )
    existing = {row.field_type_name: row.field_type_id for row in result}

    return await _ensure_lookup_entries(
        session,
        "field_type_lookup",
        "field_type_id",
        "field_type_name",
        fieldTypeFactory,
        list(fieldTypeEnum),
        existing,
        lambda e: {"field_type_name": e.value, "description": f"{e.value} field type"},
    )


async def create_ticker_sources(session) -> Dict[str, int]:
    """Create ticker source lookup table."""
    from sqlalchemy import text

    # Map enum values to codes
    enum_code_map = {
        tickerSourceEnum.BLOOMBERG: "BBG",
        tickerSourceEnum.HAWKEYE: "HWK",
        tickerSourceEnum.RAMP: "RMP",
        tickerSourceEnum.LSEG: "LSE",
    }

    result = await session.execute(
        text("SELECT ticker_source_id, ticker_source_name FROM ticker_source_lookup")
    )
    existing = {row.ticker_source_name: row.ticker_source_id for row in result}

    # Create missing entries
    for enum_value in list(tickerSourceEnum):
        name = enum_value.value
        if name not in existing:
            code = enum_code_map.get(enum_value)
            ticker_source = tickerSourceFactory.build(
                ticker_source_name=name,
                ticker_source_code=code,
                description=f"{name} ticker source",
            )
            session.add(ticker_source)

    await session.commit()

    # Refresh to get all IDs
    result = await session.execute(
        text("SELECT ticker_source_id, ticker_source_name FROM ticker_source_lookup")
    )
    return {row.ticker_source_name: row.ticker_source_id for row in result}


async def create_lookup_tables(session) -> Dict[str, Dict[str, int]]:
    """Create all lookup tables using Factory Boy with enum values."""
    logger.info("📊 Creating lookup tables...")

    asset_classes = await create_asset_classes(session)
    product_types = await create_product_types(session)
    sub_asset_classes = await create_sub_asset_classes(session, asset_classes)
    data_types = await create_data_types(session)
    structure_types = await create_structure_types(session)
    market_segments = await create_market_segments(session)
    field_types = await create_field_types(session)
    ticker_sources = await create_ticker_sources(session)

    logger.success("Created lookup tables:")
    logger.info(f"   - Asset Classes: {len(asset_classes)}")
    logger.info(f"   - Product Types: {len(product_types)}")
    logger.info(f"   - Sub Asset Classes: {len(sub_asset_classes)}")
    logger.info(f"   - Data Types: {len(data_types)}")
    logger.info(f"   - Structure Types: {len(structure_types)}")
    logger.info(f"   - Market Segments: {len(market_segments)}")
    logger.info(f"   - Field Types: {len(field_types)}")
    logger.info(f"   - Ticker Sources: {len(ticker_sources)}")

    return {
        "asset_classes": asset_classes,
        "product_types": product_types,
        "sub_asset_classes": sub_asset_classes,
        "data_types": data_types,
        "structure_types": structure_types,
        "market_segments": market_segments,
        "field_types": field_types,
        "ticker_sources": ticker_sources,
    }


# ============================================================================
# Series Combination Generation
# ============================================================================


def generate_commodity_combinations() -> List[Dict]:
    """Generate valid commodity series combinations."""
    combinations = []
    for commodity_name in COMMODITY_NAMES:
        for sub, commodities in COMMODITY_SUB_ASSET_MAP.items():
            if commodity_name in commodities:
                data_type = random.choice(
                    [dataTypeEnum.PRICE, dataTypeEnum.OPEN_INTEREST]
                )
                field_type = (
                    fieldTypeEnum.PX_LAST
                    if data_type == dataTypeEnum.PRICE
                    else fieldTypeEnum.OPEN_INT
                )
                market_segment = random.choice(list(marketSegmentEnum))

                combinations.append(
                    {
                        "asset_class": assetClassEnum.COMMODITY,
                        "sub_asset_class": sub,
                        "product_type": random.choice(
                            [productTypeEnum.SPOT, productTypeEnum.INDEX]
                        ),
                        "data_type": data_type,
                        "field_type": field_type,
                        "market_segment": market_segment,
                        "series_name": commodity_name,
                        "is_derived": False,
                    }
                )
    return combinations


def generate_credit_combinations() -> List[Dict]:
    """Generate valid credit series combinations."""
    combinations = []
    credit_regions = [
        ("US IG", marketSegmentEnum.DM),
        ("EZ IG", marketSegmentEnum.DM),
        ("UK IG", marketSegmentEnum.DM),
        ("US HY", marketSegmentEnum.DM),
        ("Japan IG", marketSegmentEnum.DM),
        ("EZ HY", marketSegmentEnum.DM),
        ("EM Credit", marketSegmentEnum.EM),
        ("Asia Credit", marketSegmentEnum.EM),
        ("Latam Credit", marketSegmentEnum.EM),
    ]

    for region_name, market in credit_regions:
        combinations.append(
            {
                "asset_class": assetClassEnum.CREDIT,
                "sub_asset_class": subAssetClassEnum.OAS,
                "product_type": productTypeEnum.INDEX,
                "data_type": dataTypeEnum.PRICE_SPREAD,
                "field_type": random.choice(
                    [fieldTypeEnum.PX_LAST, fieldTypeEnum.PX_OPEN]
                ),
                "market_segment": market,
                "series_name": f"{region_name}, OAS",
                "is_derived": True,
            }
        )
    return combinations


def generate_fx_combinations() -> List[Dict]:
    """Generate valid FX series combinations."""
    combinations = []
    for market_segment, sub_assets in FX_MARKET_SUB_ASSET_MAP.items():
        for sub_asset in sub_assets:
            for _ in range(random.randint(3, 8)):  # 3-8 pairs per combination
                pair = generate_fx_pair()
                combinations.append(
                    {
                        "asset_class": assetClassEnum.FX,
                        "sub_asset_class": sub_asset,
                        "product_type": random.choice(
                            [productTypeEnum.SPOT, productTypeEnum.INDEX]
                        ),
                        "data_type": dataTypeEnum.PRICE,
                        "field_type": random.choice(list(fieldTypeEnum)),
                        "market_segment": market_segment,
                        "series_name": pair,
                        "is_derived": random.choice([True, False])
                        if productTypeEnum.INDEX
                        else False,
                    }
                )
    return combinations


def generate_random_combinations(count: int = 50) -> List[Dict]:
    """Generate random valid series combinations."""
    combinations = []
    for _ in range(count):
        asset_class = random.choice(list(assetClassEnum))
        sub_assets = ASSET_CLASS_SUB_ASSET_MAP.get(asset_class, [])
        if sub_assets:
            sub_asset = random.choice(sub_assets)
            product_type = random.choice(list(productTypeEnum))
            data_type = random.choice(list(dataTypeEnum))
            market_segment = random.choice(list(marketSegmentEnum))
            field_type = random.choice(list(fieldTypeEnum))

            # Generate appropriate series name
            if asset_class == assetClassEnum.COMMODITY:
                series_name = random.choice(COMMODITY_NAMES)
            elif asset_class == assetClassEnum.FX:
                series_name = generate_fx_pair()
            else:
                series_name = f"{fake.company()} {fake.word().title()}"

            combinations.append(
                {
                    "asset_class": asset_class,
                    "sub_asset_class": sub_asset,
                    "product_type": product_type,
                    "data_type": data_type,
                    "field_type": field_type,
                    "market_segment": market_segment,
                    "series_name": series_name,
                    "is_derived": product_type == productTypeEnum.INDEX
                    and random.choice([True, False]),
                }
            )
    return combinations


def get_valid_combinations() -> List[Dict]:
    """Generate valid combinations of asset class, sub-asset class, product type, etc."""
    combinations = []
    combinations.extend(generate_commodity_combinations())
    combinations.extend(generate_credit_combinations())
    combinations.extend(generate_fx_combinations())
    combinations.extend(generate_random_combinations(50))
    return combinations


# ============================================================================
# Meta Series Creation
# ============================================================================


def build_series_from_combination(
    combo: Dict, lookup_maps: Dict[str, Dict[str, int]]
) -> Optional[metaSeries]:
    """Build a MetaSeries instance from a combination dictionary."""
    try:
        ticker = generate_ticker(
            combo["asset_class"], combo["product_type"], combo["series_name"]
        )
        field_type_name = (
            combo["field_type"].value
            if isinstance(combo["field_type"], fieldTypeEnum)
            else combo["field_type"]
        )

        # Randomly assign a ticker source (90% chance)
        ticker_source_id = None
        if lookup_maps.get("ticker_sources") and random.random() < 0.9:
            ticker_source_values = list(lookup_maps["ticker_sources"].values())
            ticker_source_id = (
                random.choice(ticker_source_values) if ticker_source_values else None
            )

        return metaSeriesFactory.build(
            series_name=combo["series_name"],
            asset_class_id=lookup_maps["asset_classes"].get(combo["asset_class"].value),
            sub_asset_class_id=lookup_maps["sub_asset_classes"].get(
                combo["sub_asset_class"].value
            ),
            product_type_id=lookup_maps["product_types"].get(
                combo["product_type"].value
            ),
            data_type_id=lookup_maps["data_types"].get(combo["data_type"].value),
            structure_type_id=lookup_maps["structure_types"].get(
                structureTypeEnum.OUTRIGHT.value
            ),
            market_segment_id=lookup_maps["market_segments"].get(
                combo["market_segment"].value
            ),
            ticker=ticker,
            ticker_source_id=ticker_source_id,
            flds_id=lookup_maps["field_types"].get(field_type_name),
            is_active=random.choice([True, True, True, False]),  # 75% active
            is_derived=combo["is_derived"],
            source=random.choice([dataSource.RAW, dataSource.DERIVED])
            if combo["is_derived"]
            else dataSource.RAW,
            version_number=random.randint(1, 5),
        )
    except (KeyError, AttributeError) as e:
        logger.warning(f"Skipping invalid combination: {e}")
        return None


async def create_meta_series_batch(
    session, combinations: List[Dict], lookup_maps: Dict[str, Dict[str, int]]
) -> List[metaSeries]:
    """Create a batch of meta series from combinations."""
    batch_series = []

    for combo in combinations:
        series = build_series_from_combination(combo, lookup_maps)
        if series:
            session.add(series)
            batch_series.append(series)

    if batch_series:
        await session.commit()
        for ms in batch_series:
            await session.refresh(ms)

    return batch_series


async def create_meta_series(
    session, lookup_maps: Dict, num_series: int = 200
) -> List[metaSeries]:
    """Create meta series using varied enum values with async concurrency."""
    logger.info(f"📈 Creating {num_series} meta series with varied enum values...")

    # Get valid combinations
    all_combinations = get_valid_combinations()

    # Sample or use all combinations up to num_series
    if len(all_combinations) > num_series:
        combinations = random.sample(all_combinations, num_series)
    else:
        combinations = all_combinations
        # Add more random combinations if needed
        while len(combinations) < num_series:
            additional = random.sample(
                all_combinations,
                min(len(all_combinations), num_series - len(combinations)),
            )
            combinations.extend(additional)

    # Create series in batches for better performance
    batch_size = 100
    meta_series_list = []

    for i in range(0, len(combinations), batch_size):
        batch = combinations[i : i + batch_size]
        batch_series = await create_meta_series_batch(session, batch, lookup_maps)
        meta_series_list.extend(batch_series)
        logger.info(f"Created batch {i // batch_size + 1}: {len(batch_series)} series")

    logger.success(f"Created {len(meta_series_list)} meta series")
    return meta_series_list


# ============================================================================
# ClickHouse Value Data Creation
# ============================================================================


class ValueDataRecord:
    """Simple record class for ClickHouse value data insertion."""

    def __init__(self, series_id, timestamp, value, created_at, updated_at):
        self.series_id = series_id
        self.timestamp = timestamp
        self.value = value
        self.created_at = created_at
        self.updated_at = updated_at


def generate_value_for_series(series: metaSeries) -> Decimal:
    """Generate a realistic value based on series characteristics."""
    if series.is_derived:
        base_value = random.uniform(100.0, 500.0)
    else:
        base_value = random.uniform(10.0, 10000.0)
    return Decimal(str(base_value))


def create_value_data_record(
    series: metaSeries, timestamp: date, base_date: date
) -> ValueDataRecord:
    """Create a ValueDataRecord for a series at a specific timestamp."""
    return ValueDataRecord(
        series_id=series.series_id,
        timestamp=timestamp,
        value=generate_value_for_series(series),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


async def _insert_batch_clickhouse(crud_ch, session, batch: List[ValueDataRecord]):
    """Insert a batch of ValueData records into ClickHouse using bulk insert."""

    def _sync_bulk_insert():
        insert_data = []
        for vd in batch:
            insert_data.append(
                [
                    vd.series_id,
                    vd.timestamp,
                    float(vd.value),
                    vd.created_at,
                    vd.updated_at,
                ]
            )

        crud_ch.client.insert(
            "value_data",
            insert_data,
            column_names=[
                "series_id",
                "timestamp",
                "value",
                "created_at",
                "updated_at",
            ],
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_bulk_insert)


async def create_clickhouse_value_data(
    session,
    meta_series_list: List[metaSeries],
    num_per_series: int = 100,
    max_concurrent: int = 10,
) -> int:
    """Create value data entries in ClickHouse for all series using efficient batching."""
    logger.info(
        f"💹 Creating ClickHouse value data entries ({num_per_series} per series)..."
    )

    # Check if ClickHouse is initialized
    if (
        not _clickhouse_connection_manager.is_initialized()
        or _clickhouse_connection_manager.client is None
    ):
        logger.warning(
            "ClickHouse not initialized or not available. Skipping value_data seeding."
        )
        return 0

    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)

    total_count = 0
    base_date = date.today() - timedelta(days=num_per_series)
    batch_size = 500  # Number of value data entries per batch
    current_batch = []
    batch_count = 0

    for series in meta_series_list:
        for i in range(num_per_series):
            timestamp = base_date + timedelta(days=i)
            value_data = create_value_data_record(series, timestamp, base_date)
            current_batch.append(value_data)
            total_count += 1

            # Insert batch when full
            if len(current_batch) >= batch_size:
                await _insert_batch_clickhouse(crud_ch, session, current_batch)
                batch_count += 1
                logger.info(
                    f"Inserted batch {batch_count}: {len(current_batch)} entries (Total: {total_count})"
                )
                current_batch = []

    # Insert remaining entries
    if current_batch:
        await _insert_batch_clickhouse(crud_ch, session, current_batch)
        batch_count += 1
        logger.info(
            f"Inserted final batch {batch_count}: {len(current_batch)} entries (Total: {total_count})"
        )

    logger.success(f"Created {total_count} ClickHouse value data entries")
    return total_count


# ============================================================================
# Main Seeding Function
# ============================================================================


async def seed_real_financial_data(
    num_series: int = 200,
    num_value_data_per_series: int = 100,
    max_concurrent: int = 10,
):
    """Seed the database with real financial instrument data using varied enum values and async concurrency."""
    # Initialize PostgreSQL database
    init_db()

    # Initialize ClickHouse (optional, will skip if not available)
    clickhouse_available = False
    try:
        init_clickhouse()
        if _clickhouse_connection_manager.is_initialized():
            clickhouse_available = True
            logger.success("ClickHouse connection initialized")
    except Exception as e:
        logger.warning(f"ClickHouse initialization failed: {e}")
        logger.info("Continuing without ClickHouse value_data seeding...")

    try:
        async with get_session_context() as session:
            logger.info("🌱 Starting database seeding with real financial data...")
            logger.info(f"   - Target series: {num_series}")
            logger.info(f"   - Value data per series: {num_value_data_per_series}")
            logger.info(f"   - Max concurrent operations: {max_concurrent}")

            # Step 1: Create lookup tables
            lookup_maps = await create_lookup_tables(session)

            # Step 2: Create Meta Series with varied enum values
            meta_series_list = await create_meta_series(
                session, lookup_maps, num_series
            )

            # Step 3: Create Value Data in ClickHouse
            if clickhouse_available:
                total_value_data = await create_clickhouse_value_data(
                    session, meta_series_list, num_value_data_per_series, max_concurrent
                )
            else:
                logger.warning(
                    "Skipping value_data creation - ClickHouse not available"
                )
                total_value_data = 0

            # Summary
            logger.success("🎉 Database seeding completed successfully!")
            logger.info("📊 Summary:")
            logger.info(f"   - Asset Classes: {len(lookup_maps['asset_classes'])}")
            logger.info(f"   - Product Types: {len(lookup_maps['product_types'])}")
            logger.info(
                f"   - Sub Asset Classes: {len(lookup_maps['sub_asset_classes'])}"
            )
            logger.info(f"   - Data Types: {len(lookup_maps['data_types'])}")
            logger.info(f"   - Structure Types: {len(lookup_maps['structure_types'])}")
            logger.info(f"   - Market Segments: {len(lookup_maps['market_segments'])}")
            logger.info(f"   - Field Types: {len(lookup_maps['field_types'])}")
            logger.info(
                f"   - Ticker Sources: {len(lookup_maps.get('ticker_sources', {})) if lookup_maps.get('ticker_sources') else 'N/A'}"
            )
            logger.info(f"   - Meta Series: {len(meta_series_list)}")
            logger.info(
                f"   - Value Data: {total_value_data} (ClickHouse: {'✅' if clickhouse_available else '❌'})"
            )
    finally:
        # Close ClickHouse connection if it was opened
        if clickhouse_available:
            try:
                close_clickhouse()
                logger.success("ClickHouse connection closed")
            except Exception as e:
                logger.warning(f"Error closing ClickHouse connection: {e}")


# ============================================================================
# CLI Entry Point
# ============================================================================


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed the database with real financial instrument data"
    )
    parser.add_argument(
        "--series",
        type=int,
        default=200,
        help="Number of meta series to create (default: 200)",
    )
    parser.add_argument(
        "--value-data",
        type=int,
        default=100,
        help="Number of value data entries per series (default: 100)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Maximum number of concurrent operations (default: 10)",
    )

    args = parser.parse_args()

    try:
        await seed_real_financial_data(
            num_series=args.series,
            num_value_data_per_series=args.value_data,
            max_concurrent=args.concurrent,
        )
    except Exception as e:
        logger.exception(f"Error seeding database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
