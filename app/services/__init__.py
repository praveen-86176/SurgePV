"""
Service layer for business logic.
"""
from typing import Optional, List, Sequence
from datetime import datetime
import csv
import io
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import Issue, Comment, Label, User, IssueStatus, IssuePriority
from app.repositories import (
    IssueRepository, CommentRepository, LabelRepository, UserRepository
)
from app.schemas import (
    IssueCreate, IssueUpdate, IssueResponse, IssueDetailResponse,
    CommentCreate, CommentResponse,
    LabelAssignment, LabelResponse,
    BulkStatusUpdate, BulkStatusUpdateResponse,
    CSVImportResponse, CSVImportError,
    TopAssigneeResponse, LatencyReportResponse,
    UserResponse
)


class IssueService:
    """Service for issue-related business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.issue_repo = IssueRepository(db)
        self.user_repo = UserRepository(db)
        self.label_repo = LabelRepository(db)
    
    async def create_issue(self, issue_data: IssueCreate) -> IssueResponse:
        """
        Create a new issue.
        
        Validates:
        - Assignee exists (if provided)
        """
        # Validate assignee exists
        if issue_data.assignee_id:
            assignee_exists = await self.user_repo.exists(issue_data.assignee_id)
            if not assignee_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Assignee with ID {issue_data.assignee_id} does not exist"
                )
        
        # Create issue
        issue = Issue(**issue_data.model_dump())
        issue = await self.issue_repo.create(issue)
        await self.db.commit()
        
        # Reload with relations
        issue = await self.issue_repo.get_by_id(issue.id, with_relations=True)
        return IssueResponse.model_validate(issue)
    
    async def get_issue(self, issue_id: int, detailed: bool = False) -> IssueResponse | IssueDetailResponse:
        """Get issue by ID."""
        issue = await self.issue_repo.get_by_id(issue_id, with_relations=True)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        if detailed:
            return IssueDetailResponse.model_validate(issue)
        return IssueResponse.model_validate(issue)
    
    async def list_issues(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[IssueStatus] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> tuple[List[IssueResponse], int]:
        """
        List issues with filtering and pagination.
        
        Returns:
            Tuple of (issues, total_count)
        """
        skip = (page - 1) * page_size
        issues, total = await self.issue_repo.get_all(
            skip=skip,
            limit=page_size,
            status=status,
            priority=priority,
            assignee_id=assignee_id
        )
        
        issue_responses = [IssueResponse.model_validate(issue) for issue in issues]
        return issue_responses, total
    
    async def update_issue(self, issue_id: int, issue_data: IssueUpdate) -> IssueResponse:
        """
        Update an issue with optimistic concurrency control.
        
        Validates:
        - Issue exists
        - Version matches (prevents lost updates)
        - Assignee exists (if being updated)
        """
        # Get existing issue
        issue = await self.issue_repo.get_by_id(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Check version for optimistic locking
        if issue.version != issue_data.version:
            raise HTTPException(
                status_code=409,
                detail=f"Version mismatch. Expected {issue.version}, got {issue_data.version}. "
                       "The issue has been modified by another user."
            )
        
        # Validate assignee if being updated
        if issue_data.assignee_id is not None:
            assignee_exists = await self.user_repo.exists(issue_data.assignee_id)
            if not assignee_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Assignee with ID {issue_data.assignee_id} does not exist"
                )
        
        # Update fields
        update_data = issue_data.model_dump(exclude={'version'}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)
        
        # Set resolved_at timestamp if status changed to resolved
        if issue_data.status == IssueStatus.RESOLVED and not issue.resolved_at:
            issue.resolved_at = datetime.utcnow()
        elif issue_data.status and issue_data.status != IssueStatus.RESOLVED:
            issue.resolved_at = None
        
        # Update and commit
        issue = await self.issue_repo.update(issue)
        await self.db.commit()
        
        # Reload with relations
        issue = await self.issue_repo.get_by_id(issue.id, with_relations=True)
        return IssueResponse.model_validate(issue)
    
    async def add_comment(self, issue_id: int, comment_data: CommentCreate) -> CommentResponse:
        """
        Add a comment to an issue.
        
        Validates:
        - Issue exists
        - Author exists
        - Comment body is not empty
        """
        # Validate issue exists
        issue = await self.issue_repo.get_by_id(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Validate author exists
        author_exists = await self.user_repo.exists(comment_data.author_id)
        if not author_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Author with ID {comment_data.author_id} does not exist"
            )
        
        # Create comment
        comment = Comment(
            issue_id=issue_id,
            body=comment_data.body,
            author_id=comment_data.author_id
        )
        
        comment_repo = CommentRepository(self.db)
        comment = await comment_repo.create(comment)
        await self.db.commit()
        
        return CommentResponse.model_validate(comment)
    
    async def replace_labels(self, issue_id: int, label_data: LabelAssignment) -> IssueResponse:
        """
        Atomically replace all labels for an issue.
        
        This operation ensures that label assignment is atomic - either all labels
        are assigned successfully or none are.
        """
        # Validate issue exists
        issue = await self.issue_repo.get_by_id(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Replace labels atomically
        await self.label_repo.replace_issue_labels(issue, label_data.label_names)
        await self.db.commit()
        
        # Reload with relations
        issue = await self.issue_repo.get_by_id(issue.id, with_relations=True)
        return IssueResponse.model_validate(issue)
    
    async def bulk_update_status(self, bulk_data: BulkStatusUpdate) -> BulkStatusUpdateResponse:
        """
        Bulk update issue status in a single transaction.
        
        This operation is atomic - if any issue fails validation,
        the entire operation is rolled back.
        """
        try:
            updated_count = await self.issue_repo.bulk_update_status(
                bulk_data.issue_ids,
                bulk_data.status
            )
            await self.db.commit()
            
            return BulkStatusUpdateResponse(
                updated_count=updated_count,
                issue_ids=bulk_data.issue_ids,
                status=bulk_data.status
            )
        except ValueError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")
    
    async def import_from_csv(self, file: UploadFile) -> CSVImportResponse:
        """
        Import issues from CSV file.
        
        Validates each row independently and provides detailed error reporting.
        
        Expected CSV format:
        title,description,status,priority,assignee_id
        """
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        total_rows = 0
        successful = 0
        errors: List[CSVImportError] = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            total_rows += 1
            row_errors: List[str] = []
            
            try:
                # Validate required fields
                if not row.get('title'):
                    row_errors.append("Title is required")
                
                # Parse status
                status = IssueStatus.OPEN
                if row.get('status'):
                    try:
                        status = IssueStatus(row['status'].lower())
                    except ValueError:
                        row_errors.append(f"Invalid status: {row['status']}")
                
                # Parse priority
                priority = IssuePriority.MEDIUM
                if row.get('priority'):
                    try:
                        priority = IssuePriority(row['priority'].lower())
                    except ValueError:
                        row_errors.append(f"Invalid priority: {row['priority']}")
                
                # Parse assignee_id
                assignee_id = None
                if row.get('assignee_id'):
                    try:
                        assignee_id = int(row['assignee_id'])
                        # Validate assignee exists
                        if not await self.user_repo.exists(assignee_id):
                            row_errors.append(f"Assignee ID {assignee_id} does not exist")
                    except ValueError:
                        row_errors.append(f"Invalid assignee_id: {row['assignee_id']}")
                
                # If there are validation errors, skip this row
                if row_errors:
                    errors.append(CSVImportError(row_number=row_num, errors=row_errors))
                    continue
                
                # Create issue
                issue = Issue(
                    title=row['title'],
                    description=row.get('description', ''),
                    status=status,
                    priority=priority,
                    assignee_id=assignee_id
                )
                await self.issue_repo.create(issue)
                successful += 1
                
            except Exception as e:
                row_errors.append(f"Unexpected error: {str(e)}")
                errors.append(CSVImportError(row_number=row_num, errors=row_errors))
        
        # Commit all successful imports
        await self.db.commit()
        
        return CSVImportResponse(
            total_rows=total_rows,
            successful=successful,
            failed=len(errors),
            errors=errors
        )


class ReportService:
    """Service for generating reports."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.issue_repo = IssueRepository(db)
        self.user_repo = UserRepository(db)
    
    async def get_top_assignees(self, limit: int = 10) -> List[TopAssigneeResponse]:
        """Get top assignees by resolved issue count."""
        results = await self.issue_repo.get_top_assignees(limit)
        
        responses = []
        for assignee_id, resolved_count in results:
            user = await self.user_repo.get_by_id(assignee_id)
            responses.append(TopAssigneeResponse(
                assignee_id=assignee_id,
                assignee=UserResponse.model_validate(user) if user else None,
                resolved_count=resolved_count
            ))
        
        return responses
    
    async def get_resolution_latency(self) -> List[LatencyReportResponse]:
        """Get average resolution time per assignee."""
        results = await self.issue_repo.get_resolution_latency()
        
        responses = []
        for assignee_id, avg_hours, resolved_count in results:
            user = await self.user_repo.get_by_id(assignee_id)
            responses.append(LatencyReportResponse(
                assignee_id=assignee_id,
                assignee=UserResponse.model_validate(user) if user else None,
                average_resolution_hours=round(avg_hours, 2),
                resolved_count=resolved_count
            ))
        
        return responses
