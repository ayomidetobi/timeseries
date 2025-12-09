#!/usr/bin/env python3
"""Database seeding script with real financial instrument data using Factory Boy."""
import asyncio
import sys
import random
from pathlib import Path
from typing import List, Dict
from datetime import date, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init, get_session_context
from app.models.meta_series import MetaSeries, DataSource
from tests.factories import (
    AssetClassFactory,
    ProductTypeFactory,
    SubAssetClassFactory,
    DataTypeFactory,
    StructureTypeFactory,
    MarketSegmentFactory,
    FieldTypeFactory,
    MetaSeriesFactory,
    ValueDataFactory,
)
from faker import Faker
from app.constants.lookup_enums import (
    AssetClassEnum,
    SubAssetClassEnum,
    ProductTypeEnum,
    StructureTypeEnum,
    MarketSegmentEnum,
    DataTypeEnum,
    FieldTypeEnum,
    TICKER_SUFFIX_MAP,
    COMMODITY_NAMES,
    COMMODITY_SUB_ASSET_MAP,
    ASSET_CLASS_SUB_ASSET_MAP,
    FX_MARKET_SUB_ASSET_MAP,
)

fake = Faker()
random.seed()  # Initialize random seed


def generate_fx_pair() -> str:
    """Generate a currency pair using fake currency codes."""
    currency1 = fake.currency_code()
    currency2 = fake.currency_code()
    # Ensure they're different
    while currency1 == currency2:
        currency2 = fake.currency_code()
    return f"{currency1}{currency2}"


def generate_ticker(asset_class: AssetClassEnum, product: ProductTypeEnum, series_name: str) -> str:
    """Generate ticker based on asset class, product type, and series name."""
    suffix = TICKER_SUFFIX_MAP.get((asset_class, product), "Index")
    # Use series name as ticker code, clean it up for ticker format
    ticker_code = series_name.replace(",", "").replace(" ", "").upper()
    return f"{ticker_code} {suffix}"




async def create_lookup_tables(session) -> Dict[str, Dict[str, int]]:
    """Create all lookup tables using Factory Boy with enum values."""
    print("\n📊 Creating lookup tables...")
    from sqlalchemy import text
    
    # Check existing asset classes first
    result = await session.execute(
        text("SELECT asset_class_id, asset_class_name FROM asset_class_lookup")
    )
    existing_asset_classes = {row.asset_class_name: row.asset_class_id for row in result}
    
    # Create Asset Classes using Factory Boy with enum values (only if they don't exist)
    asset_classes = existing_asset_classes.copy()
    for asset_class_enum in AssetClassEnum:
        if asset_class_enum.value not in asset_classes:
            ac = AssetClassFactory.build(
                asset_class_name=asset_class_enum.value,
                description=f"{asset_class_enum.value} asset class"
            )
            session.add(ac)
    await session.commit()
    
    # Refresh to get IDs (including newly created ones)
    result = await session.execute(
        text("SELECT asset_class_id, asset_class_name FROM asset_class_lookup")
    )
    for row in result:
        asset_classes[row.asset_class_name] = row.asset_class_id
    
    # Check existing product types
    result = await session.execute(
        text("SELECT product_type_id, product_type_name FROM product_type_lookup")
    )
    existing_product_types = {row.product_type_name: row.product_type_id for row in result}
    
    # Create Product Types using Factory Boy with enum values (only if they don't exist)
    product_types = existing_product_types.copy()
    for product_enum in ProductTypeEnum:
        if product_enum.value not in product_types:
            pt = ProductTypeFactory.build(
                product_type_name=product_enum.value,
                description=f"{product_enum.value} product type",
                is_derived=(product_enum == ProductTypeEnum.INDEX)
            )
            session.add(pt)
    await session.commit()
    
    result = await session.execute(
        text("SELECT product_type_id, product_type_name FROM product_type_lookup")
    )
    for row in result:
        product_types[row.product_type_name] = row.product_type_id
    
    # Check existing sub asset classes
    result = await session.execute(
        text("SELECT sub_asset_class_id, sub_asset_class_name FROM sub_asset_class_lookup")
    )
    existing_sub_asset_classes = {row.sub_asset_class_name: row.sub_asset_class_id for row in result}
    
    # Create Sub Asset Classes using Factory Boy with enum values (only if they don't exist)
    sub_asset_classes = existing_sub_asset_classes.copy()
    for asset_class_enum, sub_asset_list in ASSET_CLASS_SUB_ASSET_MAP.items():
        for sub_asset_enum in sub_asset_list:
            if sub_asset_enum.value not in sub_asset_classes:
                asset_class_id = asset_classes.get(asset_class_enum.value)
                sac = SubAssetClassFactory.build(
                    sub_asset_class_name=sub_asset_enum.value,
                    asset_class_id=asset_class_id,
                    description=f"{sub_asset_enum.value} sub-asset class"
                )
                session.add(sac)
    await session.commit()
    
    result = await session.execute(
        text("SELECT sub_asset_class_id, sub_asset_class_name FROM sub_asset_class_lookup")
    )
    for row in result:
        sub_asset_classes[row.sub_asset_class_name] = row.sub_asset_class_id
    
    # Check existing data types
    result = await session.execute(
        text("SELECT data_type_id, data_type_name FROM data_type_lookup")
    )
    existing_data_types = {row.data_type_name: row.data_type_id for row in result}
    
    # Create Data Types using Factory Boy with enum values (only if they don't exist)
    data_types = existing_data_types.copy()
    for data_type_enum in DataTypeEnum:
        if data_type_enum.value not in data_types:
            dt = DataTypeFactory.build(
                data_type_name=data_type_enum.value,
                description=f"{data_type_enum.value} data type"
            )
            session.add(dt)
    await session.commit()
    
    result = await session.execute(
        text("SELECT data_type_id, data_type_name FROM data_type_lookup")
    )
    for row in result:
        data_types[row.data_type_name] = row.data_type_id
    
    # Check existing structure types
    result = await session.execute(
        text("SELECT structure_type_id, structure_type_name FROM structure_type_lookup")
    )
    existing_structure_types = {row.structure_type_name: row.structure_type_id for row in result}
    
    # Create Structure Types using Factory Boy with enum values (only if they don't exist)
    structure_types = existing_structure_types.copy()
    for structure_enum in StructureTypeEnum:
        if structure_enum.value not in structure_types:
            st = StructureTypeFactory.build(
                structure_type_name=structure_enum.value,
                description=f"{structure_enum.value} structure type"
            )
            session.add(st)
    await session.commit()
    
    result = await session.execute(
        text("SELECT structure_type_id, structure_type_name FROM structure_type_lookup")
    )
    for row in result:
        structure_types[row.structure_type_name] = row.structure_type_id
    
    # Check existing market segments
    result = await session.execute(
        text("SELECT market_segment_id, market_segment_name FROM market_segment_lookup")
    )
    existing_market_segments = {row.market_segment_name: row.market_segment_id for row in result}
    
    # Create Market Segments using Factory Boy with enum values (only if they don't exist)
    market_segments = existing_market_segments.copy()
    for market_enum in MarketSegmentEnum:
        if market_enum.value not in market_segments:
            ms = MarketSegmentFactory.build(
                market_segment_name=market_enum.value,
                description=f"{market_enum.value} market segment"
            )
            session.add(ms)
    await session.commit()
    
    result = await session.execute(
        text("SELECT market_segment_id, market_segment_name FROM market_segment_lookup")
    )
    for row in result:
        market_segments[row.market_segment_name] = row.market_segment_id
    
    # Check existing field types
    result = await session.execute(
        text("SELECT field_type_id, field_type_name FROM field_type_lookup")
    )
    existing_field_types = {row.field_type_name: row.field_type_id for row in result}
    
    # Create Field Types using Factory Boy with enum values (only if they don't exist)
    field_types = existing_field_types.copy()
    for field_type_enum in FieldTypeEnum:
        if field_type_enum.value not in field_types:
            ft = FieldTypeFactory.build(
                field_type_name=field_type_enum.value,
                description=f"{field_type_enum.value} field type"
            )
            session.add(ft)
    await session.commit()
    
    result = await session.execute(
        text("SELECT field_type_id, field_type_name FROM field_type_lookup")
    )
    for row in result:
        field_types[row.field_type_name] = row.field_type_id
    
    print("✅ Created lookup tables:")
    print(f"   - Asset Classes: {len(asset_classes)}")
    print(f"   - Product Types: {len(product_types)}")
    print(f"   - Sub Asset Classes: {len(sub_asset_classes)}")
    print(f"   - Data Types: {len(data_types)}")
    print(f"   - Structure Types: {len(structure_types)}")
    print(f"   - Market Segments: {len(market_segments)}")
    print(f"   - Field Types: {len(field_types)}")
    
    return {
        "asset_classes": asset_classes,
        "product_types": product_types,
        "sub_asset_classes": sub_asset_classes,
        "data_types": data_types,
        "structure_types": structure_types,
        "market_segments": market_segments,
        "field_types": field_types,
    }


def get_valid_combinations() -> List[Dict]:
    """Generate valid combinations of asset class, sub-asset class, product type, etc."""
    combinations = []
    
    # Commodity combinations
    for commodity_name in COMMODITY_NAMES:
        for sub, commodities in COMMODITY_SUB_ASSET_MAP.items():
            if commodity_name in commodities:
                # Use varied data types and field types
                data_type = random.choice([DataTypeEnum.PRICE, DataTypeEnum.OPEN_INTEREST])
                field_type = FieldTypeEnum.PX_LAST if data_type == DataTypeEnum.PRICE else FieldTypeEnum.OPEN_INT
                market_segment = random.choice(list(MarketSegmentEnum))
                
                combinations.append({
                    "asset_class": AssetClassEnum.COMMODITY,
                    "sub_asset_class": sub,
                    "product_type": random.choice([ProductTypeEnum.SPOT, ProductTypeEnum.INDEX]),
                    "data_type": data_type,
                    "field_type": field_type,
                    "market_segment": market_segment,
                    "series_name": commodity_name,
                    "is_derived": False,
                })
    
    # Credit combinations with varied market segments
    credit_regions = [
        ("US IG", MarketSegmentEnum.DM),
        ("EZ IG", MarketSegmentEnum.DM),
        ("UK IG", MarketSegmentEnum.DM),
        ("US HY", MarketSegmentEnum.DM),
        ("Japan IG", MarketSegmentEnum.DM),
        ("EZ HY", MarketSegmentEnum.DM),
        ("EM Credit", MarketSegmentEnum.EM),
        ("Asia Credit", MarketSegmentEnum.EM),
        ("Latam Credit", MarketSegmentEnum.EM),
    ]
    
    for region_name, market in credit_regions:
        combinations.append({
            "asset_class": AssetClassEnum.CREDIT,
            "sub_asset_class": SubAssetClassEnum.OAS,
            "product_type": ProductTypeEnum.INDEX,
            "data_type": DataTypeEnum.PRICE_SPREAD,
            "field_type": random.choice([FieldTypeEnum.PX_LAST, FieldTypeEnum.PX_OPEN]),
            "market_segment": market,
            "series_name": f"{region_name}, OAS",
            "is_derived": True,
        })
    
    # FX combinations with varied sub-asset classes and market segments
    for market_segment, sub_assets in FX_MARKET_SUB_ASSET_MAP.items():
        for sub_asset in sub_assets:
            for _ in range(random.randint(3, 8)):  # 3-8 pairs per combination
                pair = generate_fx_pair()
                combinations.append({
                    "asset_class": AssetClassEnum.FX,
                    "sub_asset_class": sub_asset,
                    "product_type": random.choice([ProductTypeEnum.SPOT, ProductTypeEnum.INDEX]),
                    "data_type": DataTypeEnum.PRICE,
                    "field_type": random.choice(list(FieldTypeEnum)),
                    "market_segment": market_segment,
                    "series_name": pair,
                    "is_derived": random.choice([True, False]) if ProductTypeEnum.INDEX else False,
                })
    
    # Additional random combinations using all enum values
    for _ in range(50):  # Generate 50 additional random series
        asset_class = random.choice(list(AssetClassEnum))
        sub_assets = ASSET_CLASS_SUB_ASSET_MAP.get(asset_class, [])
        if sub_assets:
            sub_asset = random.choice(sub_assets)
            product_type = random.choice(list(ProductTypeEnum))
            data_type = random.choice(list(DataTypeEnum))
            market_segment = random.choice(list(MarketSegmentEnum))
            field_type = random.choice(list(FieldTypeEnum))
            
            # Generate appropriate series name
            if asset_class == AssetClassEnum.COMMODITY:
                series_name = random.choice(COMMODITY_NAMES)
            elif asset_class == AssetClassEnum.FX:
                series_name = generate_fx_pair()
            else:
                series_name = f"{fake.company()} {fake.word().title()}"
            
            combinations.append({
                "asset_class": asset_class,
                "sub_asset_class": sub_asset,
                "product_type": product_type,
                "data_type": data_type,
                "field_type": field_type,
                "market_segment": market_segment,
                "series_name": series_name,
                "is_derived": product_type == ProductTypeEnum.INDEX and random.choice([True, False]),
            })
    
    return combinations


async def create_meta_series(session, lookup_maps: Dict, num_series: int = 200) -> List[MetaSeries]:
    """Create meta series using varied enum values with async concurrency."""
    print(f"\n📈 Creating {num_series} meta series with varied enum values...")
    
    meta_series_list = []
    asset_classes = lookup_maps["asset_classes"]
    product_types = lookup_maps["product_types"]
    sub_asset_classes = lookup_maps["sub_asset_classes"]
    data_types = lookup_maps["data_types"]
    structure_types = lookup_maps["structure_types"]
    market_segments = lookup_maps["market_segments"]
    field_types = lookup_maps["field_types"]
    
    # Get valid combinations
    all_combinations = get_valid_combinations()
    
    # Sample or use all combinations up to num_series
    if len(all_combinations) > num_series:
        combinations = random.sample(all_combinations, num_series)
    else:
        combinations = all_combinations
        # Add more random combinations if needed
        while len(combinations) < num_series:
            combinations.extend(random.sample(all_combinations, min(len(all_combinations), num_series - len(combinations))))
    
    # Create series in batches for better performance
    batch_size = 100
    for i in range(0, len(combinations), batch_size):
        batch = combinations[i:i + batch_size]
        batch_series = []
        
        for combo in batch:
            try:
                ticker = generate_ticker(combo["asset_class"], combo["product_type"], combo["series_name"])
                field_type_name = combo["field_type"].value if isinstance(combo["field_type"], FieldTypeEnum) else combo["field_type"]
                
                series = MetaSeriesFactory.build(
                    series_name=combo["series_name"],
                    asset_class_id=asset_classes.get(combo["asset_class"].value),
                    sub_asset_class_id=sub_asset_classes.get(combo["sub_asset_class"].value),
                    product_type_id=product_types.get(combo["product_type"].value),
                    data_type_id=data_types.get(combo["data_type"].value),
                    structure_type_id=structure_types.get(StructureTypeEnum.OUTRIGHT.value),
                    market_segment_id=market_segments.get(combo["market_segment"].value),
                    ticker=ticker,
                    flds_id=field_types.get(field_type_name),
                    is_active=random.choice([True, True, True, False]),  # 75% active
                    is_derived=combo["is_derived"],
                    source=random.choice([DataSource.RAW, DataSource.DERIVED]) if combo["is_derived"] else DataSource.RAW,
                    version_number=random.randint(1, 5),
                )
                session.add(series)
                batch_series.append(series)
            except (KeyError, AttributeError) as e:
                # Skip invalid combinations
                print(f"  ⚠️  Skipping invalid combination: {e}")
                continue
        
        meta_series_list.extend(batch_series)
        
        # Commit in batches
        if batch_series:
            await session.commit()
            for ms in batch_series:
                await session.refresh(ms)
            print(f"  Created batch {i // batch_size + 1}: {len(batch_series)} series")
    
    print(f"✅ Created {len(meta_series_list)} meta series")
    return meta_series_list


async def create_value_data(
    session, meta_series_list: List[MetaSeries], num_per_series: int = 100, max_concurrent: int = 10
) -> int:
    """Create value data entries for all series using efficient batching."""
    print(f"\n💹 Creating value data entries ({num_per_series} per series)...")
    total_count = 0
    base_date = date.today() - timedelta(days=num_per_series)
    
    # Process in batches to avoid memory issues and improve performance
    # Use larger batches for better database performance
    batch_size = 500  # Number of value data entries per batch
    
    current_batch = []
    batch_count = 0
    
    for series in meta_series_list:
        for i in range(num_per_series):
            value_data = ValueDataFactory.build(
                series_id=series.series_id,
                timestamp=base_date + timedelta(days=i),
            )
            session.add(value_data)
            current_batch.append(value_data)
            total_count += 1
            
            # Commit when batch is full
            if len(current_batch) >= batch_size:
                await session.commit()
                batch_count += 1
                print(f"  Committed batch {batch_count}: {len(current_batch)} entries (Total: {total_count})")
                current_batch = []
    
    # Commit remaining entries
    if current_batch:
        await session.commit()
        batch_count += 1
        print(f"  Committed final batch {batch_count}: {len(current_batch)} entries (Total: {total_count})")
    
    print(f"✅ Created {total_count} value data entries")
    return total_count


async def seed_real_financial_data(
    num_series: int = 200,
    num_value_data_per_series: int = 100,
    max_concurrent: int = 10
):
    """Seed the database with real financial instrument data using varied enum values and async concurrency."""
    init()
    
    async with get_session_context() as session:
        print("🌱 Starting database seeding with real financial data...")
        print(f"   - Target series: {num_series}")
        print(f"   - Value data per series: {num_value_data_per_series}")
        print(f"   - Max concurrent operations: {max_concurrent}")
        
        # Step 1: Create lookup tables
        lookup_maps = await create_lookup_tables(session)
        
        # Step 2: Create Meta Series with varied enum values
        meta_series_list = await create_meta_series(session, lookup_maps, num_series)
        
        # Step 3: Create Value Data with async concurrency
        total_value_data = await create_value_data(
            session, meta_series_list, num_value_data_per_series, max_concurrent
        )
        
        # Summary
        print("\n🎉 Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Asset Classes: {len(lookup_maps['asset_classes'])}")
        print(f"   - Product Types: {len(lookup_maps['product_types'])}")
        print(f"   - Sub Asset Classes: {len(lookup_maps['sub_asset_classes'])}")
        print(f"   - Data Types: {len(lookup_maps['data_types'])}")
        print(f"   - Market Segments: {len(lookup_maps['market_segments'])}")
        print(f"   - Field Types: {len(lookup_maps['field_types'])}")
        print(f"   - Meta Series: {len(meta_series_list)}")
        print(f"   - Value Data: {total_value_data}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed the database with real financial instrument data")
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
            max_concurrent=args.concurrent
        )
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
