"""
Database cleanup and maintenance script.

Performs various cleanup operations on the database.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, func
from app.core.database import AsyncSessionLocal
from app.models import User, Issue, Label, Comment, IssueStatus


async def clean_old_resolved_issues(days=90):
    """Archive or clean up old resolved issues."""
    print("=" * 60)
    print(f"Cleaning Resolved Issues Older Than {days} Days")
    print("=" * 60)
    
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    
    async with AsyncSessionLocal() as session:
        # Find old resolved issues
        result = await session.execute(
            select(Issue)
            .where(Issue.status == IssueStatus.RESOLVED)
            .where(Issue.updated_at < cutoff_date)
        )
        old_issues = result.scalars().all()
        
        if not old_issues:
            print(f"\n✓ No resolved issues older than {days} days found.")
            return
        
        print(f"\nFound {len(old_issues)} old resolved issues:")
        for issue in old_issues[:5]:  # Show first 5
            print(f"  #{issue.id} - {issue.title[:50]}")
            print(f"    Resolved: {issue.updated_at.strftime('%Y-%m-%d')}")
        
        if len(old_issues) > 5:
            print(f"  ... and {len(old_issues) - 5} more")
        
        confirm = input(f"\n⚠️  Delete these {len(old_issues)} issues? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("Cleanup cancelled.")
            return
        
        # Delete associated comments first
        for issue in old_issues:
            await session.execute(
                delete(Comment).where(Comment.issue_id == issue.id)
            )
        
        # Delete issues
        for issue in old_issues:
            await session.delete(issue)
        
        await session.commit()
        print(f"\n✓ Deleted {len(old_issues)} old resolved issues and their comments.")


async def remove_unused_labels():
    """Remove labels that are not assigned to any issues."""
    print("\n" + "=" * 60)
    print("Removing Unused Labels")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Find labels with no issues
        from sqlalchemy import text
        result = await session.execute(
            text("""
                SELECT l.id, l.name
                FROM labels l
                LEFT JOIN issue_labels il ON l.id = il.label_id
                GROUP BY l.id, l.name
                HAVING COUNT(il.issue_id) = 0
            """)
        )
        unused_labels = result.all()
        
        if not unused_labels:
            print("\n✓ No unused labels found.")
            return
        
        print(f"\nFound {len(unused_labels)} unused labels:")
        for label in unused_labels:
            print(f"  - {label.name}")
        
        confirm = input(f"\n⚠️  Delete these {len(unused_labels)} labels? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("Cleanup cancelled.")
            return
        
        # Delete unused labels
        for label in unused_labels:
            await session.execute(
                delete(Label).where(Label.id == label.id)
            )
        
        await session.commit()
        print(f"\n✓ Deleted {len(unused_labels)} unused labels.")


async def vacuum_database():
    """Optimize database (SQLite only)."""
    print("\n" + "=" * 60)
    print("Database Optimization")
    print("=" * 60)
    
    from app.core.config import settings
    
    if "sqlite" not in settings.DATABASE_URL:
        print("\n⚠️  Database optimization is only available for SQLite.")
        print("For PostgreSQL, run: VACUUM ANALYZE;")
        return
    
    async with AsyncSessionLocal() as session:
        print("\nOptimizing database...")
        
        # Get database size before
        db_path = settings.DATABASE_URL.split("///")[-1]
        db_file = Path(db_path)
        size_before = db_file.stat().st_size / 1024  # KB
        
        # Run VACUUM
        await session.execute(text("VACUUM"))
        await session.commit()
        
        # Get database size after
        size_after = db_file.stat().st_size / 1024  # KB
        saved = size_before - size_after
        
        print(f"\n✓ Database optimized!")
        print(f"  Size before: {size_before:.2f} KB")
        print(f"  Size after:  {size_after:.2f} KB")
        print(f"  Space saved: {saved:.2f} KB ({(saved/size_before*100):.1f}%)")


async def reset_database():
    """Reset database to initial state (WARNING: Deletes all data)."""
    print("\n" + "=" * 60)
    print("⚠️  DATABASE RESET WARNING ⚠️")
    print("=" * 60)
    print("\nThis will DELETE ALL DATA in the database!")
    print("This action CANNOT be undone.")
    
    confirm1 = input("\nType 'DELETE ALL DATA' to continue: ").strip()
    
    if confirm1 != "DELETE ALL DATA":
        print("\nReset cancelled.")
        return
    
    confirm2 = input("\nAre you absolutely sure? (yes/no): ").strip().lower()
    
    if confirm2 != "yes":
        print("\nReset cancelled.")
        return
    
    print("\nResetting database...")
    
    # Run init_db.py to recreate tables
    import subprocess
    result = subprocess.run(
        ["python3", "scripts/init_db.py"],
        cwd=Path(__file__).parent.parent,
        input="y\n",
        text=True,
        capture_output=True
    )
    
    if result.returncode == 0:
        print("\n✓ Database reset complete!")
        print("Sample data has been seeded.")
    else:
        print(f"\n✗ Reset failed: {result.stderr}")


async def show_maintenance_summary():
    """Show database maintenance recommendations."""
    print("=" * 60)
    print("Database Maintenance Summary")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Count records
        issue_count = await session.scalar(select(func.count()).select_from(Issue))
        comment_count = await session.scalar(select(func.count()).select_from(Comment))
        label_count = await session.scalar(select(func.count()).select_from(Label))
        
        # Count old resolved issues
        cutoff_date = datetime.now(UTC) - timedelta(days=90)
        old_resolved = await session.scalar(
            select(func.count())
            .select_from(Issue)
            .where(Issue.status == IssueStatus.RESOLVED)
            .where(Issue.updated_at < cutoff_date)
        )
        
        # Count unused labels
        from sqlalchemy import text
        result = await session.execute(
            text("""
                SELECT COUNT(*)
                FROM labels l
                LEFT JOIN issue_labels il ON l.id = il.label_id
                GROUP BY l.id
                HAVING COUNT(il.issue_id) = 0
            """)
        )
        unused_labels = len(result.all())
        
        print("\n📊 Current Status:")
        print(f"  Total Issues:   {issue_count}")
        print(f"  Total Comments: {comment_count}")
        print(f"  Total Labels:   {label_count}")
        
        print("\n🧹 Maintenance Recommendations:")
        
        if old_resolved > 0:
            print(f"  ⚠️  {old_resolved} resolved issues older than 90 days")
            print("     Consider archiving or deleting them")
        else:
            print("  ✓ No old resolved issues to clean up")
        
        if unused_labels > 0:
            print(f"  ⚠️  {unused_labels} unused labels")
            print("     Consider removing them")
        else:
            print("  ✓ No unused labels")
        
        # Database size
        from app.core.config import settings
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.split("///")[-1]
            db_file = Path(db_path)
            if db_file.exists():
                size = db_file.stat().st_size / 1024  # KB
                print(f"\n💾 Database Size: {size:.2f} KB")
                
                if size > 10240:  # > 10 MB
                    print("     Consider running vacuum to optimize")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Database Cleanup and Maintenance Utility")
        print("\nUsage:")
        print("  python3 scripts/cleanup_db.py summary        - Show maintenance summary")
        print("  python3 scripts/cleanup_db.py old-issues     - Clean old resolved issues")
        print("  python3 scripts/cleanup_db.py unused-labels  - Remove unused labels")
        print("  python3 scripts/cleanup_db.py vacuum         - Optimize database (SQLite)")
        print("  python3 scripts/cleanup_db.py reset          - Reset database (⚠️  DANGER)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "summary":
            await show_maintenance_summary()
        elif command == "old-issues":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            await clean_old_resolved_issues(days)
        elif command == "unused-labels":
            await remove_unused_labels()
        elif command == "vacuum":
            await vacuum_database()
        elif command == "reset":
            await reset_database()
        else:
            print(f"✗ Unknown command: {command}")
            print("Valid commands: summary, old-issues, unused-labels, vacuum, reset")
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
