"""
Planning Views: Prioritization, Scheduling, Capacity/Bottlenecks, and Urgent Insertion Simulation.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.operational.models import (
    MctOrdenTrabajo,
    MctMovimientoOrdenTrabajo,
    MctMaquina,
)
from apps.operational.services import get_clients_map
from apps.planning.models import (
    PocConfigPriorizacion,
    PocPlanificacion,
    PocPlanificacionDetalle,
    PocSimulacion,
)
from apps.planning.engine import (
    get_prioritized_ranking,
    calculate_machine_workloads,
)
from apps.planning.services import (
    generate_new_production_sequence,
    simulate_urgent_insertion_service,
)


def prioritization_view(request):
    orders = list(MctOrdenTrabajo.objects.all().order_by("-idordentrabajo")[:50])
    clients_map = get_clients_map()
    
    ot_ids = [o.idordentrabajo for o in orders]
    movs = list(MctMovimientoOrdenTrabajo.objects.filter(idordentrabajo__in=ot_ids))
    movs_by_ot = {}
    for m in movs:
        movs_by_ot.setdefault(m.idordentrabajo, []).append(m)

    ranking = get_prioritized_ranking(orders, clients_map, movs_by_ot, limit=len(orders))
    try:
        config = PocConfigPriorizacion.objects.filter(activo=True).first()
    except Exception:
        config = None

    return render(request, "planning/prioritization.html", {
        "ranking": ranking,
        "config": config,
        "total_evaluated": len(ranking),
    })


def scheduling_view(request):
    try:
        plans = list(PocPlanificacion.objects.all().order_by("-fecha_generacion"))
    except Exception:
        plans = []
        
    selected_plan = plans[0] if plans else None
    plan_id = request.GET.get("plan_id")
    if plan_id:
        try:
            selected_plan = PocPlanificacion.objects.filter(idplanificacion=plan_id).first()
        except Exception:
            pass

    detalles = selected_plan.detalles.all() if selected_plan else []

    return render(request, "planning/scheduling.html", {
        "plans": plans,
        "selected_plan": selected_plan,
        "detalles": detalles,
    })


def generate_plan_action(request):
    if request.method == "POST":
        plan = generate_new_production_sequence()
        messages.success(request, f"¡Secuencia {plan.codigo_plan} generada exitosamente!")
    return redirect("planning:scheduling")


def capacity_bottlenecks_view(request):
    machines = list(MctMaquina.objects.all())
    movements = list(MctMovimientoOrdenTrabajo.objects.all()[:500])
    workloads = calculate_machine_workloads(machines, movements)

    bottlenecks_count = sum(1 for w in workloads if w["is_bottleneck"])

    return render(request, "planning/capacity_bottlenecks.html", {
        "workloads": workloads,
        "bottlenecks_count": bottlenecks_count,
        "total_machines": len(workloads),
    })


def simulation_view(request):
    sim_result = None
    if request.method == "POST":
        ot_name = request.POST.get("ot_name", "OT-99999 Bomba Urgencia Minera")
        client_name = request.POST.get("client_name", "Minera Escondida BHP")
        hours = float(request.POST.get("hours", 20.0))
        sim_result = simulate_urgent_insertion_service(ot_name, client_name, hours)
        messages.info(request, "Simulación completada. Verifique el impacto en la tabla inferior.")

    recent_simulations = PocSimulacion.objects.order_by("-fecha_simulacion")[:5]

    return render(request, "planning/simulation.html", {
        "sim_result": sim_result,
        "recent_simulations": recent_simulations,
    })
