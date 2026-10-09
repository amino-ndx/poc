"""
URL configuration for industrial planning system POC.
"""
from django.contrib import admin
from django.urls import path, include
from apps.analytics.views import dashboard_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_view, name="dashboard"),
    path("operaciones/", include("apps.operational.urls", namespace="operational")),
    path("analytics/", include("apps.analytics.urls", namespace="analytics")),
    path("planning/", include("apps.planning.urls", namespace="planning")),
    path("quality/", include("apps.quality.urls", namespace="quality")),
]
