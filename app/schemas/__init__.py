"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models import IssueStatus, IssuePriority


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Label Schemas
# ============================================================================

class LabelBase(BaseModel):
    """Base label schema."""
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: Optional[str] = None


class LabelCreate(LabelBase):
    """Schema for creating a label."""
    pass


class LabelResponse(LabelBase):
    """Schema for label responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Comment Schemas
# ============================================================================

class CommentBase(BaseModel):
    """Base comment schema."""
    body: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    author_id: int = Field(..., gt=0)
    
    @field_validator('body')
    @classmethod
    def validate_body_not_empty(cls, v: str) -> str:
        """Ensure comment body is not just whitespace."""
        if not v.strip():
            raise ValueError('Comment body cannot be empty or whitespace')
        return v.strip()


class CommentResponse(CommentBase):
    """Schema for comment responses."""
    id: int
    issue_id: int
    author_id: int
    author: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Issue Schemas
# ============================================================================

class IssueBase(BaseModel):
    """Base issue schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    priority: IssuePriority = IssuePriority.MEDIUM
    assignee_id: Optional[int] = Field(None, gt=0)


class IssueCreate(IssueBase):
    """Schema for creating an issue."""
    pass


class IssueUpdate(BaseModel):
    """Schema for updating an issue (partial updates allowed)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assignee_id: Optional[int] = Field(None, gt=0)
    version: int = Field(..., gt=0, description="Current version for optimistic locking")


class IssueResponse(IssueBase):
    """Schema for issue responses."""
    id: int
    version: int
    assignee: Optional[UserResponse] = None
    labels: List[LabelResponse] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class IssueDetailResponse(IssueResponse):
    """Schema for detailed issue responses with comments."""
    comments: List[CommentResponse] = []


# ============================================================================
# Bulk Operations Schemas
# ============================================================================

class BulkStatusUpdate(BaseModel):
    """Schema for bulk status updates."""
    issue_ids: List[int] = Field(..., min_length=1)
    status: IssueStatus
    
    @field_validator('issue_ids')
    @classmethod
    def validate_unique_ids(cls, v: List[int]) -> List[int]:
        """Ensure all issue IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError('Duplicate issue IDs are not allowed')
        return v


class BulkStatusUpdateResponse(BaseModel):
    """Response schema for bulk status updates."""
    updated_count: int
    issue_ids: List[int]
    status: IssueStatus


# ============================================================================
# Label Assignment Schemas
# ============================================================================

class LabelAssignment(BaseModel):
    """Schema for assigning labels to an issue."""
    label_names: List[str] = Field(..., description="List of label names to assign")
    
    @field_validator('label_names')
    @classmethod
    def validate_unique_labels(cls, v: List[str]) -> List[str]:
        """Ensure all label names are unique."""
        if len(v) != len(set(v)):
            raise ValueError('Duplicate label names are not allowed')
        return v


# ============================================================================
# CSV Import Schemas
# ============================================================================

class CSVImportError(BaseModel):
    """Schema for CSV import row errors."""
    row_number: int
    errors: List[str]


class CSVImportResponse(BaseModel):
    """Response schema for CSV import."""
    total_rows: int
    successful: int
    failed: int
    errors: List[CSVImportError] = []


# ============================================================================
# Report Schemas
# ============================================================================

class TopAssigneeResponse(BaseModel):
    """Schema for top assignee report."""
    assignee_id: int
    assignee: Optional[UserResponse] = None
    resolved_count: int


class LatencyReportResponse(BaseModel):
    """Schema for resolution latency report."""
    assignee_id: int
    assignee: Optional[UserResponse] = None
    average_resolution_hours: float
    resolved_count: int


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[IssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Timeline Schemas (Bonus Feature)
# ============================================================================

class TimelineEventType(str):
    """Timeline event types."""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    LABEL_ADDED = "label_added"
    LABEL_REMOVED = "label_removed"
    ASSIGNED = "assigned"


class TimelineEvent(BaseModel):
    """Schema for timeline events."""
    event_type: str
    timestamp: datetime
    details: dict
    user: Optional[UserResponse] = None
