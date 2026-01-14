"""
Database backup script.

Creates timestamped backups of the database.
"""
import asyncio
import sys
import shutil
from pathlib import Path
from datetime import datetime, UTC

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def backup_database():
    """Create a backup of the database."""
    print("=" * 60)
    print("Database Backup Utility")
    print("=" * 60)
    
    # Parse database URL to get the database file path
    db_url = settings.DATABASE_URL
    
    if "sqlite" in db_url:
        # Extract database file path from SQLite URL
        # Format: sqlite+aiosqlite:///./issue_tracker.db
        db_path = db_url.split("///")[-1]
        db_file = Path(db_path)
        
        if not db_file.exists():
            print(f"✗ Database file not found: {db_file}")
            return False
        
        # Create backups directory
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Create timestamped backup
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"issue_tracker_backup_{timestamp}.db"
        
        print(f"\nBacking up database...")
        print(f"Source: {db_file}")
        print(f"Destination: {backup_file}")
        
        try:
            shutil.copy2(db_file, backup_file)
            file_size = backup_file.stat().st_size / 1024  # KB
            print(f"\n✓ Backup created successfully!")
            print(f"  Size: {file_size:.2f} KB")
            print(f"  Location: {backup_file.absolute()}")
            
            # List all backups
            backups = sorted(backup_dir.glob("issue_tracker_backup_*.db"))
            print(f"\nTotal backups: {len(backups)}")
            
            if len(backups) > 5:
                print(f"\n⚠️  You have {len(backups)} backups. Consider cleaning up old backups.")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Backup failed: {e}")
            return False
    
    elif "postgresql" in db_url:
        print("\n⚠️  PostgreSQL backup requires pg_dump.")
        print("Run the following command manually:")
        print(f"\n  pg_dump {db_url} > backups/backup_$(date +%Y%m%d_%H%M%S).sql")
        return False
    
    else:
        print(f"\n✗ Unsupported database type: {db_url}")
        return False


async def restore_database():
    """Restore database from a backup."""
    print("=" * 60)
    print("Database Restore Utility")
    print("=" * 60)
    
    backup_dir = Path("backups")
    
    if not backup_dir.exists():
        print("\n✗ No backups directory found.")
        return False
    
    # List available backups
    backups = sorted(backup_dir.glob("issue_tracker_backup_*.db"), reverse=True)
    
    if not backups:
        print("\n✗ No backup files found.")
        return False
    
    print("\nAvailable backups:")
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / 1024  # KB
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"  {i}. {backup.name} ({size:.2f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Get user selection
    try:
        choice = input("\nSelect backup to restore (number) or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            print("Restore cancelled.")
            return False
        
        index = int(choice) - 1
        if index < 0 or index >= len(backups):
            print("✗ Invalid selection.")
            return False
        
        selected_backup = backups[index]
        
        # Confirm restoration
        confirm = input(f"\n⚠️  This will overwrite the current database. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Restore cancelled.")
            return False
        
        # Parse database URL
        db_url = settings.DATABASE_URL
        db_path = db_url.split("///")[-1]
        db_file = Path(db_path)
        
        # Create backup of current database before restoring
        if db_file.exists():
            current_backup = backup_dir / f"pre_restore_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_file, current_backup)
            print(f"\n✓ Current database backed up to: {current_backup.name}")
        
        # Restore the selected backup
        shutil.copy2(selected_backup, db_file)
        print(f"\n✓ Database restored from: {selected_backup.name}")
        print("\n⚠️  Please restart the application for changes to take effect.")
        
        return True
        
    except ValueError:
        print("✗ Invalid input.")
        return False
    except Exception as e:
        print(f"\n✗ Restore failed: {e}")
        return False


async def list_backups():
    """List all available backups."""
    backup_dir = Path("backups")
    
    if not backup_dir.exists():
        print("No backups directory found.")
        return
    
    backups = sorted(backup_dir.glob("issue_tracker_backup_*.db"), reverse=True)
    
    if not backups:
        print("No backup files found.")
        return
    
    print("\n" + "=" * 60)
    print("Available Database Backups")
    print("=" * 60)
    
    total_size = 0
    for backup in backups:
        size = backup.stat().st_size / 1024  # KB
        total_size += size
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"\n  {backup.name}")
        print(f"    Size: {size:.2f} KB")
        print(f"    Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n{'=' * 60}")
    print(f"Total backups: {len(backups)}")
    print(f"Total size: {total_size:.2f} KB")
    print("=" * 60)


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Database Maintenance Utility")
        print("\nUsage:")
        print("  python3 scripts/backup_db.py backup   - Create a new backup")
        print("  python3 scripts/backup_db.py restore  - Restore from a backup")
        print("  python3 scripts/backup_db.py list     - List all backups")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "backup":
            success = await backup_database()
            sys.exit(0 if success else 1)
        elif command == "restore":
            success = await restore_database()
            sys.exit(0 if success else 1)
        elif command == "list":
            await list_backups()
            sys.exit(0)
        else:
            print(f"✗ Unknown command: {command}")
            print("Valid commands: backup, restore, list")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
