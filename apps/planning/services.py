"""
Planning Services: Orchestrates prioritization, sequencing, and persists plans into poc_* tables.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apps.operational.models import (
    MctOrdenTrabajo,
    MctMovimientoOrdenTrabajo,
    MctMaquina,
    MctCliente,
)
from apps.operational.services import get_clients_map
from apps.planning.models import (
    PocConfigPriorizacion,
    PocPlanificacion,
    PocPlanificacionDetalle,
    PocSimulacion,
    PocEventoPlanificacion,
)
from apps.planning.engine import (
    compute_order_priority,
    get_prioritized_ranking,
    calculate_machine_workloads,
)

logger = logging.getLogger(__name__)


def generate_new_production_sequence(description: str = "Secuencia Óptima de Taller", max_orders: int = 15) -> PocPlanificacion:
    """
    Evaluates active work orders, sorts them according to priority scores,
    and records a new production plan in poc_planificacion & poc_planificacion_detalle.
    """
    orders = list(MctOrdenTrabajo.objects.all().order_by("-idordentrabajo")[:max_orders])
    clients_map = get_clients_map()
    
    # Gather movements
    ot_ids = [o.idordentrabajo for o in orders]
    movs = list(MctMovimientoOrdenTrabajo.objects.filter(idordentrabajo__in=ot_ids))
    movs_by_ot: Dict[int, list] = {}
    for m in movs:
        movs_by_ot.setdefault(m.idordentrabajo, []).append(m)

    ranking = get_prioritized_ranking(orders, clients_map, movs_by_ot, limit=len(orders))

    now = datetime.now()
    plan_code = f"PLAN-{now.strftime('%Y%m%d-%H%M%S')}"

    # Calculate makespan
    total_hours = sum(item["tiempo_restante_horas"] for item in ranking)
    makespan = round(total_hours * 0.65, 1)  # assumes multi-machine parallelism

    # Check bottlenecks
    machines = list(MctMaquina.objects.all()[:20])
    workloads = calculate_machine_workloads(machines, movs)
    bottlenecks = sum(1 for w in workloads if w["is_bottleneck"])

    plan = PocPlanificacion.objects.create(
        codigo_plan=plan_code,
        descripcion=description,
        total_ordenes=len(ranking),
        makespan_horas=makespan,
        cuellos_botella_detectados=bottlenecks,
        estado="GENERADO",
    )

    current_start = now
    for idx, item in enumerate(ranking, start=1):
        dur = item["tiempo_restante_horas"]
        fin = current_start + timedelta(hours=dur)
        PocPlanificacionDetalle.objects.create(
            planificacion=plan,
            idordentrabajo=item["idordentrabajo"],
            nombreordentrabajo=item["nombreordentrabajo"],
            cliente_nombre=item["cliente"],
            posicion_secuencia=idx,
            score_prioridad=item["score"],
            holgura_horas=item["holgura"],
            critical_ratio=item["critical_ratio"],
            tiempo_estimado_horas=dur,
            fecha_inicio_programada=current_start,
            fecha_fin_programada=fin,
            razon_principal=item["razon_principal"],
        )
        current_start = fin

    PocEventoPlanificacion.objects.create(
        tipo_evento="SECUENCIA_GENERADA",
        descripcion=f"Se generó exitosamente el plan {plan_code} con {len(ranking)} órdenes y makespan de {makespan}h."
    )

    return plan


def simulate_urgent_insertion_service(urgent_ot_name: str, client_name: str, estimated_hours: float = 18.0) -> Dict[str, Any]:
    """
    Simulates inserting an emergency order into the current schedule and calculates the impact.
    """
    now = datetime.now()
    latest_plan = PocPlanificacion.objects.order_by("-fecha_generacion").first()
    
    if not latest_plan:
        latest_plan = generate_new_production_sequence("Plan Base Previo a Simulación")

    details = list(latest_plan.detalles.all().order_by("posicion_secuencia"))
    
    # Urgent order jumps to position 1
    displaced_orders = []
    accumulated_delay = estimated_hours
    
    for d in details:
        displaced_orders.append({
            "idordentrabajo": d.idordentrabajo,
            "nombreordentrabajo": d.nombreordentrabajo,
            "posicion_anterior": d.posicion_secuencia,
            "nueva_posicion": d.posicion_secuencia + 1,
            "retraso_estimado_horas": accumulated_delay,
            "nuevo_impacto_holgura": round(d.holgura_horas - accumulated_delay, 2),
        })

    simulation_result = {
        "orden_urgente": {
            "nombre": urgent_ot_name,
            "cliente": client_name,
            "horas_requeridas": estimated_hours,
            "posicion_asignada": 1,
            "score_urgencia": 98.5,
        },
        "plan_base_codigo": latest_plan.codigo_plan,
        "makespan_anterior_horas": latest_plan.makespan_horas,
        "nuevo_makespan_horas": round(latest_plan.makespan_horas + estimated_hours, 1),
        "ordenes_desplazadas_total": len(displaced_orders),
        "ordenes_impactadas": displaced_orders,
    }

    import json
    PocSimulacion.objects.create(
        nombre=f"Inserción Urgente: {urgent_ot_name[:50]}",
        tipo_simulacion="INSERCION_URGENTE",
        parametros_json=json.dumps({"ot": urgent_ot_name, "cliente": client_name, "duracion": estimated_hours}),
        resultado_json=json.dumps(simulation_result),
    )

    PocEventoPlanificacion.objects.create(
        tipo_evento="SIMULACION_URGENTE",
        descripcion=f"Simulación ejecutada para OT Urgente: {urgent_ot_name}. {len(displaced_orders)} órdenes desplazadas."
    )

    return simulation_result
