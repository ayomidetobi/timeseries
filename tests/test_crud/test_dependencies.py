"""Tests for Dependency and Calculation CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.dependencies import crud_dependency, crud_calculation
from tests.factories import (
    assetClassFactory,
    metaSeriesFactory,
    dependencyFactory,
    calculationLogFactory,
)


@pytest.mark.asyncio
@pytest.mark.crud
class TestDependencyCRUD:
    """Test SeriesDependencyGraph CRUD operations."""

    async def test_create_dependency(self, test_session: AsyncSession):
        """Test creating a dependency."""
        # Create parent and child series
        asset_class = assetClassFactory.build()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        parent = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(parent)
        await test_session.commit()
        await test_session.refresh(parent)

        child = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(child)
        await test_session.commit()
        await test_session.refresh(child)

        # Create dependency
        dependency = dependencyFactory.build(
            parent_series_id=parent.series_id, child_series_id=child.series_id
        )

        created = await crud_dependency.create(db=test_session, obj_in=dependency)

        assert created.dependency_id is not None
        assert created.parent_series_id == parent.series_id
        assert created.child_series_id == child.series_id

    async def test_get_dependencies_by_parent(self, test_session: AsyncSession):
        """Test getting dependencies by parent series."""
        # Create series
        asset_class = assetClassFactory.build()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        parent = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(parent)
        await test_session.commit()
        await test_session.refresh(parent)

        # Create multiple dependencies
        for _ in range(3):
            child = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
            test_session.add(child)
            await test_session.commit()
            await test_session.refresh(child)

            dependency = dependencyFactory.build(
                parent_series_id=parent.series_id, child_series_id=child.series_id
            )
            test_session.add(dependency)

        await test_session.commit()

        # Get dependencies
        from app.schemas.filters import DependencyFilter

        filter_obj = DependencyFilter(parent_series_id=parent.series_id)
        dependencies = await crud_dependency.get_multi_with_filters(
            db=test_session, filter_obj=filter_obj
        )

        assert len(dependencies) >= 3


@pytest.mark.asyncio
@pytest.mark.crud
class TestCalculationLogCRUD:
    """Test CalculationLog CRUD operations."""

    async def test_create_calculation_log(self, test_session: AsyncSession):
        """Test creating a calculation log."""
        # Create series
        asset_class = assetClassFactory.build()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create calculation log
        calculation = calculationLogFactory.build(derived_series_id=series.series_id)

        created = await crud_calculation.create(db=test_session, obj_in=calculation)

        assert created.calculation_id is not None
        assert created.derived_series_id == series.series_id
        assert created.calculation_method is not None

    async def test_get_calculations_by_series(self, test_session: AsyncSession):
        """Test getting calculations by series."""
        # Create series
        asset_class = assetClassFactory.build()
        test_session.add(asset_class)
        await test_session.commit()
        await test_session.refresh(asset_class)

        series = metaSeriesFactory.build(asset_class_id=asset_class.asset_class_id)
        test_session.add(series)
        await test_session.commit()
        await test_session.refresh(series)

        # Create multiple calculations
        for _ in range(5):
            calculation = calculationLogFactory.build(
                derived_series_id=series.series_id
            )
            test_session.add(calculation)

        await test_session.commit()

        # Get calculations
        from app.schemas.filters import CalculationFilter

        filter_obj = CalculationFilter(derived_series_id=series.series_id)
        calculations = await crud_calculation.get_multi_with_filters(
            db=test_session, filter_obj=filter_obj
        )

        assert len(calculations) >= 5
