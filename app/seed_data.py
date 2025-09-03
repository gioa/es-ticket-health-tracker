import logging
from datetime import datetime, timedelta
from sqlmodel import select
from app.database import get_session
from app.models import User, Ticket, TicketStatus, TicketPriority, TicketCategory

logger = logging.getLogger(__name__)


def create_sample_data():
    """Create sample data for dashboard demonstration"""
    with get_session() as session:
        # Check if data already exists (check by specific sample email)
        existing_user = session.exec(select(User).where(User.email == "john.doe@company.com")).first()
        if existing_user:
            logger.info("Sample data already exists. Skipping seeding.")
            return

        # Create sample users
        users = [
            User(name="John Doe", email="john.doe@company.com", is_active=True),
            User(name="Jane Smith", email="jane.smith@company.com", is_active=True),
            User(name="Mike Johnson", email="mike.johnson@company.com", is_active=True),
            User(name="Sarah Wilson", email="sarah.wilson@company.com", is_active=True),
            User(
                name="Alex Brown",
                email="alex.brown@company.com",
                is_active=False,  # Inactive user
            ),
        ]

        for user in users:
            session.add(user)
        session.commit()

        # Refresh to get IDs
        for user in users:
            session.refresh(user)

        # Create sample tickets with various statuses and priorities
        base_time = datetime.utcnow()

        tickets = [
            Ticket(
                title="Login authentication failure",
                description="Users are experiencing intermittent login failures when using valid credentials. The issue appears to be related to session management.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                category=TicketCategory.BUG,
                creator_id=users[0].id if users[0].id is not None else 1,
                assignee_id=users[1].id if users[1].id is not None else None,
                created_at=base_time - timedelta(hours=2),
                updated_at=base_time - timedelta(hours=1),
                estimated_hours=6.0,
                tags="authentication,login,sessions",
            ),
            Ticket(
                title="Implement dark mode theme",
                description="Add dark mode theme option to improve user experience during nighttime usage. Should include toggle in user settings.",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=users[2].id if users[2].id is not None else 1,
                assignee_id=users[1].id if users[1].id is not None else None,
                created_at=base_time - timedelta(days=3),
                updated_at=base_time - timedelta(hours=4),
                estimated_hours=12.0,
                actual_hours=8.0,
                tags="ui,theme,accessibility",
            ),
            Ticket(
                title="Database performance optimization",
                description="Slow query performance affecting user experience. Need to optimize database indexes and query structure.",
                status=TicketStatus.RESOLVED,
                priority=TicketPriority.CRITICAL,
                category=TicketCategory.MAINTENANCE,
                creator_id=users[0].id if users[0].id is not None else 1,
                assignee_id=users[2].id if users[2].id is not None else None,
                created_at=base_time - timedelta(days=5),
                updated_at=base_time - timedelta(hours=6),
                resolved_at=base_time - timedelta(hours=6),
                estimated_hours=8.0,
                actual_hours=10.5,
                tags="database,performance,optimization",
            ),
            Ticket(
                title="Email notification system setup",
                description="Configure automated email notifications for ticket status changes and assignments.",
                status=TicketStatus.CLOSED,
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=users[3].id if users[3].id is not None else 1,
                assignee_id=users[2].id if users[2].id is not None else None,
                created_at=base_time - timedelta(days=7),
                updated_at=base_time - timedelta(days=1),
                resolved_at=base_time - timedelta(days=2),
                estimated_hours=4.0,
                actual_hours=3.5,
                tags="email,notifications,automation",
            ),
            Ticket(
                title="Mobile app crashes on startup",
                description="Mobile application is crashing immediately after launch on certain Android devices. Need to investigate device compatibility.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.CRITICAL,
                category=TicketCategory.BUG,
                creator_id=users[1].id if users[1].id is not None else 1,
                created_at=base_time - timedelta(hours=8),
                updated_at=base_time - timedelta(hours=8),
                estimated_hours=16.0,
                tags="mobile,android,crash",
            ),
            Ticket(
                title="User onboarding tutorial",
                description="Create interactive tutorial to help new users understand the application features and navigation.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.LOW,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=users[3].id if users[3].id is not None else 1,
                created_at=base_time - timedelta(days=1),
                updated_at=base_time - timedelta(days=1),
                estimated_hours=20.0,
                tags="onboarding,tutorial,ux",
            ),
            Ticket(
                title="Security audit findings",
                description="Address security vulnerabilities identified in the recent security audit. Includes input validation and authentication improvements.",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.HIGH,
                category=TicketCategory.MAINTENANCE,
                creator_id=users[0].id if users[0].id is not None else 1,
                assignee_id=users[2].id if users[2].id is not None else None,
                created_at=base_time - timedelta(days=2),
                updated_at=base_time - timedelta(hours=12),
                estimated_hours=24.0,
                actual_hours=18.0,
                tags="security,audit,vulnerability",
            ),
            Ticket(
                title="API rate limiting implementation",
                description="Implement rate limiting for API endpoints to prevent abuse and ensure fair usage across all clients.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=users[2].id if users[2].id is not None else 1,
                assignee_id=users[1].id if users[1].id is not None else None,
                created_at=base_time - timedelta(hours=6),
                updated_at=base_time - timedelta(hours=6),
                estimated_hours=8.0,
                tags="api,rate-limiting,security",
            ),
            Ticket(
                title="Customer support chat widget",
                description="Integrate customer support chat widget to provide real-time assistance to users.",
                status=TicketStatus.RESOLVED,
                priority=TicketPriority.LOW,
                category=TicketCategory.FEATURE_REQUEST,
                creator_id=users[3].id if users[3].id is not None else 1,
                assignee_id=users[0].id if users[0].id is not None else None,
                created_at=base_time - timedelta(days=6),
                updated_at=base_time - timedelta(days=3),
                resolved_at=base_time - timedelta(days=3),
                estimated_hours=12.0,
                actual_hours=14.0,
                tags="support,chat,customer-service",
            ),
            Ticket(
                title="Backup system maintenance",
                description="Scheduled maintenance of backup systems and verification of data integrity.",
                status=TicketStatus.CLOSED,
                priority=TicketPriority.HIGH,
                category=TicketCategory.MAINTENANCE,
                creator_id=users[0].id if users[0].id is not None else 1,
                assignee_id=users[3].id if users[3].id is not None else None,
                created_at=base_time - timedelta(days=4),
                updated_at=base_time - timedelta(days=2),
                resolved_at=base_time - timedelta(days=2),
                estimated_hours=6.0,
                actual_hours=5.5,
                tags="backup,maintenance,data-integrity",
            ),
        ]

        for ticket in tickets:
            session.add(ticket)
        session.commit()

        logger.info(f"Created {len(users)} users and {len(tickets)} tickets successfully!")
        logger.info("Sample data has been seeded to the database.")


if __name__ == "__main__":
    create_sample_data()
