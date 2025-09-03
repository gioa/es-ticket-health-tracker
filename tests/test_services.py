import pytest
from datetime import datetime, timedelta

from app.database import reset_db
from app.services import TicketService, FlagService, ExportService, SeedService
from app.models import FilterParams, ESTicket, UserTicketFlag


@pytest.fixture
def fresh_db():
    """Reset database for each test"""
    reset_db()
    yield
    reset_db()


@pytest.fixture
def sample_tickets(fresh_db):
    """Create sample tickets for testing"""
    SeedService.create_sample_tickets(20)
    return TicketService.get_filtered_tickets(FilterParams())


@pytest.fixture
def sample_user(fresh_db):
    """Create sample user for testing"""
    return FlagService.get_or_create_user("testuser")


class TestTicketService:
    """Test ticket service functionality"""

    def test_get_filtered_tickets_no_filters(self, sample_tickets):
        """Test getting all tickets with no filters"""
        result = TicketService.get_filtered_tickets(FilterParams())
        assert len(result) == 20
        assert all(isinstance(ticket, ESTicket) for ticket in result)

    def test_get_filtered_tickets_date_range(self, sample_tickets):
        """Test filtering tickets by date range"""
        # Filter to last 7 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        filters = FilterParams(date_start=start_date, date_end=end_date)
        result = TicketService.get_filtered_tickets(filters)

        for ticket in result:
            assert start_date <= ticket.created <= end_date

    def test_get_filtered_tickets_by_team(self, sample_tickets):
        """Test filtering tickets by team"""
        # Get available teams first
        available_values = TicketService.get_available_filter_values()
        teams = available_values["teams"]

        if teams:
            selected_team = teams[0]
            filters = FilterParams(teams=[selected_team])
            result = TicketService.get_filtered_tickets(filters)

            for ticket in result:
                assert ticket.eng_team == selected_team

    def test_get_filtered_tickets_by_severity(self, sample_tickets):
        """Test filtering tickets by severity"""
        available_values = TicketService.get_available_filter_values()
        severities = available_values["severities"]

        if severities:
            selected_severity = severities[0]
            filters = FilterParams(severities=[selected_severity])
            result = TicketService.get_filtered_tickets(filters)

            for ticket in result:
                assert ticket.severity == selected_severity

    def test_get_filtered_tickets_by_status(self, sample_tickets):
        """Test filtering tickets by status"""
        available_values = TicketService.get_available_filter_values()
        statuses = available_values["statuses"]

        if statuses:
            selected_status = statuses[0]
            filters = FilterParams(statuses=[selected_status])
            result = TicketService.get_filtered_tickets(filters)

            for ticket in result:
                assert ticket.status == selected_status

    def test_get_filtered_tickets_multiple_filters(self, sample_tickets):
        """Test filtering with multiple criteria"""
        available_values = TicketService.get_available_filter_values()

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        filters = FilterParams(
            date_start=start_date,
            date_end=end_date,
            teams=available_values["teams"][:2] if available_values["teams"] else None,
            severities=available_values["severities"][:2] if available_values["severities"] else None,
        )

        result = TicketService.get_filtered_tickets(filters)

        for ticket in result:
            assert start_date <= ticket.created <= end_date
            if filters.teams:
                assert ticket.eng_team in filters.teams
            if filters.severities:
                assert ticket.severity in filters.severities

    def test_get_kpi_data(self, sample_tickets):
        """Test KPI data calculation"""
        filters = FilterParams()
        result = TicketService.get_kpi_data(filters)

        assert result.tickets_created >= 0
        assert result.tickets_mitigated >= 0
        assert result.open_tickets >= 0
        assert result.avg_time_to_resolve_hours is None or result.avg_time_to_resolve_hours >= 0

        # Basic validation - created should be >= mitigated
        assert result.tickets_created >= result.tickets_mitigated

    def test_get_kpi_data_with_filters(self, sample_tickets):
        """Test KPI calculation with filters applied"""
        # Test with date filter
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        filters = FilterParams(date_start=start_date, date_end=end_date)
        result = TicketService.get_kpi_data(filters)

        # Should get some results or zero (depending on sample data dates)
        assert result.tickets_created >= 0
        assert result.tickets_mitigated >= 0
        assert result.open_tickets >= 0

    def test_get_time_series_data(self, sample_tickets):
        """Test time series data generation"""
        filters = FilterParams()
        result = TicketService.get_time_series_data(filters)

        assert isinstance(result, list)
        for point in result:
            assert hasattr(point, "date")
            assert hasattr(point, "created")
            assert hasattr(point, "mitigated")
            assert hasattr(point, "resolved")
            assert point.created >= 0
            assert point.mitigated >= 0
            assert point.resolved >= 0

    def test_get_stacked_bar_data(self, sample_tickets):
        """Test stacked bar chart data"""
        filters = FilterParams()
        result = TicketService.get_stacked_bar_data(filters)

        assert isinstance(result, list)
        for item in result:
            assert hasattr(item, "status")
            assert hasattr(item, "severity_counts")
            assert isinstance(item.severity_counts, dict)
            # All counts should be positive
            assert all(count >= 0 for count in item.severity_counts.values())

    def test_get_team_ticket_counts(self, sample_tickets):
        """Test team ticket count data"""
        filters = FilterParams()
        result = TicketService.get_team_ticket_counts(filters)

        assert isinstance(result, list)
        assert len(result) <= 10  # Should return top 10

        for item in result:
            assert hasattr(item, "team")
            assert hasattr(item, "ticket_count")
            assert item.ticket_count > 0

        # Should be sorted by count descending
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i].ticket_count >= result[i + 1].ticket_count

    def test_get_available_filter_values(self, sample_tickets):
        """Test getting available filter values"""
        result = TicketService.get_available_filter_values()

        assert "teams" in result
        assert "severities" in result
        assert "statuses" in result

        assert isinstance(result["teams"], list)
        assert isinstance(result["severities"], list)
        assert isinstance(result["statuses"], list)

        # Should have some values from sample data
        assert len(result["teams"]) > 0
        assert len(result["severities"]) > 0
        assert len(result["statuses"]) > 0


class TestFlagService:
    """Test flag service functionality"""

    def test_get_or_create_user_new(self, fresh_db):
        """Test creating new user"""
        username = "newuser"
        user = FlagService.get_or_create_user(username)

        assert user.username == username
        assert user.display_name == username
        assert user.id is not None

    def test_get_or_create_user_existing(self, sample_user):
        """Test getting existing user"""
        username = sample_user.username
        user = FlagService.get_or_create_user(username)

        assert user.id == sample_user.id
        assert user.username == username

    def test_flag_ticket(self, sample_user, sample_tickets):
        """Test flagging a ticket"""
        ticket = sample_tickets[0]
        if ticket.id is None:
            pytest.skip("Ticket ID is None")

        flag = FlagService.flag_ticket(sample_user.id, ticket.id, "Test note")

        assert flag.user_id == sample_user.id
        assert flag.ticket_id == ticket.id
        assert flag.notes == "Test note"
        assert flag.flagged_at is not None

    def test_flag_ticket_duplicate(self, sample_user, sample_tickets):
        """Test flagging same ticket twice returns existing flag"""
        ticket = sample_tickets[0]
        if ticket.id is None:
            pytest.skip("Ticket ID is None")

        flag1 = FlagService.flag_ticket(sample_user.id, ticket.id)
        flag2 = FlagService.flag_ticket(sample_user.id, ticket.id)

        assert flag1.id == flag2.id

    def test_unflag_ticket(self, sample_user, sample_tickets):
        """Test unflagging a ticket"""
        ticket = sample_tickets[0]
        if ticket.id is None:
            pytest.skip("Ticket ID is None")

        # First flag the ticket
        FlagService.flag_ticket(sample_user.id, ticket.id)

        # Then unflag it
        result = FlagService.unflag_ticket(sample_user.id, ticket.id)
        assert result is True

        # Try unflagging again - should return False
        result = FlagService.unflag_ticket(sample_user.id, ticket.id)
        assert result is False

    def test_bulk_unflag_tickets(self, sample_user, sample_tickets):
        """Test bulk unflagging tickets"""
        # Flag multiple tickets
        ticket_ids = []
        for ticket in sample_tickets[:3]:
            if ticket.id is not None:
                FlagService.flag_ticket(sample_user.id, ticket.id)
                ticket_ids.append(ticket.id)

        if not ticket_ids:
            pytest.skip("No valid ticket IDs")

        # Bulk unflag
        count = FlagService.bulk_unflag_tickets(sample_user.id, ticket_ids)
        assert count == len(ticket_ids)

    def test_get_flagged_tickets(self, sample_user, sample_tickets):
        """Test getting flagged tickets"""
        # Flag some tickets
        flagged_count = 0
        for ticket in sample_tickets[:5]:
            if ticket.id is not None:
                FlagService.flag_ticket(sample_user.id, ticket.id, f"Note for {ticket.key}")
                flagged_count += 1

        if flagged_count == 0:
            pytest.skip("No tickets were flagged")

        # Get flagged tickets
        filters = FilterParams()
        result = FlagService.get_flagged_tickets(sample_user.id, filters)

        assert len(result) == flagged_count
        for ticket, flag in result:
            assert isinstance(ticket, ESTicket)
            assert isinstance(flag, UserTicketFlag)
            assert flag.user_id == sample_user.id

    def test_get_flagged_tickets_with_filters(self, sample_user, sample_tickets):
        """Test getting flagged tickets with filters applied"""
        # Flag a ticket
        ticket = sample_tickets[0]
        if ticket.id is None:
            pytest.skip("Ticket ID is None")

        FlagService.flag_ticket(sample_user.id, ticket.id)

        # Test with team filter
        if ticket.eng_team:
            filters = FilterParams(teams=[ticket.eng_team])
            result = FlagService.get_flagged_tickets(sample_user.id, filters)

            assert len(result) >= 1
            found_ticket = any(t.id == ticket.id for t, f in result)
            assert found_ticket

    def test_is_ticket_flagged(self, sample_user, sample_tickets):
        """Test checking if ticket is flagged"""
        ticket = sample_tickets[0]
        if ticket.id is None:
            pytest.skip("Ticket ID is None")

        # Initially not flagged
        assert not FlagService.is_ticket_flagged(sample_user.id, ticket.id)

        # Flag the ticket
        FlagService.flag_ticket(sample_user.id, ticket.id)

        # Now should be flagged
        assert FlagService.is_ticket_flagged(sample_user.id, ticket.id)

        # Unflag
        FlagService.unflag_ticket(sample_user.id, ticket.id)

        # Should not be flagged anymore
        assert not FlagService.is_ticket_flagged(sample_user.id, ticket.id)


class TestExportService:
    """Test export service functionality"""

    def test_export_flagged_tickets_csv_empty(self, sample_user, fresh_db):
        """Test CSV export with no flagged tickets"""
        filters = FilterParams()
        result = ExportService.export_flagged_tickets_csv(sample_user.id, filters)

        assert isinstance(result, str)
        # Should contain headers even with no data
        lines = result.strip().split("\n")
        assert len(lines) >= 1  # At least header row

    def test_export_flagged_tickets_csv_with_data(self, sample_user, sample_tickets):
        """Test CSV export with flagged tickets"""
        # Flag some tickets
        flagged_count = 0
        for ticket in sample_tickets[:3]:
            if ticket.id is not None:
                FlagService.flag_ticket(sample_user.id, ticket.id, f"Export test note {ticket.key}")
                flagged_count += 1

        if flagged_count == 0:
            pytest.skip("No tickets were flagged")

        filters = FilterParams()
        result = ExportService.export_flagged_tickets_csv(sample_user.id, filters)

        assert isinstance(result, str)
        lines = result.strip().split("\n")

        # Should have header + data rows
        assert len(lines) == flagged_count + 1

        # Check header contains expected columns
        header = lines[0]
        assert "key" in header
        assert "title" in header
        assert "team" in header
        assert "severity" in header
        assert "status" in header
        assert "flagged_at" in header
        assert "flag_notes" in header


class TestSeedService:
    """Test seed service functionality"""

    def test_create_sample_tickets(self, fresh_db):
        """Test creating sample tickets"""
        count = 10
        SeedService.create_sample_tickets(count)

        # Verify tickets were created
        filters = FilterParams()
        tickets = TicketService.get_filtered_tickets(filters)

        assert len(tickets) == count

        # Verify ticket properties
        for ticket in tickets:
            assert ticket.key.startswith("ES-")
            assert ticket.summary
            assert ticket.status
            assert ticket.created
            assert ticket.updated
            assert ticket.eng_team in ["Platform", "Data", "ML", "Security", "Infrastructure", "API"]
            assert ticket.severity in ["Critical", "High", "Medium", "Low"]

    def test_create_sample_tickets_multiple_calls(self, fresh_db):
        """Test creating sample tickets with multiple calls"""
        # Create first batch
        SeedService.create_sample_tickets(5)

        # Create second batch
        SeedService.create_sample_tickets(3)

        # Should have total of 8 tickets
        filters = FilterParams()
        tickets = TicketService.get_filtered_tickets(filters)

        assert len(tickets) == 8
