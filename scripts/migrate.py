"""
Database migration script using Alembic.

This is a placeholder for future migrations.
For now, we use the init_db.py script for schema creation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config


def run_migrations():
    """Run database migrations."""
    print("Running database migrations...")

    # Create Alembic config
    alembic_cfg = Config("alembic.ini")

    # Run migrations
    try:
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration")
    print("=" * 60)
    print("\nNote: For initial setup, use scripts/init_db.py instead.")
    print("This script is for running Alembic migrations.\n")

    # For now, just inform the user
    print("Alembic migrations not yet configured.")
    print("Use 'alembic init alembic' to set up migrations.")
    print("=" * 60)
