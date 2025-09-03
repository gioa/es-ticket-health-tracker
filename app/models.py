from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal


# Persistent models (stored in database)


class ESTicket(SQLModel, table=True):
    """Main ES ticket model with all required fields"""

    __tablename__ = "es_tickets"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=50, index=True)  # Ticket key like "ES-1234"
    summary: str = Field(max_length=1000)  # Used as title in UI
    description: Optional[str] = Field(default=None, max_length=10000)
    status: str = Field(max_length=100, index=True)
    type: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[str] = Field(default=None, max_length=50)
    resolution: Optional[str] = Field(default=None, max_length=200)
    created: datetime = Field(index=True)  # Ticket creation date
    updated: datetime = Field(index=True)  # Last updated date
    assignee: Optional[str] = Field(default=None, max_length=200)
    eng_team: Optional[str] = Field(default=None, max_length=100, index=True)  # Engineering team
    severity: Optional[str] = Field(default=None, max_length=50, index=True)
    outage_start_date: Optional[datetime] = Field(default=None)
    outage_end_date: Optional[datetime] = Field(default=None)
    es_components: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # JSON list of components

    # Computed fields for analytics
    mitigated_date: Optional[datetime] = Field(default=None)  # When ticket was mitigated
    resolved_date: Optional[datetime] = Field(default=None)  # When ticket was resolved
    time_to_resolve_hours: Optional[Decimal] = Field(default=None, decimal_places=2)  # Hours to resolve

    # Import/sync metadata
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    flags: List["UserTicketFlag"] = Relationship(back_populates="ticket")


class User(SQLModel, table=True):
    """User model for tracking who flags tickets"""

    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=100, index=True)
    email: Optional[str] = Field(default=None, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    flags: List["UserTicketFlag"] = Relationship(back_populates="user")


class UserTicketFlag(SQLModel, table=True):
    """Junction table for user flagged tickets"""

    __tablename__ = "user_ticket_flags"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    ticket_id: int = Field(foreign_key="es_tickets.id", index=True)
    flagged_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, max_length=1000)  # Optional user notes

    # Relationships
    user: User = Relationship(back_populates="flags")
    ticket: ESTicket = Relationship(back_populates="flags")


class TeamConfig(SQLModel, table=True):
    """Configuration for engineering teams"""

    __tablename__ = "team_configs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str = Field(unique=True, max_length=100, index=True)
    display_name: str = Field(max_length=200)
    is_active: bool = Field(default=True)
    team_lead: Optional[str] = Field(default=None, max_length=200)
    slack_channel: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TicketImportLog(SQLModel, table=True):
    """Log of ticket import/sync operations"""

    __tablename__ = "ticket_import_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    import_started: datetime = Field(default_factory=datetime.utcnow)
    import_completed: Optional[datetime] = Field(default=None)
    tickets_processed: int = Field(default=0)
    tickets_created: int = Field(default=0)
    tickets_updated: int = Field(default=0)
    status: str = Field(default="running", max_length=50)  # running, completed, failed
    error_message: Optional[str] = Field(default=None, max_length=2000)
    import_source: str = Field(max_length=100)  # e.g., "jira_api", "csv_upload"


# Non-persistent schemas (for validation, forms, API requests/responses)


class ESTicketCreate(SQLModel, table=False):
    """Schema for creating new ES tickets"""

    key: str = Field(max_length=50)
    summary: str = Field(max_length=1000)
    description: Optional[str] = Field(default=None, max_length=10000)
    status: str = Field(max_length=100)
    type: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[str] = Field(default=None, max_length=50)
    resolution: Optional[str] = Field(default=None, max_length=200)
    created: datetime
    updated: datetime
    assignee: Optional[str] = Field(default=None, max_length=200)
    eng_team: Optional[str] = Field(default=None, max_length=100)
    severity: Optional[str] = Field(default=None, max_length=50)
    outage_start_date: Optional[datetime] = Field(default=None)
    outage_end_date: Optional[datetime] = Field(default=None)
    es_components: Optional[List[str]] = Field(default=None)


class ESTicketUpdate(SQLModel, table=False):
    """Schema for updating ES tickets"""

    summary: Optional[str] = Field(default=None, max_length=1000)
    description: Optional[str] = Field(default=None, max_length=10000)
    status: Optional[str] = Field(default=None, max_length=100)
    type: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[str] = Field(default=None, max_length=50)
    resolution: Optional[str] = Field(default=None, max_length=200)
    updated: Optional[datetime] = Field(default=None)
    assignee: Optional[str] = Field(default=None, max_length=200)
    eng_team: Optional[str] = Field(default=None, max_length=100)
    severity: Optional[str] = Field(default=None, max_length=50)
    outage_start_date: Optional[datetime] = Field(default=None)
    outage_end_date: Optional[datetime] = Field(default=None)
    es_components: Optional[List[str]] = Field(default=None)
    mitigated_date: Optional[datetime] = Field(default=None)
    resolved_date: Optional[datetime] = Field(default=None)


class UserCreate(SQLModel, table=False):
    """Schema for creating users"""

    username: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=200)


class UserTicketFlagCreate(SQLModel, table=False):
    """Schema for creating ticket flags"""

    user_id: int
    ticket_id: int
    notes: Optional[str] = Field(default=None, max_length=1000)


class FilterParams(SQLModel, table=False):
    """Schema for global filter parameters"""

    date_start: Optional[datetime] = Field(default=None)
    date_end: Optional[datetime] = Field(default=None)
    teams: Optional[List[str]] = Field(default=None)
    severities: Optional[List[str]] = Field(default=None)
    statuses: Optional[List[str]] = Field(default=None)


class KPIData(SQLModel, table=False):
    """Schema for KPI card data"""

    tickets_created: int
    tickets_mitigated: int
    open_tickets: int
    avg_time_to_resolve_hours: Optional[Decimal] = Field(default=None, decimal_places=2)


class TimeSeriesPoint(SQLModel, table=False):
    """Schema for time series chart data points"""

    date: str  # ISO format date string
    created: int
    mitigated: int
    resolved: int


class StackedBarData(SQLModel, table=False):
    """Schema for stacked bar chart data"""

    status: str
    severity_counts: Dict[str, int]


class TeamTicketCount(SQLModel, table=False):
    """Schema for team ticket count data"""

    team: str
    ticket_count: int


class TicketExportRow(SQLModel, table=False):
    """Schema for CSV export of tickets"""

    key: str
    title: str
    team: Optional[str]
    severity: Optional[str]
    status: str
    created: str  # ISO format
    updated: str  # ISO format
    assignee: Optional[str]
    time_to_resolve_hours: Optional[Decimal]
    flagged_at: Optional[str]  # ISO format, only for flagged tickets
    flag_notes: Optional[str]
