"""
Operational Views: Work Orders, Movements, Order relational details.
Thin presentation layer delegating queries to services.
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from apps.operational.models import (
    MctOrdenTrabajo,
    MctMovimientoOrdenTrabajo,
    MctMaquina,
    MctOperador,
    MctProgAvisos,
    MctSla,
    MctCliente
)
from apps.operational.services import (
    get_clients_map,
    get_machines_map,
    get_operators_map,
    get_activities_map,
    get_order_parts_tree,
)


def work_orders_view(request):
    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")
    
    qs = MctOrdenTrabajo.objects.all().order_by("-idordentrabajo")
    if search:
        qs = qs.filter(nombreordentrabajo__icontains=search)
    if status_filter:
        qs = qs.filter(idestadoorden=status_filter)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    clients_map = get_clients_map()

    return render(request, "operational/work_orders.html", {
        "page_obj": page_obj,
        "search": search,
        "clients_map": clients_map,
        "total_orders": qs.count(),
    })


def work_order_detail_view(request, order_id):
    order = get_object_or_404(MctOrdenTrabajo, idordentrabajo=order_id)
    clients_map = get_clients_map()
    client_name = clients_map.get(order.idcliente, f"Cliente #{order.idcliente}")
    
    parts_tree = get_order_parts_tree(order_id)
    
    # Progavisos for this order
    progavisos = list(MctProgAvisos.objects.filter(idordentrabajo=order_id).order_by("ordenproceso", "fecha_inicio"))
    slas_map = {s.idsla: s.nombresla for s in MctSla.objects.all()}

    progaviso_items = []
    for pa in progavisos:
        progaviso_items.append({
            "pa": pa,
            "sla_nombre": slas_map.get(pa.idsla, f"SLA #{pa.idsla}"),
        })

    return render(request, "operational/order_detail.html", {
        "order": order,
        "client_name": client_name,
        "parts_tree": parts_tree,
        "progavisos": progaviso_items,
    })


def movements_view(request):
    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")

    qs = MctMovimientoOrdenTrabajo.objects.all().order_by("-idmovimientoordentrabajo")
    if search:
        qs = qs.filter(codhojaruta__icontains=search)
    if status_filter == "abiertos":
        qs = qs.filter(fechainicio__isnull=False, fechatermino__isnull=True)
    elif status_filter == "cerrados":
        qs = qs.filter(fechainicio__isnull=False, fechatermino__isnull=False)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    machines_map = get_machines_map()
    operators_map = get_operators_map()
    activities_map = get_activities_map()

    for m in page_obj:
        m.actividad_nombre = activities_map.get(m.idactividad, f"Actividad #{m.idactividad}")
        m.maquina_nombre = machines_map.get(m.idmaquina, "Sin máquina")
        m.operador_nombre = operators_map.get(m.idoperador, "Sin operador")

    return render(request, "operational/movements.html", {
        "page_obj": page_obj,
        "search": search,
        "status_filter": status_filter,
        "total_movements": qs.count(),
    })
