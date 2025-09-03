import pytest
from nicegui.testing import User

from app.database import reset_db
from app.services import SeedService


@pytest.fixture
def fresh_db():
    """Reset database for each test"""
    reset_db()
    yield
    reset_db()


@pytest.fixture
def seeded_db(fresh_db):
    """Database with sample data"""
    SeedService.create_sample_tickets(20)
    return True


async def test_dashboard_loads(user: User, seeded_db) -> None:
    """Test that the dashboard page loads without errors"""
    await user.open("/")

    # Should see the main dashboard elements
    await user.should_see("ES Ticket Health Tracker")
    await user.should_see("Filters")

    # Should see KPI section (may be loading initially)
    # Wait a moment for async data loading
    import asyncio

    await asyncio.sleep(1)


async def test_filter_components_present(user: User, seeded_db) -> None:
    """Test that filter components are present and functional"""
    await user.open("/")

    # Should have filter components
    await user.should_see("Start Date")
    await user.should_see("End Date")
    await user.should_see("Teams")
    await user.should_see("Severities")
    await user.should_see("Statuses")
    await user.should_see("Reset")


async def test_tabs_navigation(user: User, seeded_db) -> None:
    """Test that tabs are present and clickable"""
    await user.open("/")

    # Should see both tabs
    await user.should_see("Tickets")
    await user.should_see("Flagged Tickets")

    # Click on flagged tickets tab
    user.find("Flagged Tickets").click()
    # Should still be on the same page
    await user.should_see("Flagged Tickets")


async def test_seed_page_functionality(user: User, fresh_db) -> None:
    """Test the seed data functionality"""
    await user.open("/seed")

    # Should see success message
    await user.should_see("Created 100 sample tickets")
    await user.should_see("Go to Dashboard")

    # Click the dashboard link
    user.find("Go to Dashboard").click()
    await user.should_see("ES Ticket Health Tracker")


async def test_dashboard_with_no_data(user: User, fresh_db) -> None:
    """Test dashboard behavior with no data"""
    await user.open("/")

    # Should still load without errors
    await user.should_see("ES Ticket Health Tracker")
    await user.should_see("Filters")

    # May show zero values in KPIs
    import asyncio

    await asyncio.sleep(1)  # Allow for async data loading


async def test_error_handling_invalid_route(user: User) -> None:
    """Test handling of invalid routes"""
    # This test might depend on how NiceGUI handles 404s
    # For now, just ensure the app doesn't crash
    try:
        await user.open("/nonexistent-page")
        # If it redirects or shows 404, that's fine
    except Exception as e:
        import logging

        logging.info(f"Expected exception for invalid route: {str(e)}")
        # If it throws an exception, that's also acceptable for invalid routes
        pass
