"""
Database inspection and statistics script.

Provides insights into database contents and health.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text
from app.core.database import AsyncSessionLocal
from app.models import User, Issue, Label, Comment, IssueStatus, IssuePriority


async def get_database_stats():
    """Get comprehensive database statistics."""
    print("=" * 60)
    print("Database Statistics")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Count records in each table
        user_count = await session.scalar(select(func.count()).select_from(User))
        issue_count = await session.scalar(select(func.count()).select_from(Issue))
        label_count = await session.scalar(select(func.count()).select_from(Label))
        comment_count = await session.scalar(select(func.count()).select_from(Comment))
        
        print("\n📊 Record Counts:")
        print(f"  Users:    {user_count}")
        print(f"  Issues:   {issue_count}")
        print(f"  Labels:   {label_count}")
        print(f"  Comments: {comment_count}")
        
        # Issue statistics by status
        print("\n📋 Issues by Status:")
        for status in IssueStatus:
            count = await session.scalar(
                select(func.count()).select_from(Issue).where(Issue.status == status)
            )
            print(f"  {status.value.ljust(12)}: {count}")
        
        # Issue statistics by priority
        print("\n🔥 Issues by Priority:")
        for priority in IssuePriority:
            count = await session.scalar(
                select(func.count()).select_from(Issue).where(Issue.priority == priority)
            )
            print(f"  {priority.value.ljust(12)}: {count}")
        
        # Top assignees
        print("\n👥 Top Assignees:")
        result = await session.execute(
            select(User.username, func.count(Issue.id).label('count'))
            .join(Issue, Issue.assignee_id == User.id)
            .group_by(User.id, User.username)
            .order_by(func.count(Issue.id).desc())
            .limit(5)
        )
        for row in result:
            print(f"  {row.username.ljust(15)}: {row.count} issues")
        
        # Most used labels
        print("\n🏷️  Most Used Labels:")
        result = await session.execute(
            text("""
                SELECT l.name, COUNT(il.issue_id) as usage_count
                FROM labels l
                LEFT JOIN issue_labels il ON l.id = il.label_id
                GROUP BY l.id, l.name
                ORDER BY usage_count DESC
                LIMIT 5
            """)
        )
        for row in result:
            print(f"  {row.name.ljust(15)}: {row.usage_count} issues")
        
        # Recent activity
        print("\n📅 Recent Activity:")
        recent_issues = await session.execute(
            select(Issue.title, Issue.created_at, Issue.status)
            .order_by(Issue.created_at.desc())
            .limit(5)
        )
        for issue in recent_issues:
            print(f"  [{issue.status.value}] {issue.title[:40]}")
            print(f"    Created: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


async def check_database_health():
    """Check database health and integrity."""
    print("\n" + "=" * 60)
    print("Database Health Check")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        issues = []
        
        # Check for orphaned issues (assignee doesn't exist)
        orphaned_issues = await session.scalar(
            select(func.count())
            .select_from(Issue)
            .outerjoin(User, Issue.assignee_id == User.id)
            .where(Issue.assignee_id.isnot(None))
            .where(User.id.is_(None))
        )
        
        if orphaned_issues > 0:
            issues.append(f"⚠️  Found {orphaned_issues} issues with invalid assignee_id")
        else:
            print("\n✓ All issues have valid assignees")
        
        # Check for orphaned comments
        orphaned_comments = await session.scalar(
            select(func.count())
            .select_from(Comment)
            .outerjoin(Issue, Comment.issue_id == Issue.id)
            .where(Comment.issue_id.isnot(None))
            .where(Issue.id.is_(None))
        )
        
        if orphaned_comments > 0:
            issues.append(f"⚠️  Found {orphaned_comments} comments with invalid issue_id")
        else:
            print("✓ All comments are linked to valid issues")
        
        # Check for issues without timestamps
        issues_without_timestamps = await session.scalar(
            select(func.count())
            .select_from(Issue)
            .where(
                (Issue.created_at.is_(None)) | (Issue.updated_at.is_(None))
            )
        )
        
        if issues_without_timestamps > 0:
            issues.append(f"⚠️  Found {issues_without_timestamps} issues with missing timestamps")
        else:
            print("✓ All issues have proper timestamps")
        
        # Summary
        if issues:
            print("\n⚠️  Issues Found:")
            for issue in issues:
                print(f"  {issue}")
            print("\nRecommendation: Review and fix data integrity issues")
        else:
            print("\n✅ Database health check passed!")


async def list_all_users():
    """List all users in the database."""
    print("\n" + "=" * 60)
    print("All Users")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).order_by(User.id)
        )
        users = result.scalars().all()
        
        if not users:
            print("\nNo users found.")
            return
        
        for user in users:
            print(f"\nID: {user.id}")
            print(f"  Username:   {user.username}")
            print(f"  Email:      {user.email}")
            print(f"  Full Name:  {user.full_name}")
            print(f"  Created:    {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


async def list_all_labels():
    """List all labels in the database."""
    print("\n" + "=" * 60)
    print("All Labels")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Label).order_by(Label.name)
        )
        labels = result.scalars().all()
        
        if not labels:
            print("\nNo labels found.")
            return
        
        for label in labels:
            # Get usage count
            usage_count = await session.scalar(
                text("SELECT COUNT(*) FROM issue_labels WHERE label_id = :label_id"),
                {"label_id": label.id}
            )
            
            print(f"\n{label.name} ({label.color})")
            print(f"  Description: {label.description or 'N/A'}")
            print(f"  Used in:     {usage_count} issues")


async def export_data_summary():
    """Export a summary of database data."""
    print("\n" + "=" * 60)
    print("Data Export Summary")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Get all issues with details
        result = await session.execute(
            select(Issue, User)
            .join(User, Issue.assignee_id == User.id, isouter=True)
            .order_by(Issue.created_at.desc())
        )
        
        print("\nIssues Summary:")
        print("-" * 60)
        
        for issue, assignee in result:
            print(f"\n#{issue.id} - {issue.title}")
            print(f"  Status:   {issue.status.value}")
            print(f"  Priority: {issue.priority.value}")
            print(f"  Assignee: {assignee.username if assignee else 'Unassigned'}")
            print(f"  Created:  {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get comment count
            comment_count = await session.scalar(
                select(func.count()).select_from(Comment).where(Comment.issue_id == issue.id)
            )
            print(f"  Comments: {comment_count}")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Database Inspection Utility")
        print("\nUsage:")
        print("  python3 scripts/inspect_db.py stats   - Show database statistics")
        print("  python3 scripts/inspect_db.py health  - Check database health")
        print("  python3 scripts/inspect_db.py users   - List all users")
        print("  python3 scripts/inspect_db.py labels  - List all labels")
        print("  python3 scripts/inspect_db.py export  - Export data summary")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            await get_database_stats()
        elif command == "health":
            await check_database_health()
        elif command == "users":
            await list_all_users()
        elif command == "labels":
            await list_all_labels()
        elif command == "export":
            await export_data_summary()
        else:
            print(f"✗ Unknown command: {command}")
            print("Valid commands: stats, health, users, labels, export")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
