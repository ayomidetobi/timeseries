"""CRUD operations for ValueData."""
from typing import Optional, cast
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.sql import Select
import pytimeparse2

from app.crud.base import CRUDBase
from app.models.value_data import ValueData
from app.models.meta_series import MetaSeries
from app.models.lookup_tables import (
    AssetClassLookup,
    SubAssetClassLookup,
    ProductTypeLookup,
    DataTypeLookup,
    StructureTypeLookup,
    MarketSegmentLookup,
    FieldTypeLookup,
)
from app.schemas.filters import ValueDataFilter


class CRUDValueData(CRUDBase[ValueData]):
    """CRUD operations for ValueData."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        series_id: int,
        timestamp: date,
    ) -> Optional[ValueData]:
        """Get value data by series_id and timestamp."""
        query = select(ValueData).where(
            and_(
                ValueData.series_id == series_id,
                ValueData.timestamp == timestamp,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: ValueDataFilter,
    ) -> list[ValueData]:
        """Get multiple value data records with filters, including MetaSeries and lookup table filters."""
        # Start with ValueData and join MetaSeries for filtering
        query = select(ValueData).join(MetaSeries, ValueData.series_id == MetaSeries.series_id)
        
        # Track which lookup tables need to be joined (for name-based filtering)
        joins_needed = {
            'asset_class': False,
            'sub_asset_class': False,
            'product_type': False,
            'data_type': False,
            'structure_type': False,
            'market_segment': False,
            'field_type': False,
        }
        
        # Build conditions for filters that require MetaSeries join
        conditions = []
        
        # Direct ValueData filters
        if filter_obj.series_id is not None:
            conditions.append(ValueData.series_id == filter_obj.series_id)
        if filter_obj.series_id__in is not None:
            conditions.append(ValueData.series_id.in_(cast(list[int], filter_obj.series_id__in)))
        
        # Handle humanized timestamp filter (e.g., "1y", "2y", "20m")
        if filter_obj.timestamp__ago is not None:
            # Parse humanized time string to seconds
            seconds_ago = pytimeparse2.parse(filter_obj.timestamp__ago)
            if seconds_ago is not None:
                # Calculate the date that is X time ago from now
                time_ago = datetime.now() - timedelta(seconds=seconds_ago)
                date_ago = time_ago.date()
                # Filter for data from that date onwards (historical data from X time ago to now)
                conditions.append(ValueData.timestamp >= date_ago)
        
        if filter_obj.timestamp__gte is not None:
            conditions.append(ValueData.timestamp >= filter_obj.timestamp__gte)
        if filter_obj.timestamp__lte is not None:
            conditions.append(ValueData.timestamp <= filter_obj.timestamp__lte)
        if filter_obj.is_latest is not None:
            conditions.append(ValueData.is_latest == filter_obj.is_latest)
        if filter_obj.value__gte is not None:
            conditions.append(ValueData.value >= filter_obj.value__gte)
        if filter_obj.value__lte is not None:
            conditions.append(ValueData.value <= filter_obj.value__lte)
        
        # MetaSeries filters
        if filter_obj.series_name__ilike is not None:
            conditions.append(MetaSeries.series_name.ilike(f"%{filter_obj.series_name__ilike}%"))  # type: ignore[attr-defined]
        if filter_obj.series_name__in is not None:
            series_names_lower = [name.lower().strip() for name in filter_obj.series_name__in if name]
            if series_names_lower:  # Only add condition if list is not empty
                conditions.append(func.lower(MetaSeries.series_name).in_(series_names_lower))  # type: ignore[attr-defined]
        if filter_obj.ticker__ilike is not None:
            conditions.append(MetaSeries.ticker.ilike(f"%{filter_obj.ticker__ilike}%"))  # type: ignore[attr-defined]
        if filter_obj.is_active is not None:
            conditions.append(MetaSeries.is_active == filter_obj.is_active)
        if filter_obj.is_derived is not None:
            conditions.append(MetaSeries.is_derived == filter_obj.is_derived)
        
        # Lookup table filters (via MetaSeries join) - using names as primary keys for filtering
        if filter_obj.asset_class_name is not None:
            joins_needed['asset_class'] = True
            conditions.append(AssetClassLookup.asset_class_name == filter_obj.asset_class_name)
        if filter_obj.asset_class_name__in is not None:
            joins_needed['asset_class'] = True
            conditions.append(AssetClassLookup.asset_class_name.in_(cast(list[str], filter_obj.asset_class_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.sub_asset_class_name is not None:
            joins_needed['sub_asset_class'] = True
            conditions.append(SubAssetClassLookup.sub_asset_class_name == filter_obj.sub_asset_class_name)
        if filter_obj.sub_asset_class_name__in is not None:
            joins_needed['sub_asset_class'] = True
            conditions.append(SubAssetClassLookup.sub_asset_class_name.in_(cast(list[str], filter_obj.sub_asset_class_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.product_type_name is not None:
            joins_needed['product_type'] = True
            conditions.append(ProductTypeLookup.product_type_name == filter_obj.product_type_name)
        if filter_obj.product_type_name__in is not None:
            joins_needed['product_type'] = True
            conditions.append(ProductTypeLookup.product_type_name.in_(cast(list[str], filter_obj.product_type_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.data_type_name is not None:
            joins_needed['data_type'] = True
            conditions.append(DataTypeLookup.data_type_name == filter_obj.data_type_name)
        if filter_obj.data_type_name__in is not None:
            joins_needed['data_type'] = True
            conditions.append(DataTypeLookup.data_type_name.in_(cast(list[str], filter_obj.data_type_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.structure_type_name is not None:
            joins_needed['structure_type'] = True
            conditions.append(StructureTypeLookup.structure_type_name == filter_obj.structure_type_name)
        if filter_obj.structure_type_name__in is not None:
            joins_needed['structure_type'] = True
            conditions.append(StructureTypeLookup.structure_type_name.in_(cast(list[str], filter_obj.structure_type_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.market_segment_name is not None:
            joins_needed['market_segment'] = True
            conditions.append(MarketSegmentLookup.market_segment_name == filter_obj.market_segment_name)
        if filter_obj.market_segment_name__in is not None:
            joins_needed['market_segment'] = True
            conditions.append(MarketSegmentLookup.market_segment_name.in_(cast(list[str], filter_obj.market_segment_name__in)))  # type: ignore[attr-defined]
        
        if filter_obj.field_type_name is not None:
            joins_needed['field_type'] = True
            conditions.append(FieldTypeLookup.field_type_name == filter_obj.field_type_name)
        if filter_obj.field_type_name__in is not None:
            joins_needed['field_type'] = True
            conditions.append(FieldTypeLookup.field_type_name.in_(cast(list[str], filter_obj.field_type_name__in)))  # type: ignore[attr-defined]
        
        # Add joins for lookup tables when needed
        if joins_needed['asset_class']:
            query = query.join(AssetClassLookup, MetaSeries.asset_class_id == AssetClassLookup.asset_class_id)
        if joins_needed['sub_asset_class']:
            query = query.join(SubAssetClassLookup, MetaSeries.sub_asset_class_id == SubAssetClassLookup.sub_asset_class_id)
        if joins_needed['product_type']:
            query = query.join(ProductTypeLookup, MetaSeries.product_type_id == ProductTypeLookup.product_type_id)
        if joins_needed['data_type']:
            query = query.join(DataTypeLookup, MetaSeries.data_type_id == DataTypeLookup.data_type_id)
        if joins_needed['structure_type']:
            query = query.join(StructureTypeLookup, MetaSeries.structure_type_id == StructureTypeLookup.structure_type_id)
        if joins_needed['market_segment']:
            query = query.join(MarketSegmentLookup, MetaSeries.market_segment_id == MarketSegmentLookup.market_segment_id)
        if joins_needed['field_type']:
            query = query.join(FieldTypeLookup, MetaSeries.flds_id == FieldTypeLookup.field_type_id)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))  # type: ignore[arg-type]
        
        # Apply ordering
        if filter_obj.order_by:
            query = self._apply_ordering(query, filter_obj.order_by)
        else:
            # Default ordering by timestamp descending
            from sqlalchemy import desc
            query = query.order_by(desc(ValueData.timestamp))
        
        # Eagerly load relationships to avoid N+1 queries
        # Since we already joined MetaSeries, use contains_eager for the series
        # SQLAlchemy will optimize and not create duplicate joins for lookup tables already joined for filtering
        from sqlalchemy.orm import contains_eager, joinedload
        
        # Get the relationship attributes from MetaSeries
        asset_class_rel = getattr(MetaSeries, 'asset_class')
        sub_asset_class_rel = getattr(MetaSeries, 'sub_asset_class')
        product_type_rel = getattr(MetaSeries, 'product_type')
        data_type_rel = getattr(MetaSeries, 'data_type')
        structure_type_rel = getattr(MetaSeries, 'structure_type')
        market_segment_rel = getattr(MetaSeries, 'market_segment')
        field_type_rel = getattr(MetaSeries, 'field_type')
        
        # Use joinedload for all relationships - SQLAlchemy will optimize duplicate joins
        query = query.options(
            contains_eager(ValueData.series).joinedload(asset_class_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(sub_asset_class_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(product_type_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(data_type_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(structure_type_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(market_segment_rel),  # type: ignore[arg-type]
            contains_eager(ValueData.series).joinedload(field_type_rel),  # type: ignore[arg-type]
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())

    def _apply_value_data_filters(self, query: Select, filter_obj: ValueDataFilter) -> Select:
        """Apply filters to a ValueData query."""
        conditions = []
        
        if filter_obj.series_id is not None:
            conditions.append(ValueData.series_id == filter_obj.series_id)
        if filter_obj.series_id__in is not None:
            conditions.append(ValueData.series_id.in_(cast(list[int], filter_obj.series_id__in)))
        if filter_obj.timestamp__gte is not None:
            conditions.append(ValueData.timestamp >= filter_obj.timestamp__gte)
        if filter_obj.timestamp__lte is not None:
            conditions.append(ValueData.timestamp <= filter_obj.timestamp__lte)
        if filter_obj.is_latest is not None:
            conditions.append(ValueData.is_latest == filter_obj.is_latest)
        if filter_obj.value__gte is not None:
            conditions.append(ValueData.value >= filter_obj.value__gte)
        if filter_obj.value__lte is not None:
            conditions.append(ValueData.value <= filter_obj.value__lte)
        
        if conditions:
            query = query.where(and_(*conditions))  # type: ignore[arg-type]
        return query

    def _apply_ordering(self, query: Select, order_by: Optional[list[str]]) -> Select:
        """Apply ordering to a query."""
        if not order_by:
            return query
        
        from sqlalchemy import asc, desc
        for order_field in order_by:
            if order_field.startswith('-'):
                field_name = order_field[1:]
                query = query.order_by(desc(getattr(ValueData, field_name)))
            else:
                query = query.order_by(asc(getattr(ValueData, order_field)))
        return query

    async def get_derived(
        self,
        db: AsyncSession,
        *,
        filter_obj: ValueDataFilter,
    ) -> list[ValueData]:
        """Get derived value data (from series where is_derived=True)."""
        # Force is_derived=True for this method
        filter_obj.is_derived = True
        return await self.get_multi_with_filters(db=db, filter_obj=filter_obj)

    async def create_with_validation(
        self,
        db: AsyncSession,
        *,
        obj_in: ValueData,
    ) -> ValueData:
        """Create value data with series validation."""
        # Verify series exists
        series_query = select(MetaSeries).where(MetaSeries.series_id == obj_in.series_id)
        series_result = await db.execute(series_query)
        if not series_result.scalar_one_or_none():
            raise ValueError("Series not found")
        
        return await self.create(db, obj_in=obj_in)


# Create instance
crud_value_data = CRUDValueData(ValueData)
