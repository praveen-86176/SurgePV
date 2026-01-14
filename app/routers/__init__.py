"""
API routers for issue management endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import IssuePriority, IssueStatus
from app.schemas import (
    BulkStatusUpdate,
    BulkStatusUpdateResponse,
    CommentCreate,
    CommentResponse,
    CSVImportResponse,
    IssueCreate,
    IssueDetailResponse,
    IssueResponse,
    IssueUpdate,
    LabelAssignment,
    LatencyReportResponse,
    PaginatedResponse,
    TimelineEvent,
    TopAssigneeResponse,
)
from app.services import IssueService, ReportService
from app.services.timeline import TimelineService

router = APIRouter(prefix="/issues", tags=["Issues"])
report_router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================================================
# Issue Endpoints
# ============================================================================


@router.post("", response_model=IssueResponse, status_code=201)
async def create_issue(issue_data: IssueCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new issue.

    Validates:
    - Assignee exists (if provided)
    """
    service = IssueService(db)
    return await service.create_issue(issue_data)


@router.get("", response_model=PaginatedResponse)
async def list_issues(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    assignee_id: Optional[int] = Query(None, ge=1, description="Filter by assignee ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List issues with filtering and pagination.

    Supports filtering by:
    - status
    - priority
    - assignee_id
    """
    service = IssueService(db)
    issues, total = await service.list_issues(
        page=page, page_size=page_size, status=status, priority=priority, assignee_id=assignee_id
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=issues, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/{issue_id}", response_model=IssueDetailResponse)
async def get_issue(issue_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a single issue by ID with all details including comments.
    """
    service = IssueService(db)
    return await service.get_issue(issue_id, detailed=True)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(issue_id: int, issue_data: IssueUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update an issue with optimistic concurrency control.

    The `version` field is mandatory and must match the current version.
    If the version doesn't match, a 409 Conflict error is returned.

    This prevents lost updates in concurrent scenarios.
    """
    service = IssueService(db)
    return await service.update_issue(issue_id, issue_data)


# ============================================================================
# Comment Endpoints
# ============================================================================


@router.post("/{issue_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    issue_id: int, comment_data: CommentCreate, db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to an issue.

    Validates:
    - Issue exists
    - Author exists
    - Comment body is not empty
    """
    service = IssueService(db)
    return await service.add_comment(issue_id, comment_data)


# ============================================================================
# Label Endpoints
# ============================================================================


@router.put("/{issue_id}/labels", response_model=IssueResponse)
async def replace_labels(
    issue_id: int, label_data: LabelAssignment, db: AsyncSession = Depends(get_db)
):
    """
    Atomically replace all labels for an issue.

    This operation:
    1. Creates any new labels that don't exist
    2. Removes all existing labels from the issue
    3. Assigns the new labels

    All operations happen in a single transaction.
    """
    service = IssueService(db)
    return await service.replace_labels(issue_id, label_data)


# ============================================================================
# Bulk Operations
# ============================================================================


@router.post("/bulk-status", response_model=BulkStatusUpdateResponse)
async def bulk_update_status(bulk_data: BulkStatusUpdate, db: AsyncSession = Depends(get_db)):
    """
    Bulk update the status of multiple issues.

    This operation is transactional:
    - All issues must exist
    - If any validation fails, the entire operation is rolled back
    - All updates succeed or none do
    """
    service = IssueService(db)
    return await service.bulk_update_status(bulk_data)


# ============================================================================
# CSV Import
# ============================================================================


@router.post("/import", response_model=CSVImportResponse)
async def import_issues(
    file: UploadFile = File(..., description="CSV file with issues"),
    db: AsyncSession = Depends(get_db),
):
    """
    Import issues from a CSV file.

    Expected CSV format:
    ```
    title,description,status,priority,assignee_id
    Fix login bug,Users cannot log in,open,high,1
    Update docs,Documentation is outdated,open,low,2
    ```

    Each row is validated independently. The response includes:
    - Total rows processed
    - Number of successful imports
    - Number of failed imports
    - Detailed error messages for each failed row
    """
    service = IssueService(db)
    return await service.import_from_csv(file)


# ============================================================================
# Reports
# ============================================================================


@report_router.get("/top-assignees", response_model=List[TopAssigneeResponse])
async def get_top_assignees(
    limit: int = Query(10, ge=1, le=100, description="Number of top assignees to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top assignees by number of resolved issues.

    Returns assignees sorted by the number of issues they've resolved,
    in descending order.
    """
    service = ReportService(db)
    return await service.get_top_assignees(limit)


@report_router.get("/latency", response_model=List[LatencyReportResponse])
async def get_resolution_latency(db: AsyncSession = Depends(get_db)):
    """
    Get average resolution time per assignee.

    Calculates the average time (in hours) between issue creation
    and resolution for each assignee.

    Only includes resolved issues with valid timestamps.
    """
    service = ReportService(db)
    return await service.get_resolution_latency()


# ============================================================================
# Timeline (Bonus Feature)
# ============================================================================


@router.get("/{issue_id}/timeline", response_model=List[TimelineEvent])
async def get_issue_timeline(issue_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a chronological timeline of all events for an issue.

    **Bonus Feature**: This endpoint provides a complete history of the issue,
    including:
    - Issue creation
    - Status changes
    - Comments added
    - Labels assigned
    - Resolution timestamp

    Events are returned in chronological order (oldest to newest).
    """
    service = TimelineService(db)
    return await service.get_issue_timeline(issue_id)
