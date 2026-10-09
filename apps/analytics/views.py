"""
Analytics Views: Dashboard, Statistical Distributions, SLA Deviations.
"""
from django.shortcuts import render
from apps.analytics.services import (
    get_dashboard_summary,
    get_statistical_distribution_by,
    get_sla_deviations_report,
)


def dashboard_view(request):
    """
    Renders the Executive Dashboard, perfectly aligned with the design
    in template/IMG-20261004-WA0000.jpg.
    """
    summary = get_dashboard_summary()
    return render(request, "analytics/dashboard.html", {
        "kpis": summary["kpis"],
        "ranking": summary["ranking"],
        "plans_count": summary["plans_count"],
        "latest_plan": summary["latest_plan"],
    })


def statistical_analysis_view(request):
    group_by = request.GET.get("group_by", "actividad")
    stats = get_statistical_distribution_by(group_field=group_by)
    return render(request, "analytics/statistical_analysis.html", {
        "stats": stats,
        "group_by": group_by,
    })


def deviations_sla_view(request):
    sla_report = get_sla_deviations_report()
    return render(request, "analytics/deviations_sla.html", {
        "report": sla_report,
    })
