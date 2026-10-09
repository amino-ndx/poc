"""
Centralized Database Configuration & Security Router for Industrial Planning System.
"""
import os
import logging
from pathlib import Path
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def is_postgres_real_mode() -> bool:
    """
    Returns True if USE_POSTGRES_REAL is set to '1' or 'true'.
    Returns False by default (SQLite Mode).
    """
    val = os.getenv("USE_POSTGRES_REAL", "0").strip().lower()
    return val in ("1", "true", "yes", "t")


def is_sqlite_mode() -> bool:
    """
    Returns True if SQLite mode is active (default).
    """
    return not is_postgres_real_mode()


def get_database_config(base_dir: Path) -> dict:
    """
    Constructs the DATABASES setting dictionary dynamically based on USE_POSTGRES_REAL.
    Centralized configuration point for Django ORM.
    """
    if is_postgres_real_mode():
        db_name = os.getenv("POSTGRES_DB", "Npdstrazabilidad")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_pass = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_schema = os.getenv("POSTGRES_SCHEMA", "traking")

        logger.info(
            "Configuring PostgreSQL (MODE 1 - REAL DATA READ ONLY): %s@%s:%s/%s [schema=%s]",
            db_user, db_host, db_port, db_name, db_schema
        )

        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_name,
                "USER": db_user,
                "PASSWORD": db_pass,
                "HOST": db_host,
                "PORT": db_port,
                "OPTIONS": {
                    "options": f"-c search_path={db_schema},public"
                },
            }
        }
    else:
        sqlite_path = base_dir / "db.sqlite3"
        logger.info("Configuring SQLite (MODE 0 - SYNTHETIC DATA POC): %s", sqlite_path)
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(sqlite_path),
            }
        }


class ReadOnlyPostgresRouter:
    """
    Database router enforcing strict READ ONLY constraints when connected
    to PostgreSQL real database (USE_POSTGRES_REAL=1).
    Blocks INSERT, UPDATE, DELETE on all mct_* operational tables.
    """

    def db_for_read(self, model, **hints):
        return "default"

    def db_for_write(self, model, **hints):
        if is_postgres_real_mode():
            table_name = getattr(model._meta, "db_table", "")
            # Block any writes to operational mct_* tables in PostgreSQL
            if table_name.startswith("mct_") or model._meta.app_label == "operational":
                raise PermissionDenied(
                    f"SEGURIDAD ACTIVA: La base PostgreSQL real es de SOLO LECTURA. "
                    f"La operación de escritura en '{table_name}' ha sido bloqueada."
                )
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Never run migrations on operational mct_* models
        if app_label == "operational":
            return False
        return True
