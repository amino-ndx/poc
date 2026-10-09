"""
Core Context Processors for Planificador Industrial.
Injects database mode indicators and common layout metadata across all templates.
"""
import os
from datetime import datetime
from config.database import is_postgres_real_mode, is_sqlite_mode


def database_status_context(request):
    is_pg = is_postgres_real_mode()
    
    if is_pg:
        db_label = "POSTGRESQL / DATOS REALES"
        db_badge_class = "badge-postgres"
        db_desc = "Conectado a PostgreSQL Npdstrazabilidad (Solo Lectura)"
        db_engine = "PostgreSQL 18"
    else:
        db_label = "SQLITE / DATOS SINTÉTICOS"
        db_badge_class = "badge-sqlite"
        db_desc = "SQLite local con datos sintéticos industriales (POC)"
        db_engine = "SQLite 3"

    now = datetime.now()
    shift_label = f"{now.strftime('%Y-%m-%d')} (Turno Taller)"

    return {
        "IS_POSTGRES_REAL": is_pg,
        "IS_SQLITE": not is_pg,
        "DB_MODE_CODE": "1" if is_pg else "0",
        "DB_MODE_LABEL": db_label,
        "DB_BADGE_CLASS": db_badge_class,
        "DB_DESCRIPTION": db_desc,
        "DB_ENGINE": db_engine,
        "CURRENT_USER_NAME": "Alexis Planificador",
        "CURRENT_USER_INITIALS": "AP",
        "CURRENT_USER_ROLE": "Senior Industrial Planner",
        "CURRENT_SHIFT_LABEL": shift_label,
    }
