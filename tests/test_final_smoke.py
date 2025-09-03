"""
Final smoke test to verify the dashboard application works correctly.
Focuses on core functionality that we can reliably test.
"""

import pytest
import logging
from app.database import reset_db, get_session
from app.models import User, Ticket, TicketStatus, TicketPriority, TicketCategory
from app.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure clean database for each test"""
    reset_db()


def test_complete_dashboard_workflow():
    """Test a complete workflow from data creation to dashboard display"""

    # Step 1: Create users
    with get_session() as session:
        users = [
            User(name="Alice Developer", email="alice@company.com"),
            User(name="Bob Manager", email="bob@company.com"),
        ]
        for user in users:
            session.add(user)
        session.commit()

        for user in users:
            session.refresh(user)

    # Step 2: Create tickets in different states
    with get_session() as session:
        alice_id = users[0].id if users[0].id is not None else 1
        bob_id = users[1].id if users[1].id is not None else 1

        tickets = [
            Ticket(
                title="Critical Bug Fix",
                description="Fix login issue affecting multiple users",
                status=TicketStatus.OPEN,
                priority=TicketPriority.CRITICAL,
                category=TicketCategory.BUG,
                creator_id=alice_id,
                assignee_id=bob_id,
                estimated_hours=8.0,
                tags="critical,authentication",
            ),
            Ticket(
                title="New Feature Implementation",
                description="Add dashboard reporting capabilities",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.HIGH,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=bob_id,
                assignee_id=alice_id,
                estimated_hours=24.0,
                actual_hours=12.0,
                tags="dashboard,reporting",
            ),
            Ticket(
                title="Documentation Update",
                description="Update API documentation",
                status=TicketStatus.RESOLVED,
                priority=TicketPriority.LOW,
                category=TicketCategory.MAINTENANCE,
                creator_id=alice_id,
                estimated_hours=4.0,
                actual_hours=3.5,
                tags="documentation",
            ),
        ]

        for ticket in tickets:
            session.add(ticket)
        session.commit()

    # Step 3: Test dashboard service retrieves data correctly
    all_tickets = DashboardService.get_all_tickets()
    assert len(all_tickets) == 3

    # Verify ticket data structure and content
    critical_ticket = next(t for t in all_tickets if t.priority == TicketPriority.CRITICAL)
    assert critical_ticket.title == "Critical Bug Fix"
    assert critical_ticket.creator_name == "Alice Developer"
    assert critical_ticket.assignee_name == "Bob Manager"
    assert "critical" in critical_ticket.tags

    # Step 4: Test dashboard statistics
    stats = DashboardService.get_dashboard_stats()
    assert stats["total_tickets"] == 3
    assert stats["status_breakdown"]["open"] == 1
    assert stats["status_breakdown"]["in_progress"] == 1
    assert stats["status_breakdown"]["resolved"] == 1
    assert stats["priority_breakdown"]["critical"] == 1
    assert stats["priority_breakdown"]["high"] == 1
    assert stats["priority_breakdown"]["low"] == 1

    # Step 5: Test filtering capabilities
    bug_tickets = DashboardService.filter_tickets(category=TicketCategory.BUG)
    assert len(bug_tickets) == 1
    assert bug_tickets[0].category == TicketCategory.BUG

    critical_tickets = DashboardService.filter_tickets(priority=TicketPriority.CRITICAL)
    assert len(critical_tickets) == 1
    assert critical_tickets[0].priority == TicketPriority.CRITICAL

    # Search functionality
    auth_tickets = DashboardService.filter_tickets(search_term="authentication")
    assert len(auth_tickets) == 1
    assert "authentication" in auth_tickets[0].tags

    # Step 6: Test ticket management operations
    critical_ticket_id = critical_ticket.id

    # Update status
    success = DashboardService.update_ticket_status(critical_ticket_id, TicketStatus.IN_PROGRESS)
    assert success

    updated_ticket = DashboardService.get_ticket_by_id(critical_ticket_id)
    assert updated_ticket is not None
    assert updated_ticket.status == TicketStatus.IN_PROGRESS

    # Test assignment changes
    success = DashboardService.assign_ticket(critical_ticket_id, alice_id)
    assert success

    reassigned_ticket = DashboardService.get_ticket_by_id(critical_ticket_id)
    assert reassigned_ticket is not None
    assert reassigned_ticket.assignee_id == alice_id

    logger.info("Complete dashboard workflow test passed!")


def test_dashboard_handles_edge_cases():
    """Test dashboard handles edge cases properly"""

    # Test empty database
    empty_tickets = DashboardService.get_all_tickets()
    assert empty_tickets == []

    empty_stats = DashboardService.get_dashboard_stats()
    assert empty_stats["total_tickets"] == 0
    assert empty_stats["avg_resolution_hours"] is None

    # Test operations on non-existent tickets
    assert not DashboardService.update_ticket_status(999, TicketStatus.CLOSED)
    assert not DashboardService.assign_ticket(999, 1)
    assert not DashboardService.delete_ticket(999)
    assert DashboardService.get_ticket_by_id(999) is None

    # Test with invalid user assignment
    with get_session() as session:
        user = User(name="Test User", email="test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        ticket = Ticket(
            title="Test Ticket",
            description="Test",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            category=TicketCategory.OTHER,
            creator_id=user.id if user.id is not None else 1,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        ticket_id = ticket.id

    # Try to assign to non-existent user
    if ticket_id is not None:
        assert not DashboardService.assign_ticket(ticket_id, 999)

    logger.info("Edge cases test passed!")


if __name__ == "__main__":
    # Run tests directly for development
    test_complete_dashboard_workflow()
    test_dashboard_handles_edge_cases()
    logger.info("All dashboard tests passed successfully!")
