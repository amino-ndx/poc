"""
Pure Domain Engine for Planning, Sequencing, Prioritization, Capacity and Simulation.
Decoupled from views, templates and database engines.
Applies:
- Holgura (Slack time in hours)
- Critical Ratio (CR = Time to Due Date / Remaining Processing Time)
- WSPT (Weighted Shortest Processing Time)
- Multi-criteria Priority Scoring (0 - 100)
- Machine Capacity Utilization & Bottleneck identification
- Urgent Order Insertion Simulation
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def calculate_holgura(
    fecha_entrega: Optional[datetime],
    tiempo_proceso_restante_horas: float,
    fecha_referencia: Optional[datetime] = None
) -> float:
    """
    Calculates slack time (holgura) in hours:
    Holgura = (Fecha Entrega - Fecha Referencia) en horas - Tiempo Proceso Restante
    Negative holgura indicates the order is overdue or critically delayed.
    """
    if not fecha_entrega:
        return 999.0
    ref = fecha_referencia or datetime.now()
    horas_disponibles = (fecha_entrega - ref).total_seconds() / 3600.0
    return round(horas_disponibles - tiempo_proceso_restante_horas, 2)


def calculate_critical_ratio(
    fecha_entrega: Optional[datetime],
    tiempo_proceso_restante_horas: float,
    fecha_referencia: Optional[datetime] = None
) -> float:
    """
    Calculates Critical Ratio (CR):
    CR = Horas Disponibles hasta Entrega / Tiempo de Proceso Restante
    CR < 1.0 : Atrasada / Crítica
    CR = 1.0 : Justo a tiempo
    CR > 1.0 : Con holgura positiva
    """
    if not fecha_entrega:
        return 5.0
    if tiempo_proceso_restante_horas <= 0.1:
        return 1.0
    ref = fecha_referencia or datetime.now()
    horas_disponibles = (fecha_entrega - ref).total_seconds() / 3600.0
    if horas_disponibles <= 0:
        return round(max(0.01, horas_disponibles / tiempo_proceso_restante_horas), 2)
    return round(horas_disponibles / tiempo_proceso_restante_horas, 2)


def calculate_wspt_index(peso_prioridad: float, tiempo_proceso_horas: float) -> float:
    """
    WSPT = Peso / Tiempo de Proceso.
    Higher index gets sequenced first in dispatching rules.
    """
    duracion = max(1.0, tiempo_proceso_horas)
    return round(peso_prioridad / duracion, 4)


def compute_order_priority(
    order,
    client_name: str,
    movements: list,
    weights: Optional[Dict[str, float]] = None,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates multi-criteria priority score for an OT (0 to 100).
    """
    now = now or datetime.now()
    w = weights or {
        "holgura": 0.35,
        "cliente": 0.25,
        "wspt": 0.20,
        "reproceso": 0.20,
    }

    # 1. Estimated remaining duration from movements
    total_mov_duration = sum(m.duracion_horas for m in movements if m.duracion_horas > 0)
    tiempo_restante = max(4.0, total_mov_duration if total_mov_duration > 0 else 24.0)

    # 2. Due date & Holgura
    fecha_entrega = order.fechaentrega or order.fechasolicitudentrega
    holgura = calculate_holgura(fecha_entrega, tiempo_restante, now)
    cr = calculate_critical_ratio(fecha_entrega, tiempo_restante, now)

    # 3. Base score components
    # Holgura subscore: lower holgura -> higher score
    if holgura < 0:
        holgura_score = min(100.0, 75.0 + abs(holgura))
    elif holgura < 24:
        holgura_score = 70.0 - (holgura * 1.2)
    elif holgura < 72:
        holgura_score = 45.0 - (holgura * 0.3)
    else:
        holgura_score = max(5.0, 30.0 - (holgura * 0.1))

    # Client priority subscore
    name_upper = (client_name or "").upper()
    ot_upper = (order.nombreordentrabajo or "").upper()
    client_score = 50.0
    if "CODELCO" in name_upper or "MINERA ESCONDIDA" in name_upper or "BHP" in name_upper:
        client_score = 90.0
    elif "ANGLO" in name_upper or "ANTOFAGASTA" in name_upper or "PELAMBRES" in name_upper or "COLLAHUASI" in name_upper:
        client_score = 75.0
    
    # Priority flag from order model
    if order.prioridad and order.prioridad > 0:
        client_score = min(100.0, client_score + (order.prioridad * 5.0))

    # WSPT subscore
    wspt_val = calculate_wspt_index(client_score, tiempo_restante)
    wspt_score = min(100.0, wspt_val * 20.0)

    # Reproceso or Urgency penalty/boost
    reproceso_score = 10.0
    has_reproceso = any(bool(m.reprocesosol or m.reprocesocc or m.checkncbomba) for m in movements)
    if has_reproceso or "URGENCIA" in ot_upper or "PARADA" in ot_upper:
        reproceso_score = 95.0

    final_score = (
        w["holgura"] * holgura_score +
        w["cliente"] * client_score +
        w["wspt"] * wspt_score +
        w["reproceso"] * reproceso_score
    )
    final_score = round(min(99.9, max(1.0, final_score)), 1)

    # Primary Reason formulation (matching visual POC design)
    if holgura < 0:
        razon = "OT priorizada debido a: fecha de entrega comprometida vencida o en riesgo alto"
    elif "URGENCIA" in ot_upper or reproceso_score > 80:
        razon = "OT priorizada debido a: urgencia de parada de planta / reproceso operacional"
    elif holgura < 48:
        razon = "OT priorizada debido a: fecha de entrega muy próxima con holgura reducida"
    elif client_score >= 85:
        razon = "OT priorizada debido a: alto impacto operacional con cliente estratégico minero"
    else:
        razon = "OT priorizada debido a: prioridad comercial de cliente y ventana de taller"

    return {
        "idordentrabajo": order.idordentrabajo,
        "nombreordentrabajo": order.nombreordentrabajo or f"OT-{order.idordentrabajo}",
        "cliente": client_name,
        "score": final_score,
        "holgura": holgura,
        "critical_ratio": cr,
        "tiempo_restante_horas": round(tiempo_restante, 1),
        "razon_principal": razon,
    }


def get_prioritized_ranking(orders: list, clients_map: dict, movements_by_ot: dict, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Calculates priorities for all supplied orders and returns top prioritized items.
    """
    scored_items = []
    for o in orders:
        c_name = clients_map.get(o.idcliente, "Cliente No Especificado")
        movs = movements_by_ot.get(o.idordentrabajo, [])
        item = compute_order_priority(o, c_name, movs)
        scored_items.append(item)

    scored_items.sort(key=lambda x: x["score"], reverse=True)
    return scored_items[:limit]


def calculate_machine_workloads(machines: list, movements: list, weekly_capacity_hours: float = 80.0) -> List[Dict[str, Any]]:
    """
    Computes capacity utilization and identifies bottlenecks for all machines.
    Utilization % = (Total Allocated Hours / Capacity Hours) * 100
    Bottleneck if utilization > 100%.
    """
    workloads = {m.idmaquina: {"machine": m, "load_hours": 0.0, "mov_count": 0} for m in machines}
    
    for mov in movements:
        if mov.idmaquina and mov.idmaquina in workloads:
            dur = mov.duracion_horas if mov.duracion_horas > 0 else 8.0
            workloads[mov.idmaquina]["load_hours"] += dur
            workloads[mov.idmaquina]["mov_count"] += 1

    results = []
    for m_id, data in workloads.items():
        m = data["machine"]
        load = round(data["load_hours"], 1)
        utilization = round((load / weekly_capacity_hours) * 100.0, 1)
        is_bottleneck = utilization > 100.0
        results.append({
            "idmaquina": m.idmaquina,
            "nombremaquina": m.nombremaquina or m.codigomaquina or f"Máquina #{m.idmaquina}",
            "codigomaquina": m.codigomaquina or f"M-{m.idmaquina}",
            "load_hours": load,
            "capacity_hours": weekly_capacity_hours,
            "utilization": utilization,
            "is_bottleneck": is_bottleneck,
            "mov_count": data["mov_count"],
        })

    results.sort(key=lambda x: x["utilization"], reverse=True)
    return results
