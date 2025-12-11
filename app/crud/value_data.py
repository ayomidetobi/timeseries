"""CRUD operations for valueData using ClickHouse."""

import asyncio
from typing import Optional, cast, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import clickhouse_connect
import pytimeparse2  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.value_data import valueData
from app.models.meta_series import metaSeries
from app.models.lookup_tables import (
    assetClassLookup,
    subAssetClassLookup,
    productTypeLookup,
    dataTypeLookup,
    structureTypeLookup,
    marketSegmentLookup,
    fieldTypeLookup,
    tickerSourceLookup,
)
from app.schemas.filters import valueDataFilter


class crudValueData:
    """CRUD operations for valueData in ClickHouse."""

    def __init__(self, clickhouse_client: clickhouse_connect.driver.Client):
        """Initialize with ClickHouse client."""
        self.client = clickhouse_client

    def _build_clickhouse_conditions(
        self, filter_obj: valueDataFilter
    ) -> tuple[list[str], dict[str, Any]]:
        """Build ClickHouse query conditions and parameters from filter object."""
        conditions = []
        params: dict[str, Any] = {}

        # Direct valueData filters
        if filter_obj.series_id__in is not None:
            series_ids = cast(list[int], filter_obj.series_id__in)
            conditions.append(f"series_id IN ({','.join(map(str, series_ids))})")

        # Timestamp filters
        if filter_obj.timestamp__ago is not None:
            seconds_ago = pytimeparse2.parse(filter_obj.timestamp__ago)
            if seconds_ago is not None:
                time_ago = datetime.now() - timedelta(seconds=seconds_ago)
                conditions.append("timestamp >= {timestamp__gte:Date}")
                params["timestamp__gte"] = time_ago.date()

        if filter_obj.timestamp__gte is not None:
            conditions.append("timestamp >= {timestamp__gte:Date}")
            params["timestamp__gte"] = filter_obj.timestamp__gte

        if filter_obj.timestamp__lte is not None:
            conditions.append("timestamp <= {timestamp__lte:Date}")
            params["timestamp__lte"] = filter_obj.timestamp__lte

        # Value filters
        if filter_obj.value__gte is not None:
            conditions.append("value >= {value__gte:Float64}")
            params["value__gte"] = float(filter_obj.value__gte)

        if filter_obj.value__lte is not None:
            conditions.append("value <= {value__lte:Float64}")
            params["value__lte"] = float(filter_obj.value__lte)

        return conditions, params

    def _has_metadata_filters(self, filter_obj: valueDataFilter) -> bool:
        """Check if filter object contains any metadata filters that require PostgreSQL query."""
        metadata_filter_fields = [
            filter_obj.series_name__ilike,
            filter_obj.series_name__in,
            filter_obj.ticker__ilike,
            filter_obj.is_active,
            filter_obj.is_derived,
            filter_obj.is_latest,
            filter_obj.asset_class_name__in,
            filter_obj.sub_asset_class_name__in,
            filter_obj.product_type_name__in,
            filter_obj.data_type_name__in,
            filter_obj.structure_type_name__in,
            filter_obj.market_segment_name__in,
            filter_obj.field_type_name__in,
            filter_obj.ticker_source_name__in,
            filter_obj.ticker_source_code__in,
        ]
        return any(metadata_filter_fields)

    def _build_order_by_clause(self, filter_obj: valueDataFilter) -> str:
        """Build ORDER BY clause from filter object."""
        if not filter_obj.order_by:
            return "ORDER BY timestamp DESC"

        order_parts = []
        for order_field in filter_obj.order_by:
            field_name = order_field[1:] if order_field.startswith("-") else order_field
            direction = "DESC" if order_field.startswith("-") else "ASC"
            order_parts.append(f"{field_name} {direction}")

        return f"ORDER BY {', '.join(order_parts)}"

    def _build_meta_series_conditions(
        self, filter_obj: valueDataFilter
    ) -> tuple[list, dict[str, bool]]:
        """Build metaSeries filter conditions and track which joins are needed."""
        conditions = []
        joins_needed = {
            "asset_class": False,
            "sub_asset_class": False,
            "product_type": False,
            "data_type": False,
            "structure_type": False,
            "market_segment": False,
            "field_type": False,
            "ticker_source": False,
        }

        # metaSeries direct filters
        if filter_obj.series_name__ilike is not None:
            conditions.append(
                metaSeries.series_name.ilike(f"%{filter_obj.series_name__ilike}%")
            )

        if filter_obj.series_name__in is not None:
            condition = self._build_series_name_in_condition(filter_obj.series_name__in)
            if condition is not None:
                conditions.append(condition)

        if filter_obj.ticker__ilike is not None:
            conditions.append(metaSeries.ticker.ilike(f"%{filter_obj.ticker__ilike}%"))

        if filter_obj.is_active is not None:
            conditions.append(metaSeries.is_active == filter_obj.is_active)

        if filter_obj.is_derived is not None:
            conditions.append(metaSeries.is_derived == filter_obj.is_derived)

        if filter_obj.is_latest is not None:
            conditions.append(metaSeries.is_latest == filter_obj.is_latest)

        # Lookup table filters - using a map for cleaner code
        lookup_filter_map = {
            "asset_class_name__in": (
                assetClassLookup,
                "asset_class",
                "asset_class_name",
            ),
            "sub_asset_class_name__in": (
                subAssetClassLookup,
                "sub_asset_class",
                "sub_asset_class_name",
            ),
            "product_type_name__in": (
                productTypeLookup,
                "product_type",
                "product_type_name",
            ),
            "data_type_name__in": (dataTypeLookup, "data_type", "data_type_name"),
            "structure_type_name__in": (
                structureTypeLookup,
                "structure_type",
                "structure_type_name",
            ),
            "market_segment_name__in": (
                marketSegmentLookup,
                "market_segment",
                "market_segment_name",
            ),
            "field_type_name__in": (fieldTypeLookup, "field_type", "field_type_name"),
            "ticker_source_name__in": (
                tickerSourceLookup,
                "ticker_source",
                "ticker_source_name",
            ),
            "ticker_source_code__in": (
                tickerSourceLookup,
                "ticker_source",
                "ticker_source_code",
            ),
        }

        for field, (lookup_model, join_key, field_name) in lookup_filter_map.items():
            value = getattr(filter_obj, field, None)
            if value is not None:
                joins_needed[join_key] = True
                lookup_field = getattr(lookup_model, field_name)
                conditions.append(lookup_field.in_(cast(list[str], value)))

        return conditions, joins_needed

    def _build_series_name_in_condition(self, series_names: list[str]) -> Optional[Any]:
        """Build condition for series_name__in filter."""
        series_names_lower = [name.lower().strip() for name in series_names if name]
        if series_names_lower:
            return func.lower(metaSeries.series_name).in_(series_names_lower)
        return None

    def _apply_lookup_joins(self, query, joins_needed: dict[str, bool]):
        """Apply necessary joins to the query based on joins_needed dict."""
        join_map = {
            "asset_class": (
                assetClassLookup,
                metaSeries.asset_class_id == assetClassLookup.asset_class_id,
            ),
            "sub_asset_class": (
                subAssetClassLookup,
                metaSeries.sub_asset_class_id == subAssetClassLookup.sub_asset_class_id,
            ),
            "product_type": (
                productTypeLookup,
                metaSeries.product_type_id == productTypeLookup.product_type_id,
            ),
            "data_type": (
                dataTypeLookup,
                metaSeries.data_type_id == dataTypeLookup.data_type_id,
            ),
            "structure_type": (
                structureTypeLookup,
                metaSeries.structure_type_id == structureTypeLookup.structure_type_id,
            ),
            "market_segment": (
                marketSegmentLookup,
                metaSeries.market_segment_id == marketSegmentLookup.market_segment_id,
            ),
            "field_type": (
                fieldTypeLookup,
                metaSeries.flds_id == fieldTypeLookup.field_type_id,
            ),
            "ticker_source": (
                tickerSourceLookup,
                metaSeries.ticker_source_id == tickerSourceLookup.ticker_source_id,
            ),
        }

        for join_key, (lookup_model, join_condition) in join_map.items():
            if joins_needed.get(join_key, False):
                query = query.join(lookup_model, join_condition)

        return query

    def _convert_rows_to_value_data(self, rows: list) -> list[valueData]:
        """Convert ClickHouse query result rows to valueData objects."""
        return [
            valueData(
                series_id=row[0],
                timestamp=row[1],
                value=Decimal(str(row[2])),
                created_at=row[3],
                updated_at=row[4],
            )
            for row in rows
        ]

    async def get_by_id(
        self,
        *,
        series_id: int,
        timestamp: date,
    ) -> Optional[valueData]:
        """Get value data by series_id and timestamp."""

        def _sync_query():
            query = """
            SELECT 
                series_id,
                timestamp,
                value,
                created_at,
                updated_at
            FROM value_data
            WHERE series_id = {series_id:UInt32} AND timestamp = {timestamp:Date}
            LIMIT 1
            """
            return self.client.query(
                query,
                parameters={
                    "series_id": series_id,
                    "timestamp": timestamp,
                },
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_query)

        if result.result_rows:
            row = result.result_rows[0]
            return valueData(
                series_id=row[0],
                timestamp=row[1],
                value=Decimal(str(row[2])),
                created_at=row[3],
                updated_at=row[4],
            )
        return None

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: valueDataFilter,
    ) -> list[valueData]:
        """Get multiple value data records with filters.

        This method queries ClickHouse for value_data and PostgreSQL for metadata.
        It then combines the results.
        """
        # Build ClickHouse query conditions
        conditions, params = self._build_clickhouse_conditions(filter_obj)

        # Handle metadata filters via PostgreSQL query
        if self._has_metadata_filters(filter_obj):
            series_ids_filter = await self._get_filtered_series_ids(db, filter_obj)
            if not series_ids_filter:
                return []
            conditions.append(f"series_id IN ({','.join(map(str, series_ids_filter))})")

        # Build query components
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        order_by = self._build_order_by_clause(filter_obj)

        # Execute ClickHouse query
        def _sync_query():
            query = f"""
            SELECT 
                series_id,
                timestamp,
                value,
                created_at,
                updated_at
            FROM value_data
            WHERE {where_clause}
            {order_by}
            """
            return self.client.query(query, parameters=params)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_query)

        return self._convert_rows_to_value_data(result.result_rows)

    async def _get_filtered_series_ids(
        self,
        db: AsyncSession,
        filter_obj: valueDataFilter,
    ) -> list[int]:
        """Query PostgreSQL to get series_ids that match metadata filters."""
        query = select(metaSeries.series_id)

        # Build conditions and determine needed joins
        conditions, joins_needed = self._build_meta_series_conditions(filter_obj)

        # Apply joins
        query = self._apply_lookup_joins(query, joins_needed)

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return [row[0] for row in result.all()]

    async def create(
        self,
        *,
        obj_in: valueData,
    ) -> valueData:
        """Insert value data into ClickHouse."""

        def _sync_insert():
            # Note: is_latest, version_number, derived_flag, dependency_calculation_id, and field_name
            # are now on metaSeries, not valueData. Only store time-series data in ClickHouse.
            insert_data = [
                [
                    obj_in.series_id,
                    obj_in.timestamp,
                    float(obj_in.value),
                    obj_in.created_at,
                    obj_in.updated_at,
                ]
            ]

            self.client.insert(
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
        await loop.run_in_executor(None, _sync_insert)
        return obj_in

    async def create_with_validation(
        self,
        db: AsyncSession,
        *,
        obj_in: valueData,
    ) -> valueData:
        """Create value data with series validation."""
        # Verify series exists in PostgreSQL
        series_query = select(metaSeries).where(
            metaSeries.series_id == obj_in.series_id
        )
        series_result = await db.execute(series_query)
        if not series_result.scalar_one_or_none():
            raise ValueError("Series not found")

        return await self.create(obj_in=obj_in)

    async def update(
        self,
        *,
        series_id: int,
        timestamp: date,
        obj_in: dict,
    ) -> Optional[valueData]:
        """Update value data in ClickHouse.

        Note: ClickHouse doesn't support traditional UPDATE operations efficiently.
        This implementation deletes the old row and inserts a new one.
        For production, consider using ReplacingMergeTree engine or ALTER TABLE UPDATE.
        """
        # Get existing record
        existing = await self.get_by_id(series_id=series_id, timestamp=timestamp)
        if not existing:
            return None

        # Create updated record
        # Access attributes from valueData instance (works at runtime even with Column definitions)
        # Note: is_latest, version_number, derived_flag, dependency_calculation_id, and field_name
        # are now on metaSeries, not valueData
        updated = valueData(
            series_id=obj_in.get("series_id", getattr(existing, "series_id", None)),  # type: ignore
            timestamp=obj_in.get("timestamp", getattr(existing, "timestamp", None)),  # type: ignore
            value=obj_in.get("value", getattr(existing, "value", None)),  # type: ignore
            created_at=obj_in.get("created_at", getattr(existing, "created_at", None)),  # type: ignore
            updated_at=datetime.utcnow(),
        )

        # Note: ClickHouse doesn't support UPDATE operations efficiently.
        # For production, consider using ReplacingMergeTree engine.
        # For now, we'll insert a new version with updated data.
        # Note: is_latest filtering is now done via metaSeries in PostgreSQL
        return await self.create(obj_in=updated)

    async def get_derived(
        self,
        db: AsyncSession,
        *,
        filter_obj: valueDataFilter,
    ) -> list[valueData]:
        """Get derived value data (from series where is_derived=True)."""
        filter_obj.is_derived = True
        return await self.get_multi_with_filters(db=db, filter_obj=filter_obj)


def get_crud_value_data(
    clickhouse_client: clickhouse_connect.driver.Client,
) -> crudValueData:
    """Factory function to create CRUD instance."""
    return crudValueData(clickhouse_client)
