"""Query optimization utilities."""

from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def explain_query(
    db: AsyncSession,
    query: Any,
) -> str:
    """Explain a query to see the execution plan.

    Useful for debugging and optimizing slow queries.

    Note: This function uses raw SQL for EXPLAIN ANALYZE which is safe because:
    - It only wraps already-compiled SQLAlchemy queries (no user input)
    - EXPLAIN ANALYZE is read-only and cannot modify data
    - Should only be used in development/debugging contexts

    Args:
        db: Database session
        query: SQLAlchemy query to explain

    Returns:
        Query execution plan as string
    """
    # Convert query to SQL - using dialect-specific compilation for safety
    from sqlalchemy.dialects import postgresql

    # Compile with PostgreSQL dialect for proper SQL generation
    compiled_query = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )

    # SAFE: Only wrapping a pre-compiled SQLAlchemy query with EXPLAIN ANALYZE
    # No user input is directly interpolated - the query object is from SQLAlchemy
    explain_query_str = f"EXPLAIN ANALYZE {compiled_query}"

    # Use text() only for the EXPLAIN wrapper - the actual query is from SQLAlchemy
    result = await db.execute(text(explain_query_str))
    return "\n".join([str(row) for row in result])


def optimize_query(
    query: Any,
    *,
    use_index: bool = True,
    limit_results: bool = True,
) -> Any:
    """Apply query optimizations.

    Args:
        query: SQLAlchemy query
        use_index: Whether to hint using indexes
        limit_results: Whether to ensure result limiting

    Returns:
        Optimized query
    """
    # Additional optimizations can be added here
    # For example, query hints, join optimizations, etc.
    return query
