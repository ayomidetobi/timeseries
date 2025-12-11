"""Tests for ValueData CRUD operations."""

import pytest
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.value_data import crud_value_data
from tests.factories import assetClassFactory, metaSeriesFactory, valueDataFactory


@pytest.mark.asyncio
@pytest.mark.crud
class TestValueDataCRUD:
    """Test ValueData CRUD operations."""

    async def test_create_value_data(self, test_session: AsyncSession):
        """Test creating value data."""
        # Create dependencies
        asset_class = assetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create value data
        value_data = valueDataFactory.build(
            series_id=series.series_id, is_derived=False
        )

        created = await crud_value_data.create_with_validation(
            db=test_session, obj_in=value_data
        )

        assert created.series_id == series.series_id
        assert created.value is not None
        assert created.is_derived is False

    async def test_create_derived_value_data(self, test_session: AsyncSession):
        """Test creating derived value data."""
        # Create dependencies
        asset_class = assetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create derived value data
        value_data = valueDataFactory.build(
            series_id=series.series_id, is_derived=True, calculation_method="SUM"
        )

        created = await crud_value_data.create_with_validation(
            db=test_session, obj_in=value_data
        )

        assert created.is_derived is True
        assert created.calculation_method == "SUM"

    async def test_get_value_data_by_id(self, test_session: AsyncSession):
        """Test getting value data by series_id and observation_date."""
        # Create dependencies
        asset_class = assetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create value data
        value_data = valueDataFactory.build(series_id=series.series_id)
        test_session.add(value_data)
        await test_session.commit()

        # Retrieve it
        retrieved = await crud_value_data.get_by_id(
            db=test_session,
            series_id=series.series_id,
            observation_date=value_data.observation_date,
        )

        assert retrieved is not None
        assert retrieved.series_id == series.series_id
        assert retrieved.observation_date == value_data.observation_date

    async def test_get_multi_value_data(self, test_session: AsyncSession):
        """Test getting multiple value data records."""
        # Create dependencies
        asset_class = assetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create multiple value data records
        for i in range(10):
            value_data = valueDataFactory.build(
                series_id=series.series_id,
                observation_date=date.today() - timedelta(days=i),
            )
            test_session.add(value_data)

        await test_session.commit()

        # Retrieve all
        all_values = await crud_value_data.get_multi(db=test_session, skip=0, limit=100)

        assert len(all_values) >= 10

    async def test_get_derived_value_data(self, test_session: AsyncSession):
        """Test getting derived value data."""
        # Create dependencies
        asset_class = assetClassFactory()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create both raw and derived values
        for i in range(5):
            raw_value = valueDataFactory.build(
                series_id=series.series_id,
                is_derived=False,
                observation_date=date.today() - timedelta(days=i),
            )
            test_session.add(raw_value)

        for i in range(3):
            derived_value = valueDataFactory.build(
                series_id=series.series_id,
                is_derived=True,
                observation_date=date.today() - timedelta(days=i + 5),
            )
            test_session.add(derived_value)

        await test_session.commit()

        # Get only derived values
        from app.schemas.filters import ValueDataFilter

        filter_obj = ValueDataFilter(series_id=series.series_id)
        derived_values = await crud_value_data.get_derived(
            db=test_session, filter_obj=filter_obj
        )

        assert len(derived_values) >= 3
        assert all(v.is_derived is True for v in derived_values)

    async def test_create_value_data_invalid_series(self, test_session: AsyncSession):
        """Test creating value data with invalid series_id raises error."""
        value_data = valueDataFactory.build(series_id=99999)

        with pytest.raises(ValueError, match="Series not found"):
            await crud_value_data.create_with_validation(
                db=test_session, obj_in=value_data
            )
