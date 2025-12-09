"""Tests for ValueData API endpoints."""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import AssetClassFactory, MetaSeriesFactory, ValueDataFactory


@pytest.mark.asyncio
@pytest.mark.api
class TestValueDataEndpoints:
    """Test ValueData API endpoints."""
    
    async def test_create_value_data(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test POST /api/v1/value-data/"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Create value data
        value_data = ValueDataFactory.build(
            series_id=series.series_id,
            is_derived=False
        )
        
        response = await async_client.post(
            "/api/v1/value-data/",
            json=value_data.model_dump()
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["series_id"] == series.series_id
        assert float(data["value"]) == float(value_data.value)
        assert data["is_derived"] is False
    
    async def test_get_value_data_list(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test GET /api/v1/value-data/"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Create multiple value data records
        for i in range(5):
            value_data = ValueDataFactory.build(
                series_id=series.series_id,
                observation_date=date.today() - timedelta(days=i)
            )
            test_session.add(value_data)
        
        await test_session.commit()
        
        response = await async_client.get(
            f"/api/v1/value-data/?series_id={series.series_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
    
    async def test_get_value_data_by_date(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test GET /api/v1/value-data/{series_id}/{observation_date}"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Create value data
        value_data = ValueDataFactory.build(series_id=series.series_id)
        test_session.add(value_data)
        await test_session.commit()
        
        response = await async_client.get(
            f"/api/v1/value-data/{series.series_id}/{value_data.observation_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["series_id"] == series.series_id
        assert data["observation_date"] == str(value_data.observation_date)
    
    async def test_get_derived_value_data(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test GET /api/v1/value-data/derived/"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Create both raw and derived values
        for i in range(3):
            raw_value = ValueDataFactory.build(
                series_id=series.series_id,
                is_derived=False,
                observation_date=date.today() - timedelta(days=i)
            )
            test_session.add(raw_value)
        
        for i in range(2):
            derived_value = ValueDataFactory.build(
                series_id=series.series_id,
                is_derived=True,
                observation_date=date.today() - timedelta(days=i+3)
            )
            test_session.add(derived_value)
        
        await test_session.commit()
        
        response = await async_client.get(
            f"/api/v1/value-data/derived/?series_id={series.series_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(item["is_derived"] is True for item in data)
    
    async def test_filter_value_data_by_is_derived(self, async_client: AsyncClient, test_session: AsyncSession):
        """Test filtering value data by is_derived flag"""
        # Create dependencies
        asset_class = AssetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)
        
        series = MetaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)
        
        # Create both types
        for i in range(3):
            raw_value = ValueDataFactory.build(
                series_id=series.series_id,
                is_derived=False,
                observation_date=date.today() - timedelta(days=i)
            )
            test_session.add(raw_value)
        
        for i in range(2):
            derived_value = ValueDataFactory.build(
                series_id=series.series_id,
                is_derived=True,
                observation_date=date.today() - timedelta(days=i+3)
            )
            test_session.add(derived_value)
        
        await test_session.commit()
        
        # Get only raw values
        response = await async_client.get(
            f"/api/v1/value-data/?series_id={series.series_id}&is_derived=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all(item["is_derived"] is False for item in data)

