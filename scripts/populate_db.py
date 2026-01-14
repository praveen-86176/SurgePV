"""
Populate database with comprehensive, realistic data.

This script adds additional users, issues, labels, and comments
to make the database more useful for testing and demonstration.
"""

import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models import Comment, Issue, IssuePriority, IssueStatus, Label, User


async def add_more_users():
    """Add additional users to the database."""
    print("Adding more users...")

    async with AsyncSessionLocal() as session:
        new_users = [
            User(username="emma", email="emma@example.com", full_name="Emma Wilson"),
            User(username="frank", email="frank@example.com", full_name="Frank Miller"),
            User(username="grace", email="grace@example.com", full_name="Grace Lee"),
            User(username="henry", email="henry@example.com", full_name="Henry Taylor"),
        ]

        session.add_all(new_users)
        await session.flush()
        await session.commit()

        print(f"✓ Added {len(new_users)} new users")
        return new_users


async def add_more_labels():
    """Add additional labels to the database."""
    print("Adding more labels...")

    async with AsyncSessionLocal() as session:
        new_labels = [
            Label(name="security", color="#e11d48", description="Security-related issues"),
            Label(name="performance", color="#f59e0b", description="Performance optimization"),
            Label(name="ui/ux", color="#8b5cf6", description="User interface and experience"),
            Label(name="database", color="#06b6d4", description="Database-related issues"),
            Label(name="api", color="#10b981", description="API endpoints"),
            Label(name="testing", color="#6366f1", description="Testing and QA"),
            Label(name="deployment", color="#ec4899", description="Deployment and DevOps"),
            Label(name="refactoring", color="#f97316", description="Code refactoring"),
        ]

        session.add_all(new_labels)
        await session.flush()
        await session.commit()

        print(f"✓ Added {len(new_labels)} new labels")
        return new_labels


async def add_realistic_issues():
    """Add realistic issues with varied statuses and priorities."""
    print("Adding realistic issues...")

    async with AsyncSessionLocal() as session:
        # Get all users for assignment
        from sqlalchemy import select

        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            print("⚠️  No users found. Please run init_db.py first.")
            return []

        # Create varied issues
        base_time = datetime.now(UTC)

        issues_data = [
            {
                "title": "Implement user authentication system",
                "description": "Add JWT-based authentication with refresh tokens. Include login, logout, and token refresh endpoints.",
                "status": IssueStatus.IN_PROGRESS,
                "priority": IssuePriority.HIGH,
                "days_ago": 5,
            },
            {
                "title": "Fix memory leak in background worker",
                "description": "Background task is consuming increasing amounts of memory over time. Need to investigate and fix.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.CRITICAL,
                "days_ago": 2,
            },
            {
                "title": "Add pagination to issues list endpoint",
                "description": "Current endpoint returns all issues. Need to add pagination with configurable page size.",
                "status": IssueStatus.RESOLVED,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 10,
            },
            {
                "title": "Improve error messages for validation failures",
                "description": "Current error messages are too generic. Users need more specific information about what went wrong.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.LOW,
                "days_ago": 1,
            },
            {
                "title": "Add rate limiting to API endpoints",
                "description": "Implement rate limiting to prevent abuse. Use Redis for distributed rate limiting.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.HIGH,
                "days_ago": 3,
            },
            {
                "title": "Optimize database queries for reports",
                "description": "Report generation is slow. Need to add proper indexes and optimize queries.",
                "status": IssueStatus.IN_PROGRESS,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 7,
            },
            {
                "title": "Add email notifications for issue updates",
                "description": "Users should receive email notifications when issues they're assigned to are updated.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 4,
            },
            {
                "title": "Fix CORS configuration for production",
                "description": "CORS is blocking requests from production frontend. Need to update configuration.",
                "status": IssueStatus.RESOLVED,
                "priority": IssuePriority.CRITICAL,
                "days_ago": 8,
            },
            {
                "title": "Add file attachment support to issues",
                "description": "Users should be able to attach files (images, logs) to issues. Max 10MB per file.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.LOW,
                "days_ago": 6,
            },
            {
                "title": "Implement issue search functionality",
                "description": "Add full-text search across issue titles and descriptions. Consider using PostgreSQL FTS.",
                "status": IssueStatus.IN_PROGRESS,
                "priority": IssuePriority.HIGH,
                "days_ago": 9,
            },
            {
                "title": "Add API versioning",
                "description": "Implement API versioning strategy (v1, v2) to support backward compatibility.",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 12,
            },
            {
                "title": "Fix timezone handling in timestamps",
                "description": "Timestamps are not being stored in UTC consistently. Need to standardize.",
                "status": IssueStatus.RESOLVED,
                "priority": IssuePriority.HIGH,
                "days_ago": 15,
            },
            {
                "title": "Add health check endpoint",
                "description": "Implement /health endpoint for monitoring and load balancer health checks.",
                "status": IssueStatus.RESOLVED,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 20,
            },
            {
                "title": "Implement issue templates",
                "description": "Add predefined templates for common issue types (bug report, feature request, etc.)",
                "status": IssueStatus.OPEN,
                "priority": IssuePriority.LOW,
                "days_ago": 5,
            },
            {
                "title": "Add metrics and monitoring",
                "description": "Integrate Prometheus metrics for API performance monitoring.",
                "status": IssueStatus.IN_PROGRESS,
                "priority": IssuePriority.MEDIUM,
                "days_ago": 11,
            },
        ]

        issues = []
        for i, issue_data in enumerate(issues_data):
            created_at = base_time - timedelta(days=issue_data["days_ago"])
            updated_at = created_at + timedelta(hours=random.randint(1, 48))

            issue = Issue(
                title=issue_data["title"],
                description=issue_data["description"],
                status=issue_data["status"],
                priority=issue_data["priority"],
                assignee_id=users[i % len(users)].id,
                created_at=created_at,
                updated_at=updated_at,
            )

            # Set resolved_at for resolved issues
            if issue.status == IssueStatus.RESOLVED:
                issue.resolved_at = updated_at

            issues.append(issue)

        session.add_all(issues)
        await session.flush()
        await session.commit()

        print(f"✓ Added {len(issues)} realistic issues")
        return issues


async def add_comments_to_issues():
    """Add realistic comments to issues."""
    print("Adding comments to issues...")

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # Get all users and issues
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        issues_result = await session.execute(select(Issue))
        issues = issues_result.scalars().all()

        if not users or not issues:
            print("⚠️  No users or issues found.")
            return []

        comments_data = [
            "I'm starting to work on this issue.",
            "Found the root cause. It's related to the async handling.",
            "Created a PR for this. Please review.",
            "This is blocking the release. Can we prioritize?",
            "I've tested the fix locally and it works.",
            "We should add unit tests for this.",
            "Documentation needs to be updated as well.",
            "This is a duplicate of issue #5.",
            "Can someone help me understand the requirements better?",
            "Fixed and deployed to staging.",
            "Verified in production. Closing this issue.",
            "We need to discuss this in the next team meeting.",
            "I've assigned this to myself.",
            "This might be related to the recent database migration.",
            "Let's schedule a call to discuss the approach.",
        ]

        comments = []
        for issue in issues[:10]:  # Add comments to first 10 issues
            num_comments = random.randint(1, 4)
            for _ in range(num_comments):
                comment = Comment(
                    issue_id=issue.id,
                    author_id=random.choice(users).id,
                    body=random.choice(comments_data),
                    created_at=issue.created_at + timedelta(hours=random.randint(1, 72)),
                    updated_at=issue.created_at + timedelta(hours=random.randint(1, 72)),
                )
                comments.append(comment)

        session.add_all(comments)
        await session.flush()
        await session.commit()

        print(f"✓ Added {len(comments)} comments")
        return comments


async def assign_labels_to_issues():
    """Assign labels to issues."""
    print("Assigning labels to issues...")

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        from app.models import issue_labels

        # Get all labels and issues
        labels_result = await session.execute(select(Label))
        labels = labels_result.scalars().all()

        issues_result = await session.execute(select(Issue))
        issues = issues_result.scalars().all()

        if not labels or not issues:
            print("⚠️  No labels or issues found.")
            return

        # Assign 1-3 labels to each issue
        assignments = []
        for issue in issues:
            num_labels = random.randint(1, 3)
            selected_labels = random.sample(labels, min(num_labels, len(labels)))

            for label in selected_labels:
                assignments.append(
                    {
                        "issue_id": issue.id,
                        "label_id": label.id,
                        "created_at": datetime.now(UTC),
                    }
                )

        for assignment in assignments:
            await session.execute(issue_labels.insert().values(**assignment))

        await session.commit()
        print(f"✓ Assigned labels to issues ({len(assignments)} assignments)")


async def main():
    """Main function to populate database."""
    print("=" * 60)
    print("Populating Database with Realistic Data")
    print("=" * 60)
    print()

    try:
        # Add data in sequence
        await add_more_users()
        await add_more_labels()
        await add_realistic_issues()
        await add_comments_to_issues()
        await assign_labels_to_issues()

        print()
        print("=" * 60)
        print("✓ Database population complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Added 4 more users (total: 8)")
        print("  - Added 8 more labels (total: 14)")
        print("  - Added 15 realistic issues (total: 20)")
        print("  - Added comments to issues")
        print("  - Assigned labels to all issues")
        print()
        print("Run 'python3 scripts/inspect_db.py stats' to see the updated statistics.")

    except Exception as e:
        print(f"\n✗ Error during population: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
