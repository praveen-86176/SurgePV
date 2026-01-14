"""
Database initialization script.

Creates all tables and optionally seeds with sample data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal, Base, engine
from app.models import Comment, Issue, IssuePriority, IssueStatus, Label, User


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created successfully")


async def seed_data():
    """Seed database with sample data."""
    print("\nSeeding sample data...")

    async with AsyncSessionLocal() as session:
        # Create users
        users = [
            User(username="alice", email="alice@example.com", full_name="Alice Johnson"),
            User(username="bob", email="bob@example.com", full_name="Bob Smith"),
            User(username="charlie", email="charlie@example.com", full_name="Charlie Brown"),
            User(username="diana", email="diana@example.com", full_name="Diana Prince"),
        ]
        session.add_all(users)
        await session.flush()
        print(f"✓ Created {len(users)} users")

        # Create labels
        labels = [
            Label(name="bug", color="#d73a4a", description="Something isn't working"),
            Label(name="enhancement", color="#a2eeef", description="New feature or request"),
            Label(
                name="documentation",
                color="#0075ca",
                description="Improvements or additions to documentation",
            ),
            Label(name="urgent", color="#ff0000", description="Requires immediate attention"),
            Label(name="backend", color="#fbca04", description="Backend related"),
            Label(name="frontend", color="#7057ff", description="Frontend related"),
        ]
        session.add_all(labels)
        await session.flush()
        print(f"✓ Created {len(labels)} labels")

        # Create issues
        from datetime import UTC, datetime

        # Helper for naive UTC
        def utc_now():
            return datetime.now(UTC).replace(tzinfo=None)

        issues = [
            Issue(
                title="Login page not responding",
                description="Users report that the login page freezes when submitting credentials",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                assignee_id=users[0].id,
                created_at=utc_now(),
            ),
            Issue(
                title="Add dark mode support",
                description="Implement dark mode theme across the application",
                status=IssueStatus.IN_PROGRESS,
                priority=IssuePriority.MEDIUM,
                assignee_id=users[1].id,
                created_at=utc_now(),
            ),
            Issue(
                title="Update API documentation",
                description="API docs are outdated and missing new endpoints",
                status=IssueStatus.OPEN,
                priority=IssuePriority.LOW,
                assignee_id=users[2].id,
                created_at=utc_now(),
            ),
            Issue(
                title="Database connection timeout",
                description="Production database experiencing frequent timeouts",
                status=IssueStatus.RESOLVED,
                priority=IssuePriority.CRITICAL,
                assignee_id=users[0].id,
                created_at=utc_now(),
            ),
            Issue(
                title="Improve search performance",
                description="Search queries taking too long on large datasets",
                status=IssueStatus.IN_PROGRESS,
                priority=IssuePriority.HIGH,
                assignee_id=users[1].id,
                created_at=utc_now(),
            ),
        ]
        session.add_all(issues)
        await session.flush()
        print(f"✓ Created {len(issues)} issues")

        # Assign labels to issues using direct inserts to avoid lazy loading
        from app.models import issue_labels

        label_assignments = [
            # Issue 0: bug, urgent, frontend
            {"issue_id": issues[0].id, "label_id": labels[0].id, "created_at": utc_now()},
            {"issue_id": issues[0].id, "label_id": labels[3].id, "created_at": utc_now()},
            {"issue_id": issues[0].id, "label_id": labels[5].id, "created_at": utc_now()},
            # Issue 1: enhancement, frontend
            {"issue_id": issues[1].id, "label_id": labels[1].id, "created_at": utc_now()},
            {"issue_id": issues[1].id, "label_id": labels[5].id, "created_at": utc_now()},
            # Issue 2: documentation
            {"issue_id": issues[2].id, "label_id": labels[2].id, "created_at": utc_now()},
            # Issue 3: bug, urgent, backend
            {"issue_id": issues[3].id, "label_id": labels[0].id, "created_at": utc_now()},
            {"issue_id": issues[3].id, "label_id": labels[3].id, "created_at": utc_now()},
            {"issue_id": issues[3].id, "label_id": labels[4].id, "created_at": utc_now()},
            # Issue 4: enhancement, backend
            {"issue_id": issues[4].id, "label_id": labels[1].id, "created_at": utc_now()},
            {"issue_id": issues[4].id, "label_id": labels[4].id, "created_at": utc_now()},
        ]

        for assignment in label_assignments:
            await session.execute(issue_labels.insert().values(**assignment))

        print("✓ Assigned labels to issues")

        # Create comments
        comments = [
            Comment(
                issue_id=issues[0].id,
                author_id=users[1].id,
                body="Fixed in latest commit.",
                created_at=utc_now(),
            ),
            Comment(
                issue_id=issues[0].id,
                author_id=users[1].id,
                body="I can reproduce this issue. It happens when the password field is empty.",
                created_at=utc_now(),
            ),
            Comment(
                issue_id=issues[0].id,
                author_id=users[0].id,
                body="Thanks for confirming. I'll investigate the validation logic.",
                created_at=utc_now(),
            ),
            Comment(
                issue_id=issues[1].id,
                author_id=users[1].id,
                body="Started working on this. Planning to use CSS variables for theming.",
            ),
            Comment(
                issue_id=issues[3].id,
                author_id=users[0].id,
                body="Fixed by increasing connection pool size and timeout settings.",
            ),
        ]
        session.add_all(comments)
        await session.flush()
        print(f"✓ Created {len(comments)} comments")

        await session.commit()
        print("\n✓ Sample data seeded successfully")


async def main():
    """Main initialization function."""
    print("=" * 60)
    print("Issue Tracker Database Initialization")
    print("=" * 60)

    try:
        await create_tables()

        # Ask if user wants to seed data
        seed = input("\nDo you want to seed sample data? (y/n): ").lower().strip()
        if seed == "y":
            await seed_data()

        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
