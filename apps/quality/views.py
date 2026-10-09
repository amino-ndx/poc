"""
Quality Views: Database Status, MCT Table Explorer, Comparison, Data Quality, Relationship Explorer.
"""
from django.shortcuts import render
from apps.quality.services import (
    get_database_status_info,
    list_detected_mct_tables,
    get_table_sample_and_columns,
    compare_sqlite_and_postgres_counts,
    get_data_quality_report,
    verify_all_relationships,
    MAIN_MCT_TABLES,
)


def database_status_view(request):
    """
    Renders /quality/database/ with detailed non-sensitive database connection status.
    """
    db_info = get_database_status_info()
    return render(request, "quality/database_status.html", {
        "db_info": db_info,
    })


def mct_explorer_view(request):
    """
    Renders /quality/database/mct/ with dynamic MCT table browser, column metadata,
    null counts and paginated sample data.
    """
    all_tables = list_detected_mct_tables()
    selected_table = request.GET.get("table", "mct_ordentrabajo")
    page = int(request.GET.get("page", 1))

    table_data = get_table_sample_and_columns(selected_table, page=page)

    return render(request, "quality/mct_explorer.html", {
        "all_tables": all_tables,
        "selected_table": selected_table,
        "table_data": table_data,
    })


def database_compare_view(request):
    """
    Renders /quality/database/compare/ displaying dynamic row counts
    comparing SQLite local against PostgreSQL real database.
    """
    comparison_data = compare_sqlite_and_postgres_counts()
    return render(request, "quality/compare.html", {
        "comparison": comparison_data,
    })


def data_quality_view(request):
    """
    Renders /quality/ with data quality diagnostics, anomalies, nulls, and duration checks.
    """
    report = get_data_quality_report()
    return render(request, "quality/data_quality.html", {
        "report": report,
    })


def relations_explorer_view(request):
    """
    Renders /quality/relations/ with the relational verification matrix and interactive relationship tree.
    """
    relationships = verify_all_relationships()
    return render(request, "quality/relations_explorer.html", {
        "relationships": relationships,
    })
