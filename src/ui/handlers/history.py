from __future__ import annotations

from src.services.table_formatters import applications_to_table
from src.tools.db_tools import list_applications, setup_database


def list_applications_rows() -> list[list]:
    setup_database()
    apps = list_applications()
    return applications_to_table(apps)
