from nicegui import ui
from typing import Dict, Any, List, Optional
from nicegui.elements.column import Column
import asyncio
from datetime import datetime

from app.services import TicketService, FlagService, ExportService, SeedService
from app.components import (
    FilterState,
    create_topbar,
    create_filter_bar,
    create_kpi_section,
    create_time_series_chart,
    create_stacked_bar_chart,
    create_team_bar_chart,
    create_simple_tickets_table,
    create_flagged_tickets_table,
)


class DashboardState:
    """Global dashboard state management"""

    def __init__(self):
        self.filter_state = FilterState()
        self.current_user_id = 1  # Placeholder - in real app would come from auth
        self.selected_flagged_tickets: List[int] = []

        # Refreshable components
        self.kpi_container: Optional[Column] = None
        self.charts_container: Optional[Column] = None
        self.tickets_container: Optional[Column] = None
        self.flagged_container: Optional[Column] = None

        # Setup filter change callback
        self.filter_state.add_callback(self.refresh_dashboard)

    def refresh_dashboard(self):
        """Refresh all dashboard components when filters change"""
        if self.kpi_container:
            self.refresh_kpis()
        if self.charts_container:
            self.refresh_charts()
        if self.tickets_container:
            self.refresh_tickets_tab()
        if self.flagged_container:
            self.refresh_flagged_tab()

        # Update URL parameters
        self.update_url_params()

    def refresh_kpis(self):
        """Refresh KPI section"""
        if not self.kpi_container:
            return

        with self.kpi_container:
            self.kpi_container.clear()
            try:
                kpi_data = TicketService.get_kpi_data(self.filter_state.to_filter_params())
                create_kpi_section(kpi_data)
            except Exception as e:
                import logging

                logging.error(f"Error loading KPIs: {str(e)}")
                ui.label(f"Error loading KPIs: {str(e)}").classes("text-red-500")

    def refresh_charts(self):
        """Refresh charts section"""
        if not self.charts_container:
            return

        with self.charts_container:
            self.charts_container.clear()
            try:
                filters = self.filter_state.to_filter_params()

                # Time series chart
                with ui.card().classes("w-full p-4 mb-4"):
                    time_series_data = TicketService.get_time_series_data(filters)
                    create_time_series_chart(time_series_data)

                with ui.row().classes("w-full gap-4"):
                    # Stacked bar chart
                    with ui.card().classes("flex-1 p-4"):
                        stacked_data = TicketService.get_stacked_bar_data(filters)
                        create_stacked_bar_chart(stacked_data)

                    # Team bar chart
                    with ui.card().classes("flex-1 p-4"):
                        team_data = TicketService.get_team_ticket_counts(filters)
                        create_team_bar_chart(team_data)

            except Exception as e:
                import logging

                logging.error(f"Error loading charts: {str(e)}")
                ui.label(f"Error loading charts: {str(e)}").classes("text-red-500")

    def refresh_tickets_tab(self):
        """Refresh tickets table"""
        if not self.tickets_container:
            return

        with self.tickets_container:
            self.tickets_container.clear()
            try:
                tickets = TicketService.get_filtered_tickets(self.filter_state.to_filter_params())

                with ui.card().classes("w-full p-4"):
                    ui.label(f"Tickets ({len(tickets)})").classes("text-lg font-semibold mb-4")

                    if tickets:
                        create_simple_tickets_table(tickets)
                    else:
                        ui.label("No tickets found").classes("text-center text-gray-500 p-8")

            except Exception as e:
                import logging

                logging.error(f"Error loading tickets: {str(e)}")
                ui.label(f"Error loading tickets: {str(e)}").classes("text-red-500")

    def refresh_flagged_tab(self):
        """Refresh flagged tickets table"""
        if not self.flagged_container:
            return

        with self.flagged_container:
            self.flagged_container.clear()
            try:
                flagged_data = FlagService.get_flagged_tickets(
                    self.current_user_id, self.filter_state.to_filter_params()
                )

                with ui.card().classes("w-full p-4"):
                    with ui.row().classes("w-full justify-between items-center mb-4"):
                        ui.label(f"Flagged Tickets ({len(flagged_data)})").classes("text-lg font-semibold")

                        with ui.row().classes("gap-2"):
                            ui.button("Bulk Unflag", on_click=self.handle_bulk_unflag).props(
                                "color=secondary outline"
                            ).bind_enabled_from(self, "selected_flagged_tickets", lambda x: len(x) > 0)

                            ui.button("Export CSV", on_click=self.handle_export_csv).props("color=primary outline")

                    if flagged_data:
                        create_flagged_tickets_table(
                            flagged_data, self.selected_flagged_tickets, self.update_flagged_selection
                        )
                    else:
                        ui.label("No flagged tickets found").classes("text-center text-gray-500 p-8")

            except Exception as e:
                import logging

                logging.error(f"Error loading flagged tickets: {str(e)}")
                ui.label(f"Error loading flagged tickets: {str(e)}").classes("text-red-500")

    def handle_flag_change(self):
        """Handle flag/unflag actions"""
        # Refresh the tickets tab to show updated flag status
        self.refresh_tickets_tab()

    def update_flagged_selection(self, selected_ids: List[int]):
        """Update selected flagged tickets"""
        self.selected_flagged_tickets = selected_ids

    def handle_bulk_unflag(self):
        """Handle bulk unflag operation"""
        if not self.selected_flagged_tickets:
            ui.notify("No tickets selected", type="warning")
            return

        try:
            count = FlagService.bulk_unflag_tickets(self.current_user_id, self.selected_flagged_tickets)
            ui.notify(f"Unflagged {count} tickets", type="positive")
            self.selected_flagged_tickets = []
            self.refresh_flagged_tab()
        except Exception as e:
            import logging

            logging.error(f"Error unflagging tickets: {str(e)}")
            ui.notify(f"Error unflagging tickets: {str(e)}", type="negative")

    def handle_export_csv(self):
        """Handle CSV export of flagged tickets"""
        try:
            csv_content = ExportService.export_flagged_tickets_csv(
                self.current_user_id, self.filter_state.to_filter_params()
            )

            # Create download
            filename = f"flagged_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            # Use NiceGUI's download functionality
            ui.download(csv_content.encode("utf-8"), filename)
            ui.notify("CSV export downloaded", type="positive")

        except Exception as e:
            import logging

            logging.error(f"Error exporting CSV: {str(e)}")
            ui.notify(f"Error exporting CSV: {str(e)}", type="negative")

    def update_url_params(self):
        """Update URL parameters based on current filter state"""
        params = self.filter_state.to_url_params()
        if params:
            # Note: In a real application, you'd use JavaScript to update URL without reload
            # For now, this is a placeholder for URL parameter synchronization
            pass

    def load_from_url_params(self, params: Dict[str, Any]):
        """Load filter state from URL parameters"""
        self.filter_state.from_url_params(params)


def create():
    """Create the dashboard module"""

    dashboard_state = DashboardState()

    @ui.page("/")
    async def dashboard_page():
        """Main dashboard page"""

        # Load URL parameters
        # In a real app, you'd extract these from the request
        url_params = {}
        dashboard_state.load_from_url_params(url_params)

        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Create topbar
        create_topbar()

        # Main content
        with ui.column().classes("w-full max-w-7xl mx-auto p-6"):
            # Get available filter values
            try:
                available_values = TicketService.get_available_filter_values()
            except Exception as e:
                import logging

                logging.error(f"Error getting filter values: {str(e)}")
                available_values = {"teams": [], "severities": [], "statuses": []}

            # Create filter bar
            create_filter_bar(dashboard_state.filter_state, available_values)

            # KPI section
            dashboard_state.kpi_container = ui.column().classes("w-full")
            with dashboard_state.kpi_container:
                ui.label("Loading KPIs...").classes("text-center p-4")

            # Charts section
            dashboard_state.charts_container = ui.column().classes("w-full")
            with dashboard_state.charts_container:
                ui.label("Loading charts...").classes("text-center p-4")

            # Tabs section
            with ui.tabs().classes("w-full") as tabs:
                tickets_tab = ui.tab("Tickets")
                flagged_tab = ui.tab("Flagged Tickets")

            with ui.tab_panels(tabs, value=tickets_tab).classes("w-full"):
                # Tickets tab
                with ui.tab_panel(tickets_tab):
                    dashboard_state.tickets_container = ui.column().classes("w-full")
                    with dashboard_state.tickets_container:
                        ui.label("Loading tickets...").classes("text-center p-4")

                # Flagged tickets tab
                with ui.tab_panel(flagged_tab):
                    dashboard_state.flagged_container = ui.column().classes("w-full")
                    with dashboard_state.flagged_container:
                        ui.label("Loading flagged tickets...").classes("text-center p-4")

        # Initial data load
        await asyncio.sleep(0.1)  # Allow UI to render first
        dashboard_state.refresh_dashboard()

    # Note: API endpoints would typically be handled by FastAPI routes
    # For this demo, we'll use simple button handlers instead

    # Development seed data endpoint
    @ui.page("/seed")
    def seed_data():
        """Development endpoint to create sample data"""
        try:
            SeedService.create_sample_tickets(100)
            ui.label("✅ Created 100 sample tickets").classes("text-green-600 text-center p-8")
            ui.link("Go to Dashboard", "/").classes("block text-center mt-4")
        except Exception as e:
            import logging

            logging.error(f"Error creating sample data: {str(e)}")
            ui.label(f"❌ Error creating sample data: {str(e)}").classes("text-red-600 text-center p-8")
