from django.urls import path
from apps.quality import views

app_name = "quality"

urlpatterns = [
    path("", views.data_quality_view, name="data_quality"),
    path("database/", views.database_status_view, name="database_status"),
    path("database/mct/", views.mct_explorer_view, name="mct_explorer"),
    path("database/compare/", views.database_compare_view, name="database_compare"),
    path("relations/", views.relations_explorer_view, name="relations_explorer"),
]
