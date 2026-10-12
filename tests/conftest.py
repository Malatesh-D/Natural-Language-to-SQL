import pytest
from backend.core.config import get_settings
from backend.database.init_db import initialize_database

@pytest.fixture(scope="session", autouse=True)
def sample_database():
    initialize_database()
