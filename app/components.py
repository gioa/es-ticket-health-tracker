from nicegui import ui
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models import FilterParams, ESTicket, KPIData, TimeSeriesPoint, StackedBarData, TeamTicketCount


class FilterState:
    """Global state management for filters"""

    def __init__(self):
        self.date_start: Optional[date] = date.today() - timedelta(days=30)
        self.date_end: Optional[date] = date.today()
        self.teams: List[str] = []
        self.severities: List[str] = []
        self.statuses: List[str] = []
        self.on_change_callbacks: List[Callable] = []

    def add_callback(self, callback: Callable) -> None:
        """Add callback to be called when filters change"""
        self.on_change_callbacks.append(callback)

    def notify_change(self) -> None:
        """Notify all callbacks that filters have changed"""
        for callback in self.on_change_callbacks:
            callback()

    def to_filter_params(self) -> FilterParams:
        """Convert to FilterParams model"""
        return FilterParams(
            date_start=datetime.combine(self.date_start, datetime.min.time()) if self.date_start else None,
            date_end=datetime.combine(self.date_end, datetime.max.time()) if self.date_end else None,
            teams=self.teams if self.teams else None,
            severities=self.severities if self.severities else None,
            statuses=self.statuses if self.statuses else None,
        )

    def from_url_params(self, params: Dict[str, Any]) -> None:
        """Update filters from URL parameters"""
        if "date_start" in params and params["date_start"]:
            try:
                self.date_start = datetime.fromisoformat(params["date_start"]).date()
            except ValueError as e:
                import logging

                logging.warning(f"Invalid date_start URL param: {params['date_start']} - {str(e)}")
                pass

        if "date_end" in params and params["date_end"]:
            try:
                self.date_end = datetime.fromisoformat(params["date_end"]).date()
            except ValueError as e:
                import logging

                logging.warning(f"Invalid date_end URL param: {params['date_end']} - {str(e)}")
                pass

        if "teams" in params and params["teams"]:
            self.teams = params["teams"].split(",") if isinstance(params["teams"], str) else params["teams"]

        if "severities" in params and params["severities"]:
            self.severities = (
                params["severities"].split(",") if isinstance(params["severities"], str) else params["severities"]
            )

        if "statuses" in params and params["statuses"]:
            self.statuses = params["statuses"].split(",") if isinstance(params["statuses"], str) else params["statuses"]

    def to_url_params(self) -> Dict[str, str]:
        """Convert to URL parameters"""
        params = {}

        if self.date_start:
            params["date_start"] = self.date_start.isoformat()
        if self.date_end:
            params["date_end"] = self.date_end.isoformat()
        if self.teams:
            params["teams"] = ",".join(self.teams)
        if self.severities:
            params["severities"] = ",".join(self.severities)
        if self.statuses:
            params["statuses"] = ",".join(self.statuses)

        return params


def create_topbar():
    """Create the application topbar with logo and avatar"""
    with ui.header().classes("bg-primary text-white shadow-lg"):
        with ui.row().classes("w-full items-center justify-between px-6 py-2"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("analytics").classes("text-2xl")
                ui.label("ES Ticket Health Tracker").classes("text-xl font-bold")

            # Avatar section
            with ui.row().classes("items-center gap-2"):
                ui.avatar("user", color="white", text_color="primary")
                ui.label("Admin User").classes("text-sm")


def create_filter_bar(filter_state: FilterState, available_values: Dict[str, List[str]]):
    """Create the global filter bar"""
    with ui.card().classes("w-full p-4 mb-4 shadow-md"):
        ui.label("Filters").classes("text-lg font-semibold mb-3")

        with ui.row().classes("w-full gap-4 items-end"):
            # Date range filters
            with ui.column().classes("gap-1"):
                ui.label("Start Date").classes("text-sm font-medium text-gray-700")
                start_value = filter_state.date_start.isoformat() if filter_state.date_start else None
                date_start_input = ui.date(value=start_value).classes("min-w-36")

                def update_start_date(value):
                    if value.value:
                        try:
                            filter_state.date_start = datetime.fromisoformat(value.value).date()
                        except (ValueError, TypeError) as e:
                            import logging

                            logging.warning(f"Invalid start date format: {value.value} - {str(e)}")
                            filter_state.date_start = None
                    else:
                        filter_state.date_start = None
                    filter_state.notify_change()

                date_start_input.on("update:model-value", update_start_date)

            with ui.column().classes("gap-1"):
                ui.label("End Date").classes("text-sm font-medium text-gray-700")
                end_value = filter_state.date_end.isoformat() if filter_state.date_end else None
                date_end_input = ui.date(value=end_value).classes("min-w-36")

                def update_end_date(value):
                    if value.value:
                        try:
                            filter_state.date_end = datetime.fromisoformat(value.value).date()
                        except (ValueError, TypeError) as e:
                            import logging

                            logging.warning(f"Invalid end date format: {value.value} - {str(e)}")
                            filter_state.date_end = None
                    else:
                        filter_state.date_end = None
                    filter_state.notify_change()

                date_end_input.on("update:model-value", update_end_date)

            # Team filter
            with ui.column().classes("gap-1"):
                ui.label("Teams").classes("text-sm font-medium text-gray-700")
                team_select = ui.select(
                    options=available_values.get("teams", []), multiple=True, value=filter_state.teams
                ).classes("min-w-48")

                def update_teams(value):
                    filter_state.teams = value.value or []
                    filter_state.notify_change()

                team_select.on("update:model-value", update_teams)

            # Severity filter
            with ui.column().classes("gap-1"):
                ui.label("Severities").classes("text-sm font-medium text-gray-700")
                severity_select = ui.select(
                    options=available_values.get("severities", []), multiple=True, value=filter_state.severities
                ).classes("min-w-36")

                def update_severities(value):
                    filter_state.severities = value.value or []
                    filter_state.notify_change()

                severity_select.on("update:model-value", update_severities)

            # Status filter
            with ui.column().classes("gap-1"):
                ui.label("Statuses").classes("text-sm font-medium text-gray-700")
                status_select = ui.select(
                    options=available_values.get("statuses", []), multiple=True, value=filter_state.statuses
                ).classes("min-w-36")

                def update_statuses(value):
                    filter_state.statuses = value.value or []
                    filter_state.notify_change()

                status_select.on("update:model-value", update_statuses)

            # Reset button
            def reset_filters():
                filter_state.date_start = date.today() - timedelta(days=30)
                filter_state.date_end = date.today()
                filter_state.teams = []
                filter_state.severities = []
                filter_state.statuses = []

                # Update UI components
                start_val = filter_state.date_start.isoformat() if filter_state.date_start else None
                end_val = filter_state.date_end.isoformat() if filter_state.date_end else None
                date_start_input.set_value(start_val)
                date_end_input.set_value(end_val)
                team_select.set_value([])
                severity_select.set_value([])
                status_select.set_value([])

                filter_state.notify_change()

            ui.button("Reset", on_click=reset_filters).classes("bg-gray-500 text-white px-4 py-2").props("outline")


def create_kpi_card(
    title: str, value: str, change: str = "", positive: bool = True, sparkline_data: Optional[List[int]] = None
):
    """Create a KPI card with optional sparkline"""
    with ui.card().classes("p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-56"):
        ui.label(title).classes("text-sm text-gray-500 uppercase tracking-wider mb-2")
        ui.label(value).classes("text-3xl font-bold text-gray-800 mb-2")

        if change:
            change_color = "text-green-500" if positive else "text-red-500"
            ui.label(change).classes(f"text-sm {change_color}")

        # Simple sparkline using CSS
        if sparkline_data and len(sparkline_data) > 1:
            max_val = max(sparkline_data) if max(sparkline_data) > 0 else 1
            with ui.row().classes("mt-3 gap-1 items-end h-8"):
                for val in sparkline_data[-10:]:  # Last 10 data points
                    height = int((val / max_val) * 24) if max_val > 0 else 1
                    ui.element("div").classes("w-1 bg-blue-400 rounded-t").style(f"height: {height}px")


def create_kpi_section(kpi_data: KPIData):
    """Create the KPI cards section"""
    with ui.row().classes("gap-4 w-full mb-6"):
        create_kpi_card(
            "Tickets Created",
            str(kpi_data.tickets_created),
            sparkline_data=[kpi_data.tickets_created] * 10,  # Placeholder
        )

        create_kpi_card(
            "Tickets Mitigated",
            str(kpi_data.tickets_mitigated),
            sparkline_data=[kpi_data.tickets_mitigated] * 10,  # Placeholder
        )

        create_kpi_card(
            "Open Tickets",
            str(kpi_data.open_tickets),
            sparkline_data=[kpi_data.open_tickets] * 10,  # Placeholder
        )

        avg_time_str = f"{kpi_data.avg_time_to_resolve_hours:.1f}h" if kpi_data.avg_time_to_resolve_hours else "N/A"
        create_kpi_card(
            "Avg Time to Resolve",
            avg_time_str,
            sparkline_data=[int(kpi_data.avg_time_to_resolve_hours or 0)] * 10,  # Placeholder
        )


def create_time_series_chart(data: List[TimeSeriesPoint]):
    """Create time series chart for created vs mitigated vs resolved"""
    if not data:
        ui.label("No data available").classes("text-center text-gray-500 p-8")
        return

    # Prepare data for ECharts
    dates = [point.date for point in data]
    created_data = [point.created for point in data]
    mitigated_data = [point.mitigated for point in data]
    resolved_data = [point.resolved for point in data]

    chart_options = {
        "title": {"text": "Tickets Created vs. Mitigated vs. Resolved per Day"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Created", "Mitigated", "Resolved"]},
        "xAxis": {"type": "category", "data": dates},
        "yAxis": {"type": "value"},
        "series": [
            {"name": "Created", "type": "line", "data": created_data, "itemStyle": {"color": "#3b82f6"}},
            {"name": "Mitigated", "type": "line", "data": mitigated_data, "itemStyle": {"color": "#10b981"}},
            {"name": "Resolved", "type": "line", "data": resolved_data, "itemStyle": {"color": "#f59e0b"}},
        ],
    }

    ui.echart(chart_options).classes("w-full h-80")


def create_stacked_bar_chart(data: List[StackedBarData]):
    """Create stacked bar chart for status and severity"""
    if not data:
        ui.label("No data available").classes("text-center text-gray-500 p-8")
        return

    # Prepare data for ECharts
    statuses = [item.status for item in data]

    # Get all unique severities
    all_severities = set()
    for item in data:
        all_severities.update(item.severity_counts.keys())
    all_severities = sorted(list(all_severities))

    # Create series data
    series = []
    colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"]

    for i, severity in enumerate(all_severities):
        series_data = [item.severity_counts.get(severity, 0) for item in data]
        series.append(
            {
                "name": severity,
                "type": "bar",
                "stack": "total",
                "data": series_data,
                "itemStyle": {"color": colors[i % len(colors)]},
            }
        )

    chart_options = {
        "title": {"text": "Ticket Count by Status and Severity"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": all_severities},
        "xAxis": {"type": "category", "data": statuses},
        "yAxis": {"type": "value"},
        "series": series,
    }

    ui.echart(chart_options).classes("w-full h-80")


def create_team_bar_chart(data: List[TeamTicketCount]):
    """Create vertical bar chart for top teams with most tickets"""
    if not data:
        ui.label("No data available").classes("text-center text-gray-500 p-8")
        return

    # Prepare data for ECharts
    teams = [item.team for item in data]
    counts = [item.ticket_count for item in data]

    chart_options = {
        "title": {"text": "Top Engineering Teams by Ticket Count"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": teams},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": counts, "itemStyle": {"color": "#3b82f6"}}],
    }

    ui.echart(chart_options).classes("w-full h-80")


def create_simple_tickets_table(tickets: List[ESTicket]) -> ui.table:
    """Create a simple tickets table"""

    def format_time_to_resolve(hours: Optional[Decimal]) -> str:
        """Format time to resolve in human-readable format"""
        if hours is None:
            return "N/A"

        total_hours = float(hours)
        if total_hours < 1:
            return f"{total_hours * 60:.0f}m"
        elif total_hours < 24:
            return f"{total_hours:.1f}h"
        else:
            days = total_hours / 24
            return f"{days:.1f}d"

    # Prepare table data
    rows = []
    for ticket in tickets:
        rows.append(
            {
                "key": ticket.key,
                "title": ticket.summary,
                "team": ticket.eng_team or "N/A",
                "severity": ticket.severity or "N/A",
                "status": ticket.status,
                "created": ticket.created.strftime("%Y-%m-%d %H:%M"),
                "updated": ticket.updated.strftime("%Y-%m-%d %H:%M"),
                "assignee": ticket.assignee or "Unassigned",
                "timeToResolve": format_time_to_resolve(ticket.time_to_resolve_hours),
                "ticket_id": ticket.id,
            }
        )

    columns = [
        {"name": "key", "label": "Key", "field": "key", "sortable": True, "align": "left"},
        {"name": "title", "label": "Title", "field": "title", "sortable": True, "align": "left"},
        {"name": "team", "label": "Team", "field": "team", "sortable": True, "align": "left"},
        {"name": "severity", "label": "Severity", "field": "severity", "sortable": True, "align": "center"},
        {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
        {"name": "created", "label": "Created", "field": "created", "sortable": True, "align": "center"},
        {"name": "updated", "label": "Updated", "field": "updated", "sortable": True, "align": "center"},
        {"name": "assignee", "label": "Assignee", "field": "assignee", "sortable": True, "align": "left"},
        {
            "name": "timeToResolve",
            "label": "Time to Resolve",
            "field": "timeToResolve",
            "sortable": True,
            "align": "center",
        },
    ]

    table = ui.table(columns=columns, rows=rows, row_key="ticket_id", pagination=20).classes("w-full")

    return table


def create_flagged_tickets_table(
    tickets_and_flags: List[tuple], selected_tickets: List[int], on_selection_change: Callable[[List[int]], None]
):
    """Create table for flagged tickets with bulk actions"""

    # Prepare table data
    rows = []
    for ticket, flag in tickets_and_flags:
        rows.append(
            {
                "key": ticket.key,
                "title": ticket.summary,
                "team": ticket.eng_team or "N/A",
                "severity": ticket.severity or "N/A",
                "status": ticket.status,
                "created": ticket.created.strftime("%Y-%m-%d %H:%M"),
                "flagged_at": flag.flagged_at.strftime("%Y-%m-%d %H:%M"),
                "notes": flag.notes or "",
                "ticket_id": ticket.id,
                "assignee": ticket.assignee or "Unassigned",
            }
        )

    columns = [
        {"name": "key", "label": "Key", "field": "key", "sortable": True, "align": "left"},
        {"name": "title", "label": "Title", "field": "title", "sortable": True, "align": "left"},
        {"name": "team", "label": "Team", "field": "team", "sortable": True, "align": "left"},
        {"name": "severity", "label": "Severity", "field": "severity", "sortable": True, "align": "center"},
        {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
        {"name": "created", "label": "Created", "field": "created", "sortable": True, "align": "center"},
        {"name": "flagged_at", "label": "Flagged At", "field": "flagged_at", "sortable": True, "align": "center"},
        {"name": "notes", "label": "Notes", "field": "notes", "sortable": False, "align": "left"},
        {"name": "assignee", "label": "Assignee", "field": "assignee", "sortable": True, "align": "left"},
    ]

    table = ui.table(columns=columns, rows=rows, row_key="ticket_id", selection="multiple", pagination=20).classes(
        "w-full"
    )

    # Handle selection changes
    def update_selection():
        selected = table.selected
        ticket_ids = [row["ticket_id"] for row in selected] if selected else []
        on_selection_change(ticket_ids)

    table.on("selection", update_selection)

    return table
