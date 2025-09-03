from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enumeration"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, Enum):
    """Ticket category enumeration"""

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    SUPPORT = "support"
    MAINTENANCE = "maintenance"
    OTHER = "other"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    """User model for ticket assignment and creation tracking"""

    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    created_tickets: List["Ticket"] = Relationship(
        back_populates="creator", sa_relationship_kwargs={"foreign_keys": "[Ticket.creator_id]"}
    )
    assigned_tickets: List["Ticket"] = Relationship(
        back_populates="assignee", sa_relationship_kwargs={"foreign_keys": "[Ticket.assignee_id]"}
    )


class Ticket(SQLModel, table=True):
    """Main ticket model for the dashboard"""

    __tablename__ = "tickets"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    category: TicketCategory = Field(default=TicketCategory.OTHER)

    # Foreign keys
    creator_id: int = Field(foreign_key="users.id")
    assignee_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)

    # Additional fields for dashboard functionality
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    tags: str = Field(default="", max_length=500)  # Comma-separated tags

    # Relationships
    creator: User = Relationship(
        back_populates="created_tickets", sa_relationship_kwargs={"foreign_keys": "[Ticket.creator_id]"}
    )
    assignee: Optional[User] = Relationship(
        back_populates="assigned_tickets", sa_relationship_kwargs={"foreign_keys": "[Ticket.assignee_id]"}
    )


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    """Schema for creating new users"""

    name: str = Field(max_length=100)
    email: str = Field(max_length=255)


class TicketCreate(SQLModel, table=False):
    """Schema for creating new tickets"""

    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    category: TicketCategory = Field(default=TicketCategory.OTHER)
    creator_id: int
    assignee_id: Optional[int] = Field(default=None)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    tags: str = Field(default="", max_length=500)


class TicketUpdate(SQLModel, table=False):
    """Schema for updating existing tickets"""

    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TicketStatus] = Field(default=None)
    priority: Optional[TicketPriority] = Field(default=None)
    category: Optional[TicketCategory] = Field(default=None)
    assignee_id: Optional[int] = Field(default=None)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    tags: Optional[str] = Field(default=None, max_length=500)
    resolved_at: Optional[datetime] = Field(default=None)


class TicketResponse(SQLModel, table=False):
    """Schema for ticket API responses with related data"""

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    creator_name: str
    assignee_name: Optional[str]
    created_at: str  # ISO format datetime string
    updated_at: str  # ISO format datetime string
    resolved_at: Optional[str]  # ISO format datetime string
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    tags: str
