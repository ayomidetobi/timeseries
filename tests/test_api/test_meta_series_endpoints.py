"""Tests for MetaSeries API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import AssetClassFactory, ProductTypeFactory, MetaSeriesFactory


@pytest.mark.asyncio
@pytest.mark.api
class TestMetaSeriesEndpoints:
    """Test MetaSeries API endpoints."""
    
    async def test_create_meta_series(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test POST /api/v1/meta-series/"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        product_type = ProductTypeFactory()
        test_session.add(product_type)
        await test_session.commit()
        await test_session.refresh(product_type)
        
        # Create series data
        series_data = MetaSeriesFactory.build(
            asset_class_id=asset_class.asset_class_id,
            product_type_id=product_type.product_type_id
        )
        
        response = await async_client.post(
            "/api/v1/meta-series/",
            json=series_data.model_dump(exclude={"series_id"})
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["series_name"] == series_data.series_name
        assert data["asset_class_id"] == asset_class.asset_class_id
        assert "series_id" in data
    
    async def test_get_meta_series_list(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test GET /api/v1/meta-series/"""
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
        
        response = await async_client.get("/api/v1/meta-series/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
    
    async def test_get_meta_series_by_id(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test GET /api/v1/meta-series/{series_id}"""
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
        
        response = await async_client.get(f"/api/v1/meta-series/{series.series_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["series_id"] == series.series_id
        assert data["series_name"] == series.series_name
    
    async def test_get_meta_series_not_found(self, async_client: AsyncClient):
        """Test GET /api/v1/meta-series/{series_id} with non-existent ID"""
        response = await async_client.get("/api/v1/meta-series/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_update_meta_series(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test PUT /api/v1/meta-series/{series_id}"""
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
        
        # Update data
        update_data = {
            "series_name": "Updated Series Name",
            "is_active": False
        }
        
        response = await async_client.put(
            f"/api/v1/meta-series/{series.series_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["series_name"] == "Updated Series Name"
        assert data["is_active"] is False
    
    async def test_delete_meta_series(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test DELETE /api/v1/meta-series/{series_id}"""
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
        
        response = await async_client.delete(f"/api/v1/meta-series/{series.series_id}")
        
        assert response.status_code == 204
        
        # Verify soft delete
        get_response = await async_client.get(f"/api/v1/meta-series/{series.series_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["is_active"] is False

