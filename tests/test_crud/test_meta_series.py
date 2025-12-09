"""Tests for MetaSeries CRUD operations."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meta_series import MetaSeries
from app.crud.meta_series import crud_meta_series
from tests.factories import AssetClassFactory, ProductTypeFactory, MetaSeriesFactory


@pytest.mark.asyncio
@pytest.mark.crud
class TestMetaSeriesCRUD:
    """Test MetaSeries CRUD operations."""
    
    async def test_create_meta_series(self, test_session: AsyncSession):
        """Test creating a meta series."""
        # Create dependencies first
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        product_type = ProductTypeFactory()
        test_session.add(product_type)
        await test_session.commit()
        await test_session.refresh(product_type)
        
        # Create meta series
        series_data = MetaSeriesFactory.build(
            asset_class_id=asset_class.asset_class_id,
            product_type_id=product_type.product_type_id
        )
        
        created_series = await crud_meta_series.create(
            db=test_session,
            obj_in=series_data
        )
        
        assert created_series.series_id is not None
        assert created_series.series_name == series_data.series_name
        assert created_series.asset_class_id == asset_class.asset_class_id
        assert created_series.product_type_id == product_type.product_type_id
    
    async def test_get_meta_series_by_id(self, test_session: AsyncSession):
        """Test getting a meta series by ID."""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        # Create and save series
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Retrieve it
        retrieved = await crud_meta_series.get_by_id(
            db=test_session,
            series_id=series.series_id
        )
        
        assert retrieved is not None
        assert retrieved.series_id == series.series_id
        assert retrieved.series_name == series.series_name
    
    async def test_get_multi_meta_series(self, test_session: AsyncSession):
        """Test getting multiple meta series."""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        # Create multiple series
        for _ in range(5):
            series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
            test_session.add(series)
        
        await test_session.commit()
        
        # Retrieve all
        all_series = await crud_meta_series.get_multi(
            db=test_session,
            skip=0,
            limit=100
        )
        
        assert len(all_series) >= 5
    
    async def test_update_meta_series(self, test_session: AsyncSession):
        """Test updating a meta series."""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        # Create series
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Update it
        update_data = {"series_name": "Updated Name", "is_active": False}
        updated = await crud_meta_series.update(
            db=test_session,
            db_obj=series,
            obj_in=update_data
        )
        
        assert updated.series_name == "Updated Name"
        assert updated.is_active is False
    
    async def test_soft_delete_meta_series(self, test_session: AsyncSession):
        """Test soft deleting a meta series."""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        # Create series
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id, is_active=True)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Soft delete
        deleted = await crud_meta_series.soft_delete(
            db=test_session,
            series_id=series.series_id
        )
        
        assert deleted is not None
        assert deleted.is_active is False
        
        # Verify it's still in database but inactive
        retrieved = await crud_meta_series.get_by_id(
            db=test_session,
            series_id=series.series_id
        )
        assert retrieved.is_active is False

