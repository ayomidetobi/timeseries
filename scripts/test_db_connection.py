#!/usr/bin/env python3
"""Test database connection and verify it's working."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init, db_health_check, check_if_db_is_initialized
from app.core.config import settings


async def test_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    db_url = settings.database_url
    print(f"📊 Database URL: {db_url[:50]}...")  # Show first 50 chars
    
    # Check if URL needs to be converted from postgres:// to postgresql+asyncpg://
    if db_url and db_url.startswith("postgres://"):
        print("⚠️  Converting postgres:// to postgresql+asyncpg:// for async connection")
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Update settings temporarily
        from app.core.database import _db_connection_manager
        _db_connection_manager.database_url = db_url
    
    try:
        # Initialize database
        print("\n1️⃣ Initializing database connection...")
        init()
        
        if not check_if_db_is_initialized():
            print("❌ Database not initialized")
            return False
        
        print("✅ Database engine created")
        
        # Test health check
        print("\n2️⃣ Testing database health check...")
        await db_health_check(timeout=5.0)
        print("✅ Database connection successful!")
        
        # Test query
        print("\n3️⃣ Testing database query...")
        from sqlalchemy import text
        from app.core.database import get_session_context
        
        async with get_session_context() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL version: {version[:50]}...")
            
            # Check if TimescaleDB is available
            result = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')")
            )
            has_timescaledb = result.scalar()
            if has_timescaledb:
                print("✅ TimescaleDB extension is installed")
            else:
                print("⚠️  TimescaleDB extension is not installed (optional)")
            
            # Check if value_data table exists
            result = await session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'value_data'
                    )
                """)
            )
            has_value_data = result.scalar()
            if has_value_data:
                print("✅ value_data table exists")
            else:
                print("⚠️  value_data table does not exist (run migrations)")
        
        print("\n🎉 Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)

