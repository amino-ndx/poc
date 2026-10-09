from django.urls import path
from apps.operational import views

app_name = "operational"

urlpatterns = [
    path("ordenes/", views.work_orders_view, name="work_orders"),
    path("ordenes/<int:order_id>/", views.work_order_detail_view, name="order_detail"),
    path("movimientos/", views.movements_view, name="movements"),
]
