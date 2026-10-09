from django.urls import path
from apps.planning import views

app_name = "planning"

urlpatterns = [
    path("priorizacion/", views.prioritization_view, name="prioritization"),
    path("secuencia/", views.scheduling_view, name="scheduling"),
    path("secuencia/generar/", views.generate_plan_action, name="generate_plan"),
    path("capacidad/", views.capacity_bottlenecks_view, name="capacity"),
    path("simulacion/", views.simulation_view, name="simulation"),
]
