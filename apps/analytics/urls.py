from django.urls import path
from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("estadisticas/", views.statistical_analysis_view, name="statistical_analysis"),
    path("desviaciones/", views.deviations_sla_view, name="deviations_sla"),
]
