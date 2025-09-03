import pytest
from app.database import reset_db, get_session
from app.models import User, Ticket, TicketStatus, TicketPriority, TicketCategory
from app.dashboard_service import DashboardService


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test"""
    reset_db()


def test_dashboard_service_empty_database():
    """Test dashboard service with empty database"""
    tickets = DashboardService.get_all_tickets()
    assert tickets == []

    stats = DashboardService.get_dashboard_stats()
    assert stats["total_tickets"] == 0
    assert stats["avg_resolution_hours"] is None


def test_dashboard_service_with_single_ticket():
    """Test dashboard service with one ticket"""
    with get_session() as session:
        # Create user first
        user = User(name="Test User", email="test@dashboard.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create ticket
        ticket = Ticket(
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            category=TicketCategory.BUG,
            creator_id=user.id if user.id is not None else 1,
        )
        session.add(ticket)
        session.commit()

    # Test service methods
    tickets = DashboardService.get_all_tickets()
    assert len(tickets) == 1
    assert tickets[0].title == "Test Ticket"
    assert tickets[0].creator_name == "Test User"

    stats = DashboardService.get_dashboard_stats()
    assert stats["total_tickets"] == 1
    assert stats["status_breakdown"]["open"] == 1


def test_ticket_status_update():
    """Test updating ticket status"""
    with get_session() as session:
        user = User(name="Test User", email="status_test@dashboard.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        ticket = Ticket(
            title="Status Test",
            description="Test ticket for status update",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            category=TicketCategory.FEATURE_REQUEST,
            creator_id=user.id if user.id is not None else 1,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        ticket_id = ticket.id

    # Test status update
    if ticket_id is not None:
        success = DashboardService.update_ticket_status(ticket_id, TicketStatus.RESOLVED)
        assert success

        # Verify update
        updated_ticket = DashboardService.get_ticket_by_id(ticket_id)
        assert updated_ticket is not None
        assert updated_ticket.status == TicketStatus.RESOLVED
        assert updated_ticket.resolved_at is not None


def test_filter_tickets():
    """Test ticket filtering functionality"""
    with get_session() as session:
        user = User(name="Filter User", email="filter@dashboard.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create tickets with different priorities
        tickets = [
            Ticket(
                title="High Priority Bug",
                description="Critical issue",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                category=TicketCategory.BUG,
                creator_id=user.id if user.id is not None else 1,
                tags="urgent,bug",
            ),
            Ticket(
                title="Low Priority Feature",
                description="Nice to have feature",
                status=TicketStatus.OPEN,
                priority=TicketPriority.LOW,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=user.id if user.id is not None else 1,
                tags="enhancement",
            ),
        ]

        for ticket in tickets:
            session.add(ticket)
        session.commit()

    # Test filtering by priority
    high_priority = DashboardService.filter_tickets(priority=TicketPriority.HIGH)
    assert len(high_priority) == 1
    assert high_priority[0].title == "High Priority Bug"

    # Test search filtering
    search_results = DashboardService.filter_tickets(search_term="urgent")
    assert len(search_results) == 1
    assert search_results[0].title == "High Priority Bug"


def test_user_management():
    """Test user-related service methods"""
    with get_session() as session:
        users = [
            User(name="Active User", email="active@dashboard.com", is_active=True),
            User(name="Inactive User", email="inactive@dashboard.com", is_active=False),
        ]

        for user in users:
            session.add(user)
        session.commit()

    # Get all active users
    active_users = DashboardService.get_all_users()
    assert len(active_users) == 1
    assert active_users[0].name == "Active User"


def test_ticket_assignment():
    """Test ticket assignment functionality"""
    with get_session() as session:
        creator = User(name="Creator", email="creator@dashboard.com")
        assignee = User(name="Assignee", email="assignee@dashboard.com")
        session.add(creator)
        session.add(assignee)
        session.commit()
        session.refresh(creator)
        session.refresh(assignee)

        ticket = Ticket(
            title="Assignment Test",
            description="Test ticket assignment",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            category=TicketCategory.SUPPORT,
            creator_id=creator.id if creator.id is not None else 1,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        ticket_id = ticket.id
        assignee_id = assignee.id

    # Test assignment
    if ticket_id is not None and assignee_id is not None:
        success = DashboardService.assign_ticket(ticket_id, assignee_id)
        assert success

        # Verify assignment
        assigned_ticket = DashboardService.get_ticket_by_id(ticket_id)
        assert assigned_ticket is not None
        assert assigned_ticket.assignee_id == assignee_id

        # Test unassignment
        success = DashboardService.assign_ticket(ticket_id, None)
        assert success

        unassigned_ticket = DashboardService.get_ticket_by_id(ticket_id)
        assert unassigned_ticket is not None
        assert unassigned_ticket.assignee_id is None
