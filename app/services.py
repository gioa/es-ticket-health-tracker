from typing import List, Dict, Optional, Tuple
from sqlmodel import select, func, and_, col
from datetime import datetime
from decimal import Decimal
import csv
from io import StringIO

from app.database import get_session
from app.models import (
    ESTicket,
    User,
    UserTicketFlag,
    FilterParams,
    KPIData,
    TimeSeriesPoint,
    StackedBarData,
    TeamTicketCount,
    TicketExportRow,
)


class TicketService:
    """Service for ticket data operations and analytics"""

    @staticmethod
    def get_filtered_tickets(filters: FilterParams) -> List[ESTicket]:
        """Get tickets based on filter parameters"""
        with get_session() as session:
            query = select(ESTicket)
            conditions = []

            # Date range filter
            if filters.date_start:
                conditions.append(ESTicket.created >= filters.date_start)
            if filters.date_end:
                conditions.append(ESTicket.created <= filters.date_end)

            # Team filter
            if filters.teams:
                conditions.append(col(ESTicket.eng_team).in_(filters.teams))

            # Severity filter
            if filters.severities:
                conditions.append(col(ESTicket.severity).in_(filters.severities))

            # Status filter
            if filters.statuses:
                conditions.append(col(ESTicket.status).in_(filters.statuses))

            if conditions:
                query = query.where(and_(*conditions))

            result = session.exec(query).all()
            return list(result)

    @staticmethod
    def get_kpi_data(filters: FilterParams) -> KPIData:
        """Calculate KPI metrics based on filters"""
        with get_session() as session:
            base_conditions = []

            # Apply date range to created date
            if filters.date_start:
                base_conditions.append(ESTicket.created >= filters.date_start)
            if filters.date_end:
                base_conditions.append(ESTicket.created <= filters.date_end)

            # Team filter
            if filters.teams:
                base_conditions.append(col(ESTicket.eng_team).in_(filters.teams))

            # Severity filter
            if filters.severities:
                base_conditions.append(col(ESTicket.severity).in_(filters.severities))

            # Status filter
            if filters.statuses:
                base_conditions.append(col(ESTicket.status).in_(filters.statuses))

            base_query = select(ESTicket)
            if base_conditions:
                base_query = base_query.where(and_(*base_conditions))

            tickets = session.exec(base_query).all()

            # Calculate metrics
            tickets_created = len(tickets)

            # Tickets mitigated (have mitigated_date set)
            tickets_mitigated = len([t for t in tickets if t.mitigated_date is not None])

            # Open tickets (not resolved)
            open_tickets = len([t for t in tickets if t.resolved_date is None])

            # Average time to resolve
            resolved_tickets = [t for t in tickets if t.time_to_resolve_hours is not None]
            avg_time_to_resolve_hours = None
            if resolved_tickets:
                total_hours_value = sum(
                    float(t.time_to_resolve_hours) for t in resolved_tickets if t.time_to_resolve_hours is not None
                )
                avg_hours = total_hours_value / len(resolved_tickets)
                avg_time_to_resolve_hours = Decimal(str(round(avg_hours, 2)))

            return KPIData(
                tickets_created=tickets_created,
                tickets_mitigated=tickets_mitigated,
                open_tickets=open_tickets,
                avg_time_to_resolve_hours=avg_time_to_resolve_hours,
            )

    @staticmethod
    def get_time_series_data(filters: FilterParams) -> List[TimeSeriesPoint]:
        """Get time series data for created vs mitigated vs resolved per day"""
        tickets = TicketService.get_filtered_tickets(filters)

        # Group tickets by date
        daily_data: Dict[str, Dict[str, int]] = {}

        for ticket in tickets:
            # Created count
            created_date = ticket.created.date().isoformat()
            if created_date not in daily_data:
                daily_data[created_date] = {"created": 0, "mitigated": 0, "resolved": 0}
            daily_data[created_date]["created"] += 1

            # Mitigated count
            if ticket.mitigated_date:
                mitigated_date = ticket.mitigated_date.date().isoformat()
                if mitigated_date not in daily_data:
                    daily_data[mitigated_date] = {"created": 0, "mitigated": 0, "resolved": 0}
                daily_data[mitigated_date]["mitigated"] += 1

            # Resolved count
            if ticket.resolved_date:
                resolved_date = ticket.resolved_date.date().isoformat()
                if resolved_date not in daily_data:
                    daily_data[resolved_date] = {"created": 0, "mitigated": 0, "resolved": 0}
                daily_data[resolved_date]["resolved"] += 1

        # Convert to list and sort by date
        result = []
        for date_str in sorted(daily_data.keys()):
            data = daily_data[date_str]
            result.append(
                TimeSeriesPoint(
                    date=date_str, created=data["created"], mitigated=data["mitigated"], resolved=data["resolved"]
                )
            )

        return result

    @staticmethod
    def get_stacked_bar_data(filters: FilterParams) -> List[StackedBarData]:
        """Get stacked bar chart data showing ticket count by status and severity"""
        tickets = TicketService.get_filtered_tickets(filters)

        # Group by status and count by severity
        status_severity_counts: Dict[str, Dict[str, int]] = {}

        for ticket in tickets:
            status = ticket.status
            severity = ticket.severity or "Unknown"

            if status not in status_severity_counts:
                status_severity_counts[status] = {}

            if severity not in status_severity_counts[status]:
                status_severity_counts[status][severity] = 0

            status_severity_counts[status][severity] += 1

        # Convert to list
        result = []
        for status, severity_counts in status_severity_counts.items():
            result.append(StackedBarData(status=status, severity_counts=severity_counts))

        return result

    @staticmethod
    def get_team_ticket_counts(filters: FilterParams) -> List[TeamTicketCount]:
        """Get ticket counts by engineering team (top teams)"""
        tickets = TicketService.get_filtered_tickets(filters)

        # Count by team
        team_counts: Dict[str, int] = {}

        for ticket in tickets:
            team = ticket.eng_team or "Unknown"
            team_counts[team] = team_counts.get(team, 0) + 1

        # Convert to list and sort by count descending
        result = []
        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True):
            result.append(TeamTicketCount(team=team, ticket_count=count))

        return result[:10]  # Top 10 teams

    @staticmethod
    def get_available_filter_values() -> Dict[str, List[str]]:
        """Get available values for each filter type"""
        with get_session() as session:
            # Get unique teams
            teams_query = select(ESTicket.eng_team).distinct().where(col(ESTicket.eng_team).isnot(None))
            teams = [t for t in session.exec(teams_query).all() if t]

            # Get unique severities
            severities_query = select(ESTicket.severity).distinct().where(col(ESTicket.severity).isnot(None))
            severities = [s for s in session.exec(severities_query).all() if s]

            # Get unique statuses
            statuses_query = select(ESTicket.status).distinct()
            statuses = list(session.exec(statuses_query).all())

            return {"teams": sorted(teams), "severities": sorted(severities), "statuses": sorted(statuses)}


class FlagService:
    """Service for managing ticket flags"""

    @staticmethod
    def get_or_create_user(username: str) -> User:
        """Get existing user or create new one"""
        with get_session() as session:
            user = session.exec(select(User).where(User.username == username)).first()
            if user is None:
                user = User(username=username, display_name=username)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    @staticmethod
    def flag_ticket(user_id: int, ticket_id: int, notes: Optional[str] = None) -> UserTicketFlag:
        """Flag a ticket for a user"""
        with get_session() as session:
            # Check if already flagged
            existing_flag = session.exec(
                select(UserTicketFlag).where(
                    and_(UserTicketFlag.user_id == user_id, UserTicketFlag.ticket_id == ticket_id)
                )
            ).first()

            if existing_flag is not None:
                return existing_flag

            # Create new flag
            flag = UserTicketFlag(user_id=user_id, ticket_id=ticket_id, notes=notes, flagged_at=datetime.utcnow())
            session.add(flag)
            session.commit()
            session.refresh(flag)
            return flag

    @staticmethod
    def unflag_ticket(user_id: int, ticket_id: int) -> bool:
        """Remove flag from a ticket"""
        with get_session() as session:
            flag = session.exec(
                select(UserTicketFlag).where(
                    and_(UserTicketFlag.user_id == user_id, UserTicketFlag.ticket_id == ticket_id)
                )
            ).first()

            if flag is not None:
                session.delete(flag)
                session.commit()
                return True
            return False

    @staticmethod
    def bulk_unflag_tickets(user_id: int, ticket_ids: List[int]) -> int:
        """Bulk unflag multiple tickets"""
        unflagged_count = 0
        for ticket_id in ticket_ids:
            if FlagService.unflag_ticket(user_id, ticket_id):
                unflagged_count += 1
        return unflagged_count

    @staticmethod
    def get_flagged_tickets(user_id: int, filters: FilterParams) -> List[Tuple[ESTicket, UserTicketFlag]]:
        """Get all flagged tickets for a user with optional filters"""
        with get_session() as session:
            query = (
                select(ESTicket, UserTicketFlag)
                .join(UserTicketFlag, col(ESTicket.id) == col(UserTicketFlag.ticket_id))
                .where(col(UserTicketFlag.user_id) == user_id)
            )

            conditions = []

            # Apply filters to ESTicket
            if filters.date_start:
                conditions.append(ESTicket.created >= filters.date_start)
            if filters.date_end:
                conditions.append(ESTicket.created <= filters.date_end)
            if filters.teams:
                conditions.append(col(ESTicket.eng_team).in_(filters.teams))
            if filters.severities:
                conditions.append(col(ESTicket.severity).in_(filters.severities))
            if filters.statuses:
                conditions.append(col(ESTicket.status).in_(filters.statuses))

            if conditions:
                query = query.where(and_(*conditions))

            results = session.exec(query).all()
            return [(ticket, flag) for ticket, flag in results]

    @staticmethod
    def is_ticket_flagged(user_id: int, ticket_id: int) -> bool:
        """Check if a ticket is flagged by a user"""
        with get_session() as session:
            flag = session.exec(
                select(UserTicketFlag).where(
                    and_(UserTicketFlag.user_id == user_id, UserTicketFlag.ticket_id == ticket_id)
                )
            ).first()
            return flag is not None


class ExportService:
    """Service for data export operations"""

    @staticmethod
    def export_flagged_tickets_csv(user_id: int, filters: FilterParams) -> str:
        """Export flagged tickets to CSV format"""
        flagged_tickets = FlagService.get_flagged_tickets(user_id, filters)

        # Prepare data for export
        export_data = []
        for ticket, flag in flagged_tickets:
            export_data.append(
                TicketExportRow(
                    key=ticket.key,
                    title=ticket.summary,
                    team=ticket.eng_team,
                    severity=ticket.severity,
                    status=ticket.status,
                    created=ticket.created.isoformat(),
                    updated=ticket.updated.isoformat(),
                    assignee=ticket.assignee,
                    time_to_resolve_hours=ticket.time_to_resolve_hours,
                    flagged_at=flag.flagged_at.isoformat(),
                    flag_notes=flag.notes,
                )
            )

        # Generate CSV
        output = StringIO()
        if export_data:
            fieldnames = export_data[0].model_fields.keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in export_data:
                writer.writerow(row.model_dump())

        return output.getvalue()


class SeedService:
    """Service for seeding test data"""

    @staticmethod
    def create_sample_tickets(count: int = 50) -> None:
        """Create sample tickets for development and testing"""
        with get_session() as session:
            import random
            from datetime import datetime, timedelta

            teams = ["Platform", "Data", "ML", "Security", "Infrastructure", "API"]
            severities = ["Critical", "High", "Medium", "Low"]
            statuses = ["Open", "In Progress", "Resolved", "Closed", "Blocked"]
            priorities = ["Highest", "High", "Medium", "Low", "Lowest"]

            base_date = datetime.utcnow() - timedelta(days=60)

            # Get existing max ticket number to avoid duplicates
            existing_max = session.exec(select(func.max(ESTicket.key))).first()

            start_num = 1000
            if existing_max:
                try:
                    # Extract number from key like "ES-1234"
                    existing_num = int(existing_max.split("-")[1]) if existing_max else 999
                    start_num = existing_num + 1
                except (IndexError, ValueError) as e:
                    import logging

                    logging.warning(f"Could not parse existing ticket key {existing_max}: {str(e)}")
                    pass

            for i in range(count):
                created_date = base_date + timedelta(
                    days=random.randint(0, 60), hours=random.randint(0, 23), minutes=random.randint(0, 59)
                )

                # Some tickets are mitigated/resolved
                mitigated_date = None
                resolved_date = None
                time_to_resolve_hours = None

                if random.random() < 0.6:  # 60% chance of mitigation
                    mitigated_date = created_date + timedelta(hours=random.randint(1, 48))

                if random.random() < 0.4:  # 40% chance of resolution
                    resolved_date = (mitigated_date or created_date) + timedelta(hours=random.randint(1, 72))
                    time_to_resolve_hours = Decimal(str((resolved_date - created_date).total_seconds() / 3600))

                ticket = ESTicket(
                    key=f"ES-{start_num + i}",
                    summary=f"Sample ticket {i + 1}: {random.choice(['Database performance', 'API timeout', 'Memory leak', 'Security issue', 'Data corruption'])}",
                    description=f"Detailed description for ticket {i + 1}",
                    status=random.choice(statuses),
                    type="Bug",
                    priority=random.choice(priorities),
                    created=created_date,
                    updated=created_date + timedelta(hours=random.randint(0, 24)),
                    assignee=f"user{random.randint(1, 10)}@company.com",
                    eng_team=random.choice(teams),
                    severity=random.choice(severities),
                    mitigated_date=mitigated_date,
                    resolved_date=resolved_date,
                    time_to_resolve_hours=time_to_resolve_hours,
                )
                session.add(ticket)

            session.commit()
