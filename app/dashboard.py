from nicegui import ui, app
from datetime import datetime
from app.dashboard_service import DashboardService
from app.models import TicketStatus, TicketPriority, TicketCategory
import logging

logger = logging.getLogger(__name__)


def create():
    """Create dashboard module with routing"""

    # Apply modern theme
    ui.colors(
        primary="#2563eb",  # Professional blue
        secondary="#64748b",  # Subtle gray
        accent="#10b981",  # Success green
        positive="#10b981",
        negative="#ef4444",  # Error red
        warning="#f59e0b",  # Warning amber
        info="#3b82f6",  # Info blue
    )

    @ui.page("/")
    def dashboard_page():
        """Main dashboard page with ticket table and statistics"""
        create_dashboard_ui()


def create_dashboard_ui():
    """Create the main dashboard UI"""

    # Page header
    with ui.row().classes("w-full justify-between items-center mb-6"):
        ui.label("Ticket Dashboard").classes("text-3xl font-bold text-gray-800")
        ui.button("Refresh Data", on_click=lambda: refresh_dashboard(), icon="refresh").classes(
            "bg-primary text-white px-4 py-2"
        )

    # Statistics cards
    stats_container = ui.row().classes("w-full gap-4 mb-6")
    create_stats_cards(stats_container)

    # Filters section
    filters_container = ui.card().classes("w-full p-4 mb-4")
    with filters_container:
        ui.label("Filters").classes("text-lg font-semibold mb-3")
        create_filters_ui()

    # Main tickets table
    table_container = ui.card().classes("w-full p-4")
    with table_container:
        ui.label("Tickets").classes("text-lg font-semibold mb-4")
        create_tickets_table()


def create_stats_cards(container):
    """Create statistics cards for dashboard overview"""
    try:
        stats = DashboardService.get_dashboard_stats()

        with container:
            # Total tickets card
            with ui.card().classes("p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-48"):
                ui.label("Total Tickets").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(stats["total_tickets"])).classes("text-3xl font-bold text-gray-800 mt-2")

            # Open tickets card
            open_count = stats["status_breakdown"].get("open", 0)
            with ui.card().classes("p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-48"):
                ui.label("Open Tickets").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(open_count)).classes("text-3xl font-bold text-blue-600 mt-2")

            # In progress card
            in_progress = stats["status_breakdown"].get("in_progress", 0)
            with ui.card().classes("p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-48"):
                ui.label("In Progress").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(in_progress)).classes("text-3xl font-bold text-yellow-600 mt-2")

            # Resolved tickets card
            resolved = stats["status_breakdown"].get("resolved", 0)
            with ui.card().classes("p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-48"):
                ui.label("Resolved").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(resolved)).classes("text-3xl font-bold text-green-600 mt-2")

            # Average resolution time card
            avg_hours = stats.get("avg_resolution_hours")
            avg_display = f"{avg_hours:.1f}h" if avg_hours and avg_hours > 0 else "N/A"
            with ui.card().classes("p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow min-w-48"):
                ui.label("Avg Resolution Time").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(avg_display).classes("text-3xl font-bold text-purple-600 mt-2")

    except Exception as e:
        logger.error(f"Error loading statistics: {str(e)}")
        ui.notify(f"Error loading statistics: {str(e)}", type="negative")


def create_filters_ui():
    """Create filters for ticket table"""
    with ui.row().classes("w-full gap-4 flex-wrap"):
        # Status filter
        status_options = ["All Statuses"] + [status.value.replace("_", " ").title() for status in TicketStatus]
        status_select = ui.select(options=status_options, value="All Statuses", label="Status").classes("min-w-40")

        # Priority filter
        priority_options = ["All Priorities"] + [priority.value.title() for priority in TicketPriority]
        priority_select = ui.select(options=priority_options, value="All Priorities", label="Priority").classes(
            "min-w-40"
        )

        # Category filter
        category_options = ["All Categories"] + [
            category.value.replace("_", " ").title() for category in TicketCategory
        ]
        category_select = ui.select(options=category_options, value="All Categories", label="Category").classes(
            "min-w-40"
        )

        # Search input
        search_input = ui.input(label="Search", placeholder="Search in title, description, tags...").classes("min-w-64")

        # Apply filters button
        ui.button(
            "Apply Filters",
            on_click=lambda: apply_filters(
                status_select.value, priority_select.value, category_select.value, search_input.value
            ),
            icon="filter_list",
        ).classes("bg-secondary text-white px-4 py-2")

        # Clear filters button
        ui.button(
            "Clear",
            on_click=lambda: clear_filters(status_select, priority_select, category_select, search_input),
            icon="clear",
        ).props("outline").classes("px-4 py-2")


def create_tickets_table():
    """Create the main tickets table with actions"""
    try:
        tickets = DashboardService.get_all_tickets()

        # Prepare table data
        columns = [
            {"name": "id", "label": "ID", "field": "id", "sortable": True, "align": "left"},
            {"name": "title", "label": "Title", "field": "title", "sortable": True, "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "sortable": True},
            {"name": "priority", "label": "Priority", "field": "priority", "sortable": True},
            {"name": "category", "label": "Category", "field": "category", "sortable": True},
            {"name": "creator_name", "label": "Creator", "field": "creator_name", "sortable": True},
            {"name": "assignee_name", "label": "Assignee", "field": "assignee_name", "sortable": True},
            {"name": "created_at", "label": "Created", "field": "created_at", "sortable": True},
        ]

        # Format ticket data for display
        rows = []
        for ticket in tickets:
            # Format datetime for display
            created_date = datetime.fromisoformat(ticket.created_at).strftime("%Y-%m-%d %H:%M")

            # Format status and priority for display
            status_display = ticket.status.value.replace("_", " ").title()
            priority_display = ticket.priority.value.title()
            category_display = ticket.category.value.replace("_", " ").title()

            rows.append(
                {
                    "id": ticket.id,
                    "title": ticket.title,
                    "status": status_display,
                    "priority": priority_display,
                    "category": category_display,
                    "creator_name": ticket.creator_name,
                    "assignee_name": ticket.assignee_name or "Unassigned",
                    "created_at": created_date,
                }
            )

        # Create table
        table = ui.table(columns=columns, rows=rows, pagination=20).classes("w-full")

        app.storage.client["tickets_table"] = table

        # Add action buttons below table
        with ui.row().classes("gap-2 mt-4"):
            ui.button("Refresh Table", on_click=lambda: refresh_tickets_table(), icon="refresh").classes(
                "bg-secondary text-white px-4 py-2"
            )

    except Exception as e:
        logger.error(f"Error loading tickets: {str(e)}")
        ui.notify(f"Error loading tickets: {str(e)}", type="negative")


def apply_filters(status_filter, priority_filter, category_filter, search_term):
    """Apply filters to tickets table"""
    try:
        # Convert filter values back to enums or None
        status = None
        if status_filter != "All Statuses":
            for s in TicketStatus:
                if s.value.replace("_", " ").title() == status_filter:
                    status = s
                    break

        priority = None
        if priority_filter != "All Priorities":
            for p in TicketPriority:
                if p.value.title() == priority_filter:
                    priority = p
                    break

        category = None
        if category_filter != "All Categories":
            for c in TicketCategory:
                if c.value.replace("_", " ").title() == category_filter:
                    category = c
                    break

        # Convert empty strings to None
        search_term = search_term.strip() if search_term and search_term.strip() else None

        filtered_tickets = DashboardService.filter_tickets(
            status=status, priority=priority, category=category, search_term=search_term
        )

        # Update table with filtered data
        refresh_tickets_table(filtered_tickets)
        ui.notify(f"Found {len(filtered_tickets)} tickets", type="info")

    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}")
        ui.notify(f"Error applying filters: {str(e)}", type="negative")


def clear_filters(status_select, priority_select, category_select, search_input):
    """Clear all filters and refresh table"""
    status_select.set_value("All Statuses")
    priority_select.set_value("All Priorities")
    category_select.set_value("All Categories")
    search_input.set_value("")
    refresh_dashboard()


def refresh_tickets_table(tickets=None):
    """Refresh the tickets table with new data"""
    if tickets is None:
        tickets = DashboardService.get_all_tickets()

    # Get stored table reference
    table = app.storage.client.get("tickets_table")
    if table:
        # Format ticket data for display
        rows = []
        for ticket in tickets:
            created_date = datetime.fromisoformat(ticket.created_at).strftime("%Y-%m-%d %H:%M")
            status_display = ticket.status.value.replace("_", " ").title()
            priority_display = ticket.priority.value.title()
            category_display = ticket.category.value.replace("_", " ").title()

            rows.append(
                {
                    "id": ticket.id,
                    "title": ticket.title,
                    "status": status_display,
                    "priority": priority_display,
                    "category": category_display,
                    "creator_name": ticket.creator_name,
                    "assignee_name": ticket.assignee_name or "Unassigned",
                    "created_at": created_date,
                }
            )

        table.rows = rows
        table.update()


def refresh_dashboard():
    """Refresh the entire dashboard by navigating to the same page"""
    ui.navigate.to("/", new_tab=False)
