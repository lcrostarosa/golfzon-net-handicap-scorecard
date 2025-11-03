#!/usr/bin/env python
"""
Bootstrap script to initialize the database using Alembic migrations.
"""
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from database import get_engine
from models import Base


def bootstrap_database():
    """Initialize database with Alembic migrations."""
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Check if alembic.ini exists
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print("ERROR: alembic.ini not found. Please run 'alembic init alembic' first.")
        sys.exit(1)
    
    # Set up Alembic config
    alembic_cfg = Config(str(alembic_ini))
    
    # Check if versions directory exists and has migrations
    versions_dir = project_root / "alembic" / "versions"
    if not versions_dir.exists():
        versions_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if there are any migration files
    migration_files = list(versions_dir.glob("*.py"))
    
    if not migration_files:
        print("Creating initial migration...")
        # Create initial migration
        command.revision(
            alembic_cfg,
            autogenerate=True,
            message="Initial migration"
        )
        print("✓ Initial migration created")
    
    # Run migrations
    print("Running migrations...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations applied successfully")
    except Exception as e:
        print(f"ERROR: Failed to apply migrations: {e}")
        sys.exit(1)
    
    # Verify database exists and has tables
    engine = get_engine()
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = ['leagues', 'teams', 'players', 'weekly_scores', 'alembic_version']
    missing_tables = [t for t in expected_tables if t not in tables]
    
    if missing_tables:
        print(f"WARNING: Missing tables: {missing_tables}")
        sys.exit(1)
    
    print("✓ Database initialized successfully")
    print(f"✓ Tables created: {', '.join([t for t in tables if t != 'alembic_version'])}")


if __name__ == "__main__":
    bootstrap_database()

