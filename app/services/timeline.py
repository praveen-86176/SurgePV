"""
Timeline service for tracking issue history.

This is a bonus feature that provides a chronological view of all events
related to an issue (status changes, comments, label updates, etc.).
"""
from typing import List
from datetime import datetime
from sqlalchemy import select, union_all, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Issue, Comment, issue_labels
from app.repositories import IssueRepository, CommentRepository, UserRepository
from app.schemas import TimelineEvent, UserResponse


class TimelineService:
    """Service for generating issue timelines."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.issue_repo = IssueRepository(db)
        self.comment_repo = CommentRepository(db)
        self.user_repo = UserRepository(db)
    
    async def get_issue_timeline(self, issue_id: int) -> List[TimelineEvent]:
        """
        Get a chronological timeline of all events for an issue.
        
        Events include:
        - Issue creation
        - Status changes (inferred from updated_at)
        - Comments added
        - Labels added/removed
        
        Returns events sorted by timestamp in ascending order.
        """
        # Verify issue exists
        issue = await self.issue_repo.get_by_id(issue_id, with_relations=True)
        if not issue:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Issue not found")
        
        timeline: List[TimelineEvent] = []
        
        # 1. Issue created event
        timeline.append(TimelineEvent(
            event_type="created",
            timestamp=issue.created_at,
            details={
                "title": issue.title,
                "status": issue.status.value,
                "priority": issue.priority.value,
                "assignee_id": issue.assignee_id
            },
            user=UserResponse.model_validate(issue.assignee) if issue.assignee else None
        ))
        
        # 2. Status change events (if updated_at != created_at)
        if issue.updated_at > issue.created_at:
            timeline.append(TimelineEvent(
                event_type="status_changed",
                timestamp=issue.updated_at,
                details={
                    "current_status": issue.status.value,
                    "note": "Status or other fields updated"
                },
                user=UserResponse.model_validate(issue.assignee) if issue.assignee else None
            ))
        
        # 3. Comment events
        comments = await self.comment_repo.get_by_issue_id(issue_id)
        for comment in comments:
            timeline.append(TimelineEvent(
                event_type="comment_added",
                timestamp=comment.created_at,
                details={
                    "comment_id": comment.id,
                    "body": comment.body[:100] + "..." if len(comment.body) > 100 else comment.body
                },
                user=UserResponse.model_validate(comment.author) if comment.author else None
            ))
        
        # 4. Label events (current labels)
        for label in issue.labels:
            timeline.append(TimelineEvent(
                event_type="label_added",
                timestamp=issue.updated_at,  # Approximate - we don't track exact time
                details={
                    "label_id": label.id,
                    "label_name": label.name,
                    "label_color": label.color
                },
                user=None  # We don't track who added labels
            ))
        
        # 5. Resolved event (if applicable)
        if issue.resolved_at:
            timeline.append(TimelineEvent(
                event_type="status_changed",
                timestamp=issue.resolved_at,
                details={
                    "status": "resolved",
                    "note": "Issue marked as resolved"
                },
                user=UserResponse.model_validate(issue.assignee) if issue.assignee else None
            ))
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x.timestamp)
        
        return timeline
