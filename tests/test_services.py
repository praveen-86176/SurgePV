"""
Unit tests for the Issue Tracker API.
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Issue, User, Label, Comment, IssueStatus, IssuePriority
from app.services import IssueService, ReportService
from app.schemas import IssueCreate, IssueUpdate, CommentCreate, LabelAssignment, BulkStatusUpdate
from fastapi import HTTPException


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_issue(sample_user):
    """Sample issue for testing."""
    return Issue(
        id=1,
        title="Test Issue",
        description="Test description",
        status=IssueStatus.OPEN,
        priority=IssuePriority.MEDIUM,
        version=1,
        assignee_id=sample_user.id,
        assignee=sample_user,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        labels=[],
        comments=[]
    )


# ============================================================================
# Issue Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_issue_success(mock_db, sample_user):
    """Test successful issue creation."""
    issue_data = IssueCreate(
        title="New Issue",
        description="Test description",
        status=IssueStatus.OPEN,
        priority=IssuePriority.HIGH,
        assignee_id=sample_user.id
    )
    
    service = IssueService(mock_db)
    
    # Mock repository methods
    with patch.object(service.user_repo, 'exists', return_value=True), \
         patch.object(service.issue_repo, 'create') as mock_create, \
         patch.object(service.issue_repo, 'get_by_id') as mock_get:
        
        # Setup mock returns
        created_issue = Issue(
            **issue_data.model_dump(),
            id=1,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        created_issue.assignee = sample_user
        created_issue.labels = []
        created_issue.comments = []
        
        mock_create.return_value = created_issue
        mock_get.return_value = created_issue
        
        # Execute
        result = await service.create_issue(issue_data)
        
        # Verify
        assert result.title == issue_data.title
        assert result.status == issue_data.status
        assert result.priority == issue_data.priority
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_issue_invalid_assignee(mock_db):
    """Test issue creation with non-existent assignee."""
    issue_data = IssueCreate(
        title="New Issue",
        description="Test description",
        assignee_id=999  # Non-existent user
    )
    
    service = IssueService(mock_db)
    
    # Mock repository to return False for user existence
    with patch.object(service.user_repo, 'exists', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await service.create_issue(issue_data)
        
        assert exc_info.value.status_code == 400
        assert "does not exist" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_issue_version_mismatch(mock_db, sample_issue):
    """Test optimistic locking - version mismatch."""
    update_data = IssueUpdate(
        title="Updated Title",
        version=1  # Current version in DB is also 1
    )
    
    # Simulate another user updated the issue (version is now 2)
    sample_issue.version = 2
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'get_by_id', return_value=sample_issue):
        with pytest.raises(HTTPException) as exc_info:
            await service.update_issue(sample_issue.id, update_data)
        
        assert exc_info.value.status_code == 409
        assert "Version mismatch" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_issue_success(mock_db, sample_issue, sample_user):
    """Test successful issue update with correct version."""
    update_data = IssueUpdate(
        title="Updated Title",
        status=IssueStatus.IN_PROGRESS,
        version=1
    )
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'get_by_id') as mock_get, \
         patch.object(service.issue_repo, 'update') as mock_update:
        
        # First call returns issue for update, second for response
        updated_issue = Issue(
            id=sample_issue.id,
            title=update_data.title,
            description=sample_issue.description,
            status=update_data.status,
            priority=sample_issue.priority,
            version=2,  # Version incremented
            assignee_id=sample_user.id,
            assignee=sample_user,
            labels=[],
            comments=[],
            created_at=sample_issue.created_at,
            updated_at=datetime.now(UTC)
        )
        
        mock_get.side_effect = [sample_issue, updated_issue]
        mock_update.return_value = updated_issue
        
        result = await service.update_issue(sample_issue.id, update_data)
        
        assert result.title == update_data.title
        assert result.status == update_data.status
        assert result.version == 2
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_comment_success(mock_db, sample_issue, sample_user):
    """Test adding a comment to an issue."""
    comment_data = CommentCreate(
        body="This is a test comment",
        author_id=sample_user.id
    )
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'get_by_id', return_value=sample_issue), \
         patch.object(service.user_repo, 'exists', return_value=True), \
         patch('app.services.CommentRepository') as MockCommentRepo:
        
        # Setup mock comment repository
        mock_comment_repo = MockCommentRepo.return_value
        created_comment = Comment(
            id=1,
            issue_id=sample_issue.id,
            author_id=sample_user.id,
            body=comment_data.body,
            author=sample_user,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        mock_comment_repo.create = AsyncMock(return_value=created_comment)
        
        result = await service.add_comment(sample_issue.id, comment_data)
        
        assert result.body == comment_data.body
        assert result.author_id == sample_user.id
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_comment_empty_body(mock_db):
    """Test adding a comment with empty body."""
    with pytest.raises(ValueError) as exc_info:
        CommentCreate(body="   ", author_id=1)
    
    assert "cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_bulk_update_status_success(mock_db):
    """Test bulk status update."""
    bulk_data = BulkStatusUpdate(
        issue_ids=[1, 2, 3],
        status=IssueStatus.RESOLVED
    )
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'bulk_update_status', return_value=3):
        result = await service.bulk_update_status(bulk_data)
        
        assert result.updated_count == 3
        assert result.issue_ids == bulk_data.issue_ids
        assert result.status == bulk_data.status
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_update_status_partial_failure(mock_db):
    """Test bulk update with missing issue IDs."""
    bulk_data = BulkStatusUpdate(
        issue_ids=[1, 2, 999],  # 999 doesn't exist
        status=IssueStatus.RESOLVED
    )
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'bulk_update_status', side_effect=ValueError("One or more issue IDs not found")):
        with pytest.raises(HTTPException) as exc_info:
            await service.bulk_update_status(bulk_data)
        
        assert exc_info.value.status_code == 400
        mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_replace_labels_atomic(mock_db, sample_issue):
    """Test atomic label replacement."""
    label_data = LabelAssignment(label_names=["bug", "urgent", "backend"])
    
    service = IssueService(mock_db)
    
    with patch.object(service.issue_repo, 'get_by_id') as mock_get, \
         patch.object(service.label_repo, 'replace_issue_labels') as mock_replace:
        
        # Setup mocks
        labels = [
            Label(id=1, name="bug", color="#d73a4a", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            Label(id=2, name="urgent", color="#ff0000", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            Label(id=3, name="backend", color="#fbca04", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]
        sample_issue.labels = labels
        
        mock_get.side_effect = [sample_issue, sample_issue]
        mock_replace.return_value = None
        
        result = await service.replace_labels(sample_issue.id, label_data)
        
        assert len(result.labels) == 3
        mock_db.commit.assert_called_once()


# ============================================================================
# Report Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_top_assignees(mock_db, sample_user):
    """Test top assignees report."""
    service = ReportService(mock_db)
    
    with patch.object(service.issue_repo, 'get_top_assignees', return_value=[(sample_user.id, 10)]), \
         patch.object(service.user_repo, 'get_by_id', return_value=sample_user):
        
        results = await service.get_top_assignees(limit=10)
        
        assert len(results) == 1
        assert results[0].assignee_id == sample_user.id
        assert results[0].resolved_count == 10


@pytest.mark.asyncio
async def test_get_resolution_latency(mock_db, sample_user):
    """Test resolution latency report."""
    service = ReportService(mock_db)
    
    with patch.object(service.issue_repo, 'get_resolution_latency', return_value=[(sample_user.id, 24.5, 5)]), \
         patch.object(service.user_repo, 'get_by_id', return_value=sample_user):
        
        results = await service.get_resolution_latency()
        
        assert len(results) == 1
        assert results[0].assignee_id == sample_user.id
        assert results[0].average_resolution_hours == 24.5
        assert results[0].resolved_count == 5


# ============================================================================
# Schema Validation Tests
# ============================================================================

def test_issue_create_validation():
    """Test IssueCreate schema validation."""
    # Valid data
    valid_data = IssueCreate(
        title="Test Issue",
        description="Description",
        status=IssueStatus.OPEN,
        priority=IssuePriority.HIGH
    )
    assert valid_data.title == "Test Issue"
    
    # Invalid: empty title
    with pytest.raises(ValueError):
        IssueCreate(title="", description="Test")


def test_bulk_status_unique_ids():
    """Test BulkStatusUpdate validates unique IDs."""
    # Valid: unique IDs
    valid_data = BulkStatusUpdate(issue_ids=[1, 2, 3], status=IssueStatus.RESOLVED)
    assert len(valid_data.issue_ids) == 3
    
    # Invalid: duplicate IDs
    with pytest.raises(ValueError) as exc_info:
        BulkStatusUpdate(issue_ids=[1, 2, 2], status=IssueStatus.RESOLVED)
    
    assert "Duplicate" in str(exc_info.value)


def test_label_assignment_unique_names():
    """Test LabelAssignment validates unique names."""
    # Valid: unique names
    valid_data = LabelAssignment(label_names=["bug", "urgent"])
    assert len(valid_data.label_names) == 2
    
    # Invalid: duplicate names
    with pytest.raises(ValueError) as exc_info:
        LabelAssignment(label_names=["bug", "bug"])
    
    assert "Duplicate" in str(exc_info.value)
