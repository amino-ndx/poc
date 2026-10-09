"""
Data Access and Repository Services for Operational Data (mct_*).
Centralizes queries so presentation and domain layers never query tables directly.
Works identically over SQLite and PostgreSQL.
"""
import logging
from typing import List, Dict, Any, Optional
from django.db import connection
from apps.operational.models import (
    MctOrdenTrabajo,
    MctOrdenTrabajoParte,
    MctComponente,
    MctParte,
    MctHojaRuta,
    MctMovimientoOrdenTrabajo,
    MctMaquina,
    MctOperador,
    MctProgAvisos,
    MctMovimientoBloqueo,
    MctActividad,
    MctSeccion,
    MctSla,
    MctCliente,
    MctProducto,
    MctEstadoOrden,
)

logger = logging.getLogger(__name__)


def get_clients_map() -> Dict[int, str]:
    """Returns a lookup dict mapping idcliente -> nombrecliente."""
    try:
        return {
            c.idcliente: (c.nombrecliente or c.nombrecorto or f"Cliente #{c.idcliente}")
            for c in MctCliente.objects.all()
        }
    except Exception as e:
        logger.warning("Could not fetch clients map: %s", e)
        return {}


def get_machines_map() -> Dict[int, str]:
    """Returns a lookup dict mapping idmaquina -> nombremaquina."""
    try:
        return {
            m.idmaquina: (m.nombremaquina or m.codigomaquina or f"Máquina #{m.idmaquina}")
            for m in MctMaquina.objects.all()
        }
    except Exception as e:
        logger.warning("Could not fetch machines map: %s", e)
        return {}


def get_operators_map() -> Dict[int, str]:
    """Returns a lookup dict mapping idoperador -> nombreoperador (WITHOUT RUT)."""
    try:
        return {
            o.idoperador: (o.nombreoperador or f"Operador #{o.idoperador}")
            for o in MctOperador.objects.all()
        }
    except Exception as e:
        logger.warning("Could not fetch operators map: %s", e)
        return {}


def get_activities_map() -> Dict[int, str]:
    """Returns a lookup dict mapping idactividad -> nombreactividad."""
    try:
        return {
            a.idactividad: (a.nombreactividad or f"Actividad #{a.idactividad}")
            for a in MctActividad.objects.all()
        }
    except Exception as e:
        logger.warning("Could not fetch activities map: %s", e)
        return {}


def get_components_map() -> Dict[int, str]:
    """Returns a lookup dict mapping idcomponente -> nombrecomponente."""
    try:
        return {
            c.idcomponente: (c.nombrecomponente or f"Componente #{c.idcomponente}")
            for c in MctComponente.objects.all()
        }
    except Exception as e:
        logger.warning("Could not fetch components map: %s", e)
        return {}


def get_work_orders(limit: Optional[int] = 100, search: Optional[str] = None):
    """Fetches work orders with optional search and limit."""
    qs = MctOrdenTrabajo.objects.all().order_by("-idordentrabajo")
    if search:
        qs = qs.filter(nombreordentrabajo__icontains=search)
    if limit:
        qs = qs[:limit]
    return list(qs)


def get_work_order_by_id(order_id: int) -> Optional[MctOrdenTrabajo]:
    """Fetches a single work order by its ID."""
    return MctOrdenTrabajo.objects.filter(idordentrabajo=order_id).first()


def get_order_parts_tree(order_id: int) -> List[Dict[str, Any]]:
    """
    Builds the relational hierarchy for a given OT:
    OT -> OT Parte -> Componente / Parte -> Hoja de Ruta -> Movimientos
    """
    ot_partes = list(MctOrdenTrabajoParte.objects.filter(idordentrabajo=order_id))
    parts_map = {p.idparte: p for p in MctParte.objects.all()}
    components_map = {c.idcomponente: c for c in MctComponente.objects.all()}
    machines_map = get_machines_map()
    operators_map = get_operators_map()
    activities_map = get_activities_map()

    tree = []
    for otp in ot_partes:
        comp = components_map.get(otp.idcomponente)
        parte = parts_map.get(otp.idparte)
        
        # Find hojas de ruta for this ot parte
        hrs = list(MctHojaRuta.objects.filter(idordentrabajoparte=otp.idordentrabajoparte))
        hr_items = []
        for hr in hrs:
            movs = list(MctMovimientoOrdenTrabajo.objects.filter(idhojaruta=hr.idhojaruta).order_by("fechainicio"))
            mov_items = []
            for m in movs:
                bloqueos = list(MctMovimientoBloqueo.objects.filter(codhojaruta=m.codhojaruta)) if m.codhojaruta else []
                mov_items.append({
                    "movimiento": m,
                    "actividad_nombre": activities_map.get(m.idactividad, f"Actividad #{m.idactividad}"),
                    "maquina_nombre": machines_map.get(m.idmaquina, "Sin máquina"),
                    "operador_nombre": operators_map.get(m.idoperador, "Sin operador"),
                    "duracion_horas": m.duracion_horas,
                    "bloqueos": bloqueos,
                })
            hr_items.append({
                "hoja_ruta": hr,
                "movimientos": mov_items,
            })
        
        tree.append({
            "ot_parte": otp,
            "componente": comp,
            "parte": parte,
            "hojas_ruta": hr_items,
        })
    return tree


def get_open_movements_count() -> int:
    """Returns the count of open movements (fechainicio is NOT NULL and fechatermino IS NULL)."""
    try:
        return MctMovimientoOrdenTrabajo.objects.filter(
            fechainicio__isnull=False,
            fechatermino__isnull=True
        ).count()
    except Exception as e:
        logger.warning("Error counting open movements: %s", e)
        return 0


def ensure_operational_tables_exist_in_sqlite():
    """
    Creates SQLite operational tables if they don't exist yet in db.sqlite3.
    This enables full local SQLite development with unmanaged mct_* models.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_cliente (
                idcliente INTEGER PRIMARY KEY,
                rut TEXT,
                digito TEXT,
                nombrecliente TEXT,
                telefono TEXT,
                direccion TEXT,
                email TEXT,
                idrubro INTEGER,
                idpais INTEGER,
                idciudad INTEGER,
                estado INTEGER,
                contacto TEXT,
                nombrecorto TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_estadoorden (
                idestadoorden INTEGER PRIMARY KEY,
                nombreestado TEXT,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_producto (
                idproducto INTEGER PRIMARY KEY,
                idmodelo INTEGER,
                idcliente INTEGER,
                nombreproducto TEXT,
                estado INTEGER,
                caudal INTEGER,
                rpm INTEGER,
                altura INTEGER,
                potencia INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_ordentrabajo (
                idordentrabajo INTEGER PRIMARY KEY,
                idcliente INTEGER,
                idcotizacion INTEGER,
                idtipoorden INTEGER,
                idproducto INTEGER,
                nombreordentrabajo TEXT,
                fecharecepcion TIMESTAMP,
                fechaentrega TIMESTAMP,
                fechasolicitudentrega TIMESTAMP,
                fechacreacion TIMESTAMP,
                idestadoorden INTEGER,
                prioridad INTEGER,
                idfamilia INTEGER,
                otcliente TEXT,
                contactocliente TEXT,
                idusuario INTEGER,
                debaja INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_componente (
                idcomponente INTEGER PRIMARY KEY,
                nombrecomponente TEXT,
                estado INTEGER,
                cantidad INTEGER,
                aplicafresa BOOLEAN,
                aplicaevaluacion BOOLEAN
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_parte (
                idparte INTEGER PRIMARY KEY,
                nombreparte TEXT,
                idcomponente INTEGER,
                idhojaruta INTEGER,
                idmaterial INTEGER,
                idtipoparte INTEGER,
                costofabricacion INTEGER,
                esprincipal INTEGER,
                escritico INTEGER,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_ordentrabajoparte (
                idordentrabajoparte INTEGER PRIMARY KEY,
                idordentrabajo INTEGER,
                idparte INTEGER,
                idcomponente INTEGER,
                itemparte INTEGER,
                itemcorr INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_hojaruta (
                idhojaruta INTEGER PRIMARY KEY,
                idordentrabajoparte INTEGER,
                codhojaruta TEXT,
                fechacreacion TIMESTAMP,
                fechafundicion TIMESTAMP,
                modalidad INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_actividad (
                idactividad INTEGER PRIMARY KEY,
                nombreactividad TEXT,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_seccion (
                idseccion INTEGER PRIMARY KEY,
                nombreseccion TEXT,
                codigoseccion TEXT,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_maquina (
                idmaquina INTEGER PRIMARY KEY,
                idsubseccion INTEGER,
                nombremaquina TEXT,
                codigomaquina TEXT,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_operador (
                idoperador INTEGER PRIMARY KEY,
                nombreoperador TEXT,
                rut TEXT,
                idmaquina INTEGER,
                idseccionprincipal INTEGER,
                idperfil INTEGER,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_movimientoordentrabajo (
                idmovimientoordentrabajo INTEGER PRIMARY KEY,
                idordentrabajo INTEGER,
                idhojaruta INTEGER,
                codhojaruta TEXT,
                idparte INTEGER,
                idmaquina INTEGER,
                idseccion INTEGER,
                idactividad INTEGER,
                idaccion INTEGER,
                fechainicio TIMESTAMP,
                fechatermino TIMESTAMP,
                codigoaccion TEXT,
                estadoactividad INTEGER,
                numeroinspeccion TEXT,
                idoperador INTEGER,
                tiempotrabajado INTEGER,
                idmotivocierre INTEGER,
                idcausacierre INTEGER,
                observacion TEXT,
                reprocesosol TEXT,
                reprocesocc TEXT,
                checkncbomba BOOLEAN
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_sla (
                idsla INTEGER PRIMARY KEY,
                nombresla TEXT,
                diastramo INTEGER,
                escritico INTEGER,
                estado INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_progavisos (
                idprogaviso INTEGER PRIMARY KEY AUTOINCREMENT,
                idordentrabajo INTEGER,
                idsla INTEGER,
                fecha_inicio TIMESTAMP,
                fecha_termino TIMESTAMP,
                fecha_inicio_aviso TIMESTAMP,
                dias_tramo INTEGER,
                estado INTEGER,
                fecha_real_termino TIMESTAMP,
                ordenproceso INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mct_movimientobloqueo (
                idmovimientobloqueo INTEGER PRIMARY KEY,
                idregistrotrabajo INTEGER,
                codhojaruta TEXT,
                idoperador INTEGER,
                idseccion INTEGER,
                idmotivobloqueo INTEGER,
                fecharebloqueo TIMESTAMP,
                fechadesbloqueo TIMESTAMP,
                idoperadordesbloquea INTEGER,
                estadobloqueo INTEGER
            );
        """)
