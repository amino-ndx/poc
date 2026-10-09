"""
Quality Services: Database Status, MCT Table Explorer, SQLite vs PostgreSQL Comparator,
Data Quality Diagnostics, and Relationship Verification.
Never exposes sensitive passwords.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from django.db import connection
from config.database import is_postgres_real_mode, is_sqlite_mode

logger = logging.getLogger(__name__)

MAIN_MCT_TABLES = [
    "mct_ordentrabajo",
    "mct_ordentrabajoparte",
    "mct_componente",
    "mct_parte",
    "mct_hojaruta",
    "mct_movimientoordentrabajo",
    "mct_maquina",
    "mct_operador",
    "mct_progavisos",
    "mct_movimientobloqueo",
    "mct_actividad",
    "mct_seccion",
    "mct_sla",
    "mct_cliente",
    "mct_producto",
    "mct_estadoorden",
]


def get_database_status_info() -> Dict[str, Any]:
    """
    Returns non-sensitive metadata regarding the active database connection.
    Guaranteed never to reveal passwords.
    """
    is_pg = is_postgres_real_mode()
    
    if is_pg:
        db_name = os.getenv("POSTGRES_DB", "Npdstrazabilidad")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        schema = os.getenv("POSTGRES_SCHEMA", "traking")
        engine = "PostgreSQL"
        mode_label = "PostgreSQL — Datos reales"
    else:
        db_name = "db.sqlite3"
        host = "Localhost (Archivo local)"
        port = "N/A"
        user = "N/A"
        schema = "main"
        engine = "SQLite"
        mode_label = "SQLite — Datos sintéticos"

    # Test active connection
    status = "CONECTADO"
    error_msg = None
    table_counts = {}

    try:
        with connection.cursor() as cursor:
            for tbl in MAIN_MCT_TABLES:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                    row = cursor.fetchone()
                    table_counts[tbl] = row[0] if row else 0
                except Exception:
                    table_counts[tbl] = "N/A"
    except Exception as e:
        status = "ERROR"
        error_msg = "No fue posible conectar con la base de datos configurada."
        logger.error("Database connection check failed: %s", e)

    return {
        "is_postgres": is_pg,
        "is_sqlite": not is_pg,
        "mode_label": mode_label,
        "engine": engine,
        "database_name": db_name,
        "host": host,
        "port": port,
        "user": user,
        "schema": schema,
        "status": status,
        "error_msg": error_msg,
        "table_counts": table_counts,
    }


def list_detected_mct_tables() -> List[Dict[str, Any]]:
    """
    Detects all tables starting with 'mct_' in the current database.
    Returns table name, record count, and column count.
    """
    is_pg = is_postgres_real_mode()
    tables_info = []

    with connection.cursor() as cursor:
        if is_pg:
            schema = os.getenv("POSTGRES_SCHEMA", "traking")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name LIKE 'mct_%%'
                ORDER BY table_name;
            """, [schema])
            table_names = [row[0] for row in cursor.fetchall()]
            
            for t in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {t};")
                    rc = cursor.fetchone()[0]
                except Exception:
                    rc = 0
                try:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = %s;
                    """, [schema, t])
                    cc = cursor.fetchone()[0]
                except Exception:
                    cc = 0
                tables_info.append({"name": t, "row_count": rc, "col_count": cc, "exists": True})
        else:
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'mct_%%'
                ORDER BY name;
            """)
            table_names = [row[0] for row in cursor.fetchall()]
            for t in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {t};")
                    rc = cursor.fetchone()[0]
                except Exception:
                    rc = 0
                try:
                    cursor.execute(f"PRAGMA table_info({t});")
                    cc = len(cursor.fetchall())
                except Exception:
                    cc = 0
                tables_info.append({"name": t, "row_count": rc, "col_count": cc, "exists": True})

    return tables_info


def get_table_sample_and_columns(table_name: str, page: int = 1, page_size: int = 15) -> Dict[str, Any]:
    """
    Inspects columns, types, null counts, and returns paginated sample rows for an mct_* table.
    """
    if not table_name.startswith("mct_"):
        return {"error": "Solo se permite explorar tablas mct_*"}

    is_pg = is_postgres_real_mode()
    columns_info = []
    rows = []
    total_rows = 0

    with connection.cursor() as cursor:
        if is_pg:
            schema = os.getenv("POSTGRES_SCHEMA", "traking")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, [schema, table_name])
            col_meta = cursor.fetchall()
            col_names = [c[0] for c in col_meta]

            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            total_rows = cursor.fetchone()[0]

            for c in col_meta:
                c_name, c_type, is_null = c
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {c_name} IS NULL;")
                    null_count = cursor.fetchone()[0]
                except Exception:
                    null_count = "N/A"
                columns_info.append({
                    "name": c_name,
                    "type": c_type,
                    "nullable": is_null == "YES",
                    "null_count": null_count,
                })
            
            offset = (page - 1) * page_size
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {page_size} OFFSET {offset};")
            raw_rows = cursor.fetchall()
            for r in raw_rows:
                rows.append([str(val) if val is not None else "" for val in r])
        else:
            cursor.execute(f"PRAGMA table_info({table_name});")
            col_meta = cursor.fetchall()
            col_names = [c[1] for c in col_meta]

            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            total_rows = cursor.fetchone()[0]

            for c in col_meta:
                cid, c_name, c_type, notnull, dflt, pk = c
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {c_name} IS NULL;")
                    null_count = cursor.fetchone()[0]
                except Exception:
                    null_count = 0
                columns_info.append({
                    "name": c_name,
                    "type": c_type,
                    "nullable": not notnull,
                    "null_count": null_count,
                })

            offset = (page - 1) * page_size
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {page_size} OFFSET {offset};")
            raw_rows = cursor.fetchall()
            for r in raw_rows:
                rows.append([str(val) if val is not None else "" for val in r])

    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    return {
        "table_name": table_name,
        "total_rows": total_rows,
        "page": page,
        "total_pages": total_pages,
        "columns": columns_info,
        "col_names": col_names,
        "rows": rows,
    }


def compare_sqlite_and_postgres_counts() -> List[Dict[str, Any]]:
    """
    Dynamically compares table row counts between SQLite and PostgreSQL.
    """
    import sqlite3
    import psycopg
    from pathlib import Path
    from django.conf import settings

    sqlite_db_path = settings.BASE_DIR / "db.sqlite3"
    
    # 1. Fetch SQLite counts
    sqlite_counts = {}
    if sqlite_db_path.exists():
        try:
            s_conn = sqlite3.connect(str(sqlite_db_path))
            s_cur = s_conn.cursor()
            for tbl in MAIN_MCT_TABLES:
                try:
                    s_cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    sqlite_counts[tbl] = s_cur.fetchone()[0]
                except Exception:
                    sqlite_counts[tbl] = 0
            s_conn.close()
        except Exception as e:
            logger.warning("Error reading SQLite counts: %s", e)

    # 2. Fetch PostgreSQL counts
    pg_counts = {}
    pg_db = os.getenv("POSTGRES_DB", "Npdstrazabilidad")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "root123")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_schema = os.getenv("POSTGRES_SCHEMA", "traking")

    try:
        conn = psycopg.connect(
            dbname=pg_db,
            user=pg_user,
            password=pg_pass,
            host=pg_host,
            port=pg_port,
            options=f"-c search_path={pg_schema},public"
        )
        cur = conn.cursor()
        for tbl in MAIN_MCT_TABLES:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                pg_counts[tbl] = cur.fetchone()[0]
            except Exception:
                pg_counts[tbl] = "Error"
        conn.close()
    except Exception as e:
        logger.warning("Could not connect to PostgreSQL for comparison: %s", e)
        for tbl in MAIN_MCT_TABLES:
            pg_counts[tbl] = "No conectado"

    comparison = []
    for tbl in MAIN_MCT_TABLES:
        comparison.append({
            "table": tbl,
            "sqlite_count": sqlite_counts.get(tbl, 0),
            "postgres_count": pg_counts.get(tbl, "N/A"),
        })

    return comparison


def get_data_quality_report() -> Dict[str, Any]:
    """
    Performs data quality checks on operational movements and orders:
    - Movements with NULL fechainicio
    - Movements with duration <= 0
    - Movements with negative durations (fechatermino < fechainicio)
    - Open movements
    - Movements without machine
    - Movements without operator
    - OTs without parts
    """
    from apps.operational.models import (
        MctOrdenTrabajo,
        MctMovimientoOrdenTrabajo,
        MctOrdenTrabajoParte,
        MctHojaRuta,
    )
    
    total_movs = MctMovimientoOrdenTrabajo.objects.count()
    null_start = MctMovimientoOrdenTrabajo.objects.filter(fechainicio__isnull=True).count()
    open_movs = MctMovimientoOrdenTrabajo.objects.filter(fechainicio__isnull=False, fechatermino__isnull=True).count()
    no_machine = MctMovimientoOrdenTrabajo.objects.filter(idmaquina__isnull=True).count()
    no_operator = MctMovimientoOrdenTrabajo.objects.filter(idoperador__isnull=True).count()

    # Invert date anomaly
    negative_durs = 0
    zero_durs = 0
    sample = list(MctMovimientoOrdenTrabajo.objects.filter(fechainicio__isnull=False, fechatermino__isnull=False)[:500])
    for s in sample:
        if s.fechatermino < s.fechainicio:
            negative_durs += 1
        elif s.fechatermino == s.fechainicio:
            zero_durs += 1

    total_ots = MctOrdenTrabajo.objects.count()
    ots_with_parts = set(MctOrdenTrabajoParte.objects.values_list("idordentrabajo", flat=True).distinct())
    ots_without_parts = max(0, total_ots - len(ots_with_parts))

    anomalies = [
        {"check": "Movimientos con fecha de inicio NULL", "count": null_start, "severity": "ALTA" if null_start > 0 else "INFO"},
        {"check": "Movimientos abiertos (en curso en taller)", "count": open_movs, "severity": "INFO"},
        {"check": "Movimientos con duración <= 0 (fechas iguales)", "count": zero_durs, "severity": "MEDIA" if zero_durs > 0 else "INFO"},
        {"check": "Movimientos con fecha término menor a inicio", "count": negative_durs, "severity": "ALTA" if negative_durs > 0 else "INFO"},
        {"check": "Movimientos sin máquina asignada", "count": no_machine, "severity": "MEDIA" if no_machine > 0 else "INFO"},
        {"check": "Movimientos sin operador asignado", "count": no_operator, "severity": "MEDIA" if no_operator > 0 else "INFO"},
        {"check": "Órdenes de Trabajo sin partes asociadas", "count": ots_without_parts, "severity": "MEDIA" if ots_without_parts > 0 else "INFO"},
    ]

    total_issues = null_start + negative_durs + zero_durs + no_machine + no_operator + ots_without_parts
    score = max(50.0, round(100.0 - (total_issues * 0.1), 1)) if total_movs > 0 else 100.0

    return {
        "score": score,
        "total_movimientos": total_movs,
        "total_ordenes": total_ots,
        "anomalies": anomalies,
    }


def verify_all_relationships() -> List[Dict[str, Any]]:
    """
    Validates the 9 key relational links:
    OT -> OT Parte
    OT Parte -> Componente
    OT Parte -> Parte
    OT Parte -> Hoja Ruta
    Hoja Ruta -> Movimiento
    Movimiento -> Máquina
    Movimiento -> Operador
    OT -> Programación
    Movimiento -> Bloqueo
    """
    from apps.operational.models import (
        MctOrdenTrabajo,
        MctOrdenTrabajoParte,
        MctComponente,
        MctParte,
        MctHojaRuta,
        MctMovimientoOrdenTrabajo,
        MctMaquina,
        MctOperador,
        MctProgAvisos,
        MctMovimientoBloqueo,
    )

    relationships = []

    def check_rel(name: str, source_model, target_model, fk_field: str, target_pk: str, is_physical: bool = False):
        total_source = source_model.objects.count()
        if total_source == 0:
            return {"name": name, "status": "NO VALIDADA", "details": "Sin registros en modelo origen", "type": "Física" if is_physical else "Lógica"}
        
        try:
            field_obj = source_model._meta.get_field(fk_field)
            if field_obj.get_internal_type() in ("CharField", "TextField"):
                sample_ids = list(source_model.objects.filter(**{f"{fk_field}__isnull": False}).exclude(**{fk_field: ""}).values_list(fk_field, flat=True)[:100])
            else:
                sample_ids = list(source_model.objects.filter(**{f"{fk_field}__gt": 0}).values_list(fk_field, flat=True)[:100])
        except Exception:
            sample_ids = list(source_model.objects.filter(**{f"{fk_field}__isnull": False}).values_list(fk_field, flat=True)[:100])

        if not sample_ids:
            return {"name": name, "status": "NO VALIDADA", "details": "Valores NULL o 0 en clave foránea", "type": "Física" if is_physical else "Lógica"}
        
        valid_targets = target_model.objects.filter(**{f"{target_pk}__in": sample_ids}).count()
        status = "OK" if valid_targets > 0 else "ERROR"
        return {
            "name": name,
            "status": status,
            "details": f"{valid_targets} coincidencias validadas sobre muestra",
            "type": "Física (FK)" if is_physical else "Lógica (ID)",
        }

    relationships.append(check_rel("OT → OT Parte", MctOrdenTrabajoParte, MctOrdenTrabajo, "idordentrabajo", "idordentrabajo", False))
    relationships.append(check_rel("OT Parte → Componente", MctOrdenTrabajoParte, MctComponente, "idcomponente", "idcomponente", False))
    relationships.append(check_rel("OT Parte → Parte", MctOrdenTrabajoParte, MctParte, "idparte", "idparte", True))
    relationships.append(check_rel("OT Parte → Hoja Ruta", MctHojaRuta, MctOrdenTrabajoParte, "idordentrabajoparte", "idordentrabajoparte", False))
    relationships.append(check_rel("Hoja Ruta → Movimiento", MctMovimientoOrdenTrabajo, MctHojaRuta, "idhojaruta", "idhojaruta", False))
    relationships.append(check_rel("Movimiento → Máquina", MctMovimientoOrdenTrabajo, MctMaquina, "idmaquina", "idmaquina", False))
    relationships.append(check_rel("Movimiento → Operador", MctMovimientoOrdenTrabajo, MctOperador, "idoperador", "idoperador", False))
    relationships.append(check_rel("OT → Programación (Avisos)", MctProgAvisos, MctOrdenTrabajo, "idordentrabajo", "idordentrabajo", False))
    relationships.append(check_rel("Movimiento → Bloqueo", MctMovimientoBloqueo, MctHojaRuta, "codhojaruta", "codhojaruta", False))

    return relationships
