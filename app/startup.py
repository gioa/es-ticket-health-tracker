from app.database import create_tables
from app.seed_data import create_sample_data
import app.dashboard


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Create sample data for demonstration
    create_sample_data()

    # Register dashboard module
    app.dashboard.create()
