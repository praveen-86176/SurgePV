"""
Repository layer for database operations.
"""
from typing import Optional, List, Sequence
from datetime import datetime
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Issue, Comment, Label, User, IssueStatus, issue_labels


class IssueRepository:
    """Repository for Issue database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, issue: Issue) -> Issue:
        """Create a new issue."""
        self.db.add(issue)
        await self.db.flush()
        await self.db.refresh(issue)
        return issue
    
    async def get_by_id(self, issue_id: int, with_relations: bool = False) -> Optional[Issue]:
        """Get issue by ID with optional eager loading."""
        query = select(Issue).where(Issue.id == issue_id)
        
        if with_relations:
            query = query.options(
                selectinload(Issue.assignee),
                selectinload(Issue.labels),
                selectinload(Issue.comments).selectinload(Comment.author)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[IssueStatus] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> tuple[Sequence[Issue], int]:
        """
        Get all issues with filtering and pagination.
        
        Returns:
            Tuple of (issues, total_count)
        """
        # Build base query
        query = select(Issue).options(
            selectinload(Issue.assignee),
            selectinload(Issue.labels)
        )
        
        # Apply filters
        filters = []
        if status:
            filters.append(Issue.status == status)
        if priority:
            filters.append(Issue.priority == priority)
        if assignee_id:
            filters.append(Issue.assignee_id == assignee_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(Issue)
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        issues = result.scalars().all()
        
        return issues, total
    
    async def update(self, issue: Issue) -> Issue:
        """Update an issue and increment version."""
        issue.version += 1
        issue.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(issue)
        return issue
    
    async def delete(self, issue: Issue) -> None:
        """Delete an issue."""
        await self.db.delete(issue)
        await self.db.flush()
    
    async def bulk_update_status(self, issue_ids: List[int], status: IssueStatus) -> int:
        """
        Bulk update issue status.
        
        Returns:
            Number of updated issues
        """
        # Get all issues
        query = select(Issue).where(Issue.id.in_(issue_ids))
        result = await self.db.execute(query)
        issues = result.scalars().all()
        
        if len(issues) != len(issue_ids):
            raise ValueError("One or more issue IDs not found")
        
        # Update all issues
        updated_count = 0
        for issue in issues:
            issue.status = status
            issue.version += 1
            issue.updated_at = datetime.utcnow()
            
            # Set resolved_at timestamp if status is resolved
            if status == IssueStatus.RESOLVED and not issue.resolved_at:
                issue.resolved_at = datetime.utcnow()
            elif status != IssueStatus.RESOLVED:
                issue.resolved_at = None
            
            updated_count += 1
        
        await self.db.flush()
        return updated_count
    
    async def get_top_assignees(self, limit: int = 10) -> List[tuple[int, int]]:
        """
        Get top assignees by resolved issue count.
        
        Returns:
            List of (assignee_id, resolved_count) tuples
        """
        query = (
            select(Issue.assignee_id, func.count(Issue.id).label('resolved_count'))
            .where(
                and_(
                    Issue.status == IssueStatus.RESOLVED,
                    Issue.assignee_id.isnot(None)
                )
            )
            .group_by(Issue.assignee_id)
            .order_by(func.count(Issue.id).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return [(row[0], row[1]) for row in result.all()]
    
    async def get_resolution_latency(self) -> List[tuple[int, float, int]]:
        """
        Get average resolution time per assignee.
        
        Returns:
            List of (assignee_id, avg_hours, resolved_count) tuples
        """
        # Calculate hours between created_at and resolved_at
        query = (
            select(
                Issue.assignee_id,
                func.avg(
                    func.extract('epoch', Issue.resolved_at - Issue.created_at) / 3600
                ).label('avg_hours'),
                func.count(Issue.id).label('resolved_count')
            )
            .where(
                and_(
                    Issue.status == IssueStatus.RESOLVED,
                    Issue.assignee_id.isnot(None),
                    Issue.resolved_at.isnot(None)
                )
            )
            .group_by(Issue.assignee_id)
            .order_by(func.avg(
                func.extract('epoch', Issue.resolved_at - Issue.created_at) / 3600
            ))
        )
        
        result = await self.db.execute(query)
        return [(row[0], float(row[1]), row[2]) for row in result.all()]


class CommentRepository:
    """Repository for Comment database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, comment: Comment) -> Comment:
        """Create a new comment."""
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment, ['author'])
        return comment
    
    async def get_by_issue_id(self, issue_id: int) -> Sequence[Comment]:
        """Get all comments for an issue."""
        query = (
            select(Comment)
            .where(Comment.issue_id == issue_id)
            .options(selectinload(Comment.author))
            .order_by(Comment.created_at)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class LabelRepository:
    """Repository for Label database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, label: Label) -> Label:
        """Create a new label."""
        self.db.add(label)
        await self.db.flush()
        await self.db.refresh(label)
        return label
    
    async def get_by_name(self, name: str) -> Optional[Label]:
        """Get label by name."""
        query = select(Label).where(Label.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_names(self, names: List[str]) -> Sequence[Label]:
        """Get multiple labels by names."""
        query = select(Label).where(Label.name.in_(names))
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_or_create(self, name: str, color: Optional[str] = None) -> Label:
        """Get existing label or create new one."""
        label = await self.get_by_name(name)
        if not label:
            label = Label(name=name, color=color)
            label = await self.create(label)
        return label
    
    async def replace_issue_labels(self, issue: Issue, label_names: List[str]) -> None:
        """
        Atomically replace all labels for an issue.
        
        This operation:
        1. Gets or creates all labels
        2. Clears existing labels
        3. Assigns new labels
        """
        # Get or create all labels
        labels = []
        for name in label_names:
            label = await self.get_or_create(name)
            labels.append(label)
        
        # Replace labels (SQLAlchemy handles the association table)
        issue.labels = labels
        await self.db.flush()


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def exists(self, user_id: int) -> bool:
        """Check if user exists."""
        query = select(func.count()).select_from(User).where(User.id == user_id)
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count > 0
