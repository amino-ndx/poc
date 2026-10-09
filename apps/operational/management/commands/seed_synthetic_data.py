"""
Management command to seed realistic synthetic industrial data into SQLite.
Strictly protected against execution on PostgreSQL real database.
Optimized with transaction.atomic for blazing-fast SQLite insertion.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from config.database import is_postgres_real_mode
from apps.operational.models import (
    MctCliente,
    MctEstadoOrden,
    MctProducto,
    MctOrdenTrabajo,
    MctComponente,
    MctParte,
    MctOrdenTrabajoParte,
    MctHojaRuta,
    MctActividad,
    MctSeccion,
    MctMaquina,
    MctOperador,
    MctMovimientoOrdenTrabajo,
    MctSla,
    MctProgAvisos,
    MctMovimientoBloqueo,
)
from apps.operational.services import ensure_operational_tables_exist_in_sqlite


class Command(BaseCommand):
    help = "Genera datos sintéticos industriales para el entorno de desarrollo SQLite (POC)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Limpia los datos sintéticos existentes antes de generar los nuevos.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="Cantidad de órdenes de trabajo principales a generar (mínimo 200 por defecto).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Semilla aleatoria para garantizar reproducibilidad exacta (default: 42).",
        )

    def handle(self, *args, **options):
        # 1. STRICT SAFETY CHECK: NEVER RUN ON POSTGRESQL REAL
        if is_postgres_real_mode() or connection.vendor == "postgresql":
            raise CommandError(
                "La generación de datos sintéticos está permitida solamente en SQLite.\n"
                "PostgreSQL real está activo. Operación cancelada por seguridad."
            )

        reset = options["reset"]
        target_count = max(200, options["count"])
        seed_value = options["seed"]

        random.seed(seed_value)
        self.stdout.write(self.style.NOTICE(f"Iniciando generación de datos sintéticos (Semilla={seed_value})..."))

        # 2. Ensure SQLite tables exist
        ensure_operational_tables_exist_in_sqlite()

        with transaction.atomic():
            # 3. Reset if requested
            if reset:
                self.stdout.write(self.style.WARNING("Limpiando tablas operacionales sintéticas en SQLite..."))
                with connection.cursor() as cursor:
                    for tbl in [
                        "mct_movimientobloqueo",
                        "mct_progavisos",
                        "mct_movimientoordentrabajo",
                        "mct_hojaruta",
                        "mct_ordentrabajoparte",
                        "mct_parte",
                        "mct_componente",
                        "mct_ordentrabajo",
                        "mct_producto",
                        "mct_operador",
                        "mct_maquina",
                        "mct_actividad",
                        "mct_seccion",
                        "mct_sla",
                        "mct_estadoorden",
                        "mct_cliente",
                    ]:
                        cursor.execute(f"DELETE FROM {tbl};")

            # 4. Master Data Seed
            self.stdout.write("Poblando catálogos maestros industriales...")

            clientes_data = [
                (101, "Codelco División Andina", "Codelco Andina", "contacto@andina.codelco.cl"),
                (102, "Minera Escondida BHP", "Escondida BHP", "abastecimiento@bhp.com"),
                (103, "Antofagasta Minerals Los Pelambres", "Los Pelambres", "taller@aminerals.cl"),
                (104, "Anglo American Los Bronces", "Anglo Los Bronces", "mantenimiento@angloamerican.com"),
                (105, "Compañía Minera Doña Inés de Collahuasi", "Collahuasi", "compras@collahuasi.cl"),
                (106, "Sociedad Química y Minera de Chile (SQM)", "SQM Salar", "operaciones@sqm.com"),
                (107, "Teck Quebrada Blanca", "Teck QB2", "suministros@teck.com"),
                (108, "Minera Centinela", "Centinela", "mantencion@centinela.cl"),
                (109, "Lundin Mining Minera Candelaria", "Candelaria", "contacto@lundinmining.com"),
                (110, "CAP Minería Planta Magnetita", "CAP Magnetita", "planta@cap.cl"),
            ]
            for cid, name, short, email in clientes_data:
                MctCliente.objects.update_or_create(
                    idcliente=cid,
                    defaults={
                        "nombrecliente": name,
                        "nombrecorto": short,
                        "email": email,
                        "contacto": "Jefe de Mantenimiento y Confiabilidad",
                        "estado": 1,
                        "idrubro": 1,
                        "idpais": 1,
                        "idciudad": 1,
                    }
                )

            estados_data = [
                (1, "Recepción y Desarme"),
                (2, "Evaluación Técnica"),
                (3, "En Fabricación / Fundición"),
                (4, "En Mecanizado"),
                (5, "En Balanceo y Ensamble"),
                (6, "En Pruebas Hidráulicas"),
                (7, "Listo para Despacho"),
                (8, "Despachado a Faena"),
            ]
            for eid, name in estados_data:
                MctEstadoOrden.objects.update_or_create(
                    idestadoorden=eid,
                    defaults={"nombreestado": name, "estado": 1}
                )

            productos_data = [
                (201, "Bomba Warman 10/8 AH Heavy Duty Slurry", 101, 1200, 750, 45, 350),
                (202, "Bomba Warman 12/10 L Slurry Pump", 102, 1800, 680, 52, 450),
                (203, "Bomba Sulzer Ahlstar Process Pump WPP", 102, 850, 1450, 60, 200),
                (204, "Bomba Gorman-Rupp T8A3-B Autocebante", 104, 600, 1150, 38, 125),
                (205, "Bomba Flowserve Mark 3 ASME Chemical", 103, 400, 1750, 75, 90),
                (206, "Bomba KSB Meganorm Horizontal End-Suction", 105, 550, 1450, 42, 110),
                (207, "Bomba Warman 6/4 D-AH Gravel Pump", 106, 950, 900, 40, 250),
                (208, "Bomba GIW LCC Slurry Transport", 107, 2200, 600, 58, 600),
            ]
            for pid, name, cid, q, rpm, h, p in productos_data:
                MctProducto.objects.update_or_create(
                    idproducto=pid,
                    defaults={
                        "nombreproducto": name,
                        "idcliente": cid,
                        "caudal": q,
                        "rpm": rpm,
                        "altura": h,
                        "potencia": p,
                        "estado": 1,
                    }
                )

            componentes_data = [
                (1, "Impulsor Cerrado Alto Cromo", True, True),
                (2, "Carcasa Voluta Blindada", True, True),
                (3, "Eje Principal Acero 4340", False, True),
                (4, "Caja de Rodamientos Heavy Duty", True, True),
                (5, "Prensaestopas y Camisa Protectora", False, True),
                (6, "Plato de Succión y Liners", True, True),
                (7, "Tapa Trasera y Liners de Revestimiento", True, True),
                (8, "Anillo Expulsor Dinámico", False, True),
            ]
            for cid, name, fresa, eva in componentes_data:
                MctComponente.objects.update_or_create(
                    idcomponente=cid,
                    defaults={"nombrecomponente": name, "aplicafresa": fresa, "aplicaevaluacion": eva, "estado": 1}
                )

            secciones_data = [
                (10, "Desarme, Limpieza y Granallado", "SEC-DES"),
                (20, "Inspección Dimensional y END", "SEC-END"),
                (30, "Fundición y Moldeo", "SEC-FUN"),
                (40, "Maestranza y Mecanizado CNC", "SEC-MEC"),
                (50, "Tratamiento Térmico y Alivio Tensiones", "SEC-TT"),
                (60, "Balanceo Dinámico ISO G2.5", "SEC-BAL"),
                (70, "Armado y Ajuste Mecánico", "SEC-ARM"),
                (80, "Banco de Pruebas Hidráulicas", "SEC-PRU"),
                (90, "Pintura y Embalaje para Minera", "SEC-PIN"),
            ]
            for sid, name, code in secciones_data:
                MctSeccion.objects.update_or_create(
                    idseccion=sid,
                    defaults={"nombreseccion": name, "codigoseccion": code, "estado": 1}
                )

            maquinas_data = [
                (1, 40, "Torno CNC Hankook ProTurn 100", "TCNC-01"),
                (2, 40, "Torno CNC Doosan Puma 480XL", "TCNC-02"),
                (3, 40, "Torno Vertical VTL YouJi 2.5m", "TVTL-01"),
                (4, 40, "Centro de Mecanizado Mazak VTC-800", "CMAZ-01"),
                (5, 40, "Fresadora CNC Correa Anayak 4m", "FCNC-01"),
                (6, 40, "Mandrinadora CNC TOS Varnsdorf", "MAND-01"),
                (7, 60, "Balanceadora Dinámica Schenck H40", "BAL-01"),
                (8, 40, "Rectificadora Cilíndrica Tacchella", "RECT-01"),
                (9, 80, "Banco de Pruebas Hidráulicas 1000m3/h", "BPRU-01"),
                (10, 50, "Horno Tratamiento Térmico Car-Bottom", "HOR-01"),
            ]
            for mid, sub, name, code in maquinas_data:
                MctMaquina.objects.update_or_create(
                    idmaquina=mid,
                    defaults={"idsubseccion": sub, "nombremaquina": name, "codigomaquina": code, "estado": 1}
                )

            operadores_data = [
                (1, "Carlos Muñoz Espinoza", 1, 40),
                (2, "Rodrigo Valenzuela Lagos", 2, 40),
                (3, "Jorge Contreras Silva", 3, 40),
                (4, "Mauricio Araya Morales", 4, 40),
                (5, "Patricio Castro Tapia", 5, 40),
                (6, "Cristián Rojas Fuentes", 6, 40),
                (7, "Fernando Sepúlveda Olivares", 7, 60),
                (8, "Luis Miranda Pizarro", 8, 40),
                (9, "Gabriel Reyes Carrasco", 9, 80),
                (10, "Marcelo Vega Gallardo", 10, 50),
                (11, "Héctor Bravo Navarrete", 1, 40),
                (12, "Alejandro Pinto Figueroa", 7, 70),
            ]
            for oid, name, mid, sec in operadores_data:
                MctOperador.objects.update_or_create(
                    idoperador=oid,
                    defaults={"nombreoperador": name, "idmaquina": mid, "idseccionprincipal": sec, "estado": 1}
                )

            actividades_data = [
                (1, "Desarme completo de bomba y lavado"),
                (2, "Inspección visual y metrología dimensional"),
                (3, "Mecanizado desbaste de impulsor"),
                (4, "Mecanizado terminación y balanceo dinámico"),
                (5, "Mecanizado bridas y ajuste carcasa voluta"),
                (6, "Fabricación / rectificado de eje 4340"),
                (7, "Tratamiento térmico de alivio de tensiones"),
                (8, "Armado de caja de rodamientos y sellos"),
                (9, "Ensamble general y prueba hidrostática"),
                (10, "Pintura poliuretano y control final"),
            ]
            for aid, name in actividades_data:
                MctActividad.objects.update_or_create(
                    idactividad=aid,
                    defaults={"nombreactividad": name, "estado": 1}
                )

            slas_data = [
                (1, "SLA 1: Desarme y Lavado Inicial", 2),
                (2, "SLA 2: Evaluación Técnica y Cotización", 3),
                (3, "SLA 3: Aprobación y Liberación por Cliente", 5),
                (4, "SLA 4: Mecanizado y Recuperación de Partes", 10),
                (5, "SLA 5: Ensamble y Ajuste Mecánico", 4),
                (6, "SLA 6: Pruebas Hidrostáticas y Dinámicas", 3),
                (7, "SLA 7: Embalaje y Despacho Final", 2),
            ]
            for sid, name, tramo in slas_data:
                MctSla.objects.update_or_create(
                    idsla=sid,
                    defaults={"nombresla": name, "diastramo": tramo, "estado": 1}
                )

            # 5. Populate Work Orders (OTs) and relational hierarchy
            self.stdout.write(f"Generando {target_count} Órdenes de Trabajo sintéticas coherentes...")

            now = datetime.now()
            base_ot_id = 30100

            # Predefined Top Benchmark Orders matching template/IMG-20261004-WA0000.jpg
            benchmark_orders = [
                (30105, 101, 201, "OT-30105 Bomba Warman Andina Retratamiento Relaves", now - timedelta(days=20), now - timedelta(hours=32), 1, "OT-CL-ANDINA-4401"),
                (30106, 102, 202, "OT-30106 Urgencia Parada de Planta Concentradora BHP", now - timedelta(days=8), now + timedelta(hours=16), 1, "OT-CL-BHP-8890"),
                (30101, 102, 203, "OT-30101 Bomba Sulzer Minera Escondida Flotación", now - timedelta(days=15), now + timedelta(hours=40), 2, "OT-CL-BHP-7712"),
                (30103, 103, 201, "OT-30103 Bomba Warman Los Pelambres Espesador", now - timedelta(days=12), now + timedelta(hours=116), 2, "OT-CL-PEL-3091"),
                (30104, 104, 204, "OT-30104 Bomba Gorman-Rupp Anglo American Los Bronces", now - timedelta(days=10), now + timedelta(hours=92), 3, "OT-CL-AALB-5521"),
                (30102, 105, 206, "OT-30102 Bomba KSB Meganorm Collahuasi Agua Industrial", now - timedelta(days=14), now + timedelta(hours=140), 3, "OT-CL-COL-1120"),
            ]

            created_ots = []
            for oid, cid, pid, name, rec, ent, prio, otcl in benchmark_orders:
                ot = MctOrdenTrabajo(
                    idordentrabajo=oid,
                    idcliente=cid,
                    idproducto=pid,
                    nombreordentrabajo=name,
                    fecharecepcion=rec,
                    fechaentrega=ent,
                    fechasolicitudentrega=ent,
                    fechacreacion=rec,
                    prioridad=prio,
                    otcliente=otcl,
                    idestadoorden=4,
                    debaja=0,
                )
                ot.save()
                created_ots.append(ot)

            # Generate additional orders up to target_count
            client_ids = [c[0] for c in clientes_data]
            product_ids = [p[0] for p in productos_data]

            for i in range(len(benchmark_orders) + 1, target_count + 1):
                oid = base_ot_id + i
                cid = random.choice(client_ids)
                pid = random.choice(product_ids)
                p_obj = MctProducto.objects.get(idproducto=pid)
                c_obj = MctCliente.objects.get(idcliente=cid)

                rec_days_ago = random.randint(5, 60)
                rec_date = now - timedelta(days=rec_days_ago)
                
                rnd = random.random()
                if rnd < 0.15:
                    due_date = now - timedelta(hours=random.randint(10, 120))
                    prio = 1
                elif rnd < 0.30:
                    due_date = now + timedelta(hours=random.randint(12, 48))
                    prio = 1
                else:
                    due_date = now + timedelta(days=random.randint(5, 25))
                    prio = random.choice([2, 3, 4])

                ot_name = f"OT-{oid} Mantenimiento {p_obj.nombreproducto.split()[0]} {p_obj.nombreproducto.split()[1]} {c_obj.nombrecorto}"
                ot = MctOrdenTrabajo(
                    idordentrabajo=oid,
                    idcliente=cid,
                    idproducto=pid,
                    nombreordentrabajo=ot_name,
                    fecharecepcion=rec_date,
                    fechaentrega=due_date,
                    fechasolicitudentrega=due_date,
                    fechacreacion=rec_date,
                    prioridad=prio,
                    otcliente=f"OT-CL-{oid}",
                    idestadoorden=random.randint(1, 7),
                    debaja=0,
                )
                ot.save()
                created_ots.append(ot)

            self.stdout.write("Generando partes, hojas de ruta y movimientos asociados...")

            partes_to_create = []
            ot_partes_to_create = []
            hrs_to_create = []
            movs_to_create = []
            bloqueos_to_create = []
            progavisos_to_create = []

            mov_counter = 1000
            hr_counter = 5000
            otp_counter = 8000
            parte_counter = 9000
            bloqueo_counter = 200

            for ot in created_ots:
                num_components = random.randint(2, 4)
                selected_comp_ids = random.sample(range(1, 9), num_components)

                for item_idx, comp_id in enumerate(selected_comp_ids, start=1):
                    otp_counter += 1
                    parte_counter += 1
                    comp_name = componentes_data[comp_id - 1][1]

                    partes_to_create.append(MctParte(
                        idparte=parte_counter,
                        nombreparte=f"{comp_name} OT-{ot.idordentrabajo}",
                        idcomponente=comp_id,
                        costofabricacion=random.randint(500000, 3500000),
                        esprincipal=1 if item_idx == 1 else 0,
                        escritico=1 if comp_id in (1, 2, 3) else 0,
                        estado=1,
                    ))

                    ot_partes_to_create.append(MctOrdenTrabajoParte(
                        idordentrabajoparte=otp_counter,
                        idordentrabajo=ot.idordentrabajo,
                        idparte=parte_counter,
                        idcomponente=comp_id,
                        itemparte=item_idx,
                        itemcorr=item_idx,
                    ))

                    hr_counter += 1
                    cod_hr = f"HR-{ot.idordentrabajo}-{item_idx:02d}"
                    hrs_to_create.append(MctHojaRuta(
                        idhojaruta=hr_counter,
                        idordentrabajoparte=otp_counter,
                        codhojaruta=cod_hr,
                        fechacreacion=ot.fechacreacion,
                        modalidad=1,
                    ))

                    act_sequence = [1, 2, random.choice([3, 5]), 4, 9]
                    curr_time = ot.fecharecepcion or (now - timedelta(days=10))

                    for step_idx, act_id in enumerate(act_sequence, start=1):
                        mov_counter += 1
                        act_dur_hours = random.choice([2.5, 4.0, 6.5, 8.0, 12.0, 16.5])
                        m_start = curr_time
                        m_end = curr_time + timedelta(hours=act_dur_hours)

                        # Anomaly injection:
                        # - 1 open movement for benchmark POC
                        is_open = (ot.idordentrabajo == 30105 and step_idx == 3)
                        if is_open:
                            m_end = None

                        maq_id = random.randint(1, 10) if act_id in (3, 4, 5) else None
                        op_id = random.randint(1, 12)

                        has_reproceso = (random.random() < 0.08)
                        repro_sol = "S" if has_reproceso else ""
                        repro_cc = "REPROCESO POR AJUSTE TOLERANCIA" if has_reproceso else ""

                        movs_to_create.append(MctMovimientoOrdenTrabajo(
                            idmovimientoordentrabajo=mov_counter,
                            idordentrabajo=ot.idordentrabajo,
                            idhojaruta=hr_counter,
                            codhojaruta=cod_hr,
                            idparte=parte_counter,
                            idmaquina=maq_id,
                            idseccion=40 if maq_id else 10,
                            idactividad=act_id,
                            fechainicio=m_start,
                            fechatermino=m_end,
                            tiempotrabajado=None,
                            estadoactividad=1 if not is_open else 2,
                            idoperador=op_id,
                            reprocesosol=repro_sol,
                            reprocesocc=repro_cc,
                            checkncbomba=has_reproceso,
                        ))

                        if has_reproceso and random.random() < 0.4:
                            bloqueo_counter += 1
                            bloqueos_to_create.append(MctMovimientoBloqueo(
                                idmovimientobloqueo=bloqueo_counter,
                                codhojaruta=cod_hr,
                                idoperador=op_id,
                                idseccion=40,
                                idmotivobloqueo=1,
                                fecharebloqueo=m_start,
                                fechadesbloqueo=m_start + timedelta(hours=random.randint(4, 24)),
                                estadobloqueo=1,
                            ))

                        if m_end:
                            curr_time = m_end + timedelta(hours=random.uniform(0.5, 4.0))

                sla_start = ot.fecharecepcion or (now - timedelta(days=10))
                for sla_id in range(1, 6):
                    sla_tramo_days = random.randint(2, 6)
                    sla_end = sla_start + timedelta(days=sla_tramo_days)
                    dev = random.choice([-1, 0, 0, 1, 2, 4])
                    real_end = sla_end + timedelta(days=dev) if sla_end < now else None

                    progavisos_to_create.append(MctProgAvisos(
                        idordentrabajo=ot.idordentrabajo,
                        idsla=sla_id,
                        fecha_inicio=sla_start,
                        fecha_termino=sla_end,
                        fecha_inicio_aviso=sla_start,
                        dias_tramo=sla_tramo_days,
                        estado=2 if real_end else 1,
                        fecha_real_termino=real_end,
                        ordenproceso=sla_id,
                    ))
                    sla_start = sla_end

            # Fast bulk insertion
            MctParte.objects.bulk_create(partes_to_create)
            MctOrdenTrabajoParte.objects.bulk_create(ot_partes_to_create)
            MctHojaRuta.objects.bulk_create(hrs_to_create)
            MctMovimientoOrdenTrabajo.objects.bulk_create(movs_to_create)
            MctMovimientoBloqueo.objects.bulk_create(bloqueos_to_create)
            MctProgAvisos.objects.bulk_create(progavisos_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"¡Datos sintéticos generados exitosamente!\n"
            f"- Órdenes de Trabajo: {len(created_ots)}\n"
            f"- Partes: {len(partes_to_create)}\n"
            f"- Hojas de Ruta: {len(hrs_to_create)}\n"
            f"- Movimientos: {len(movs_to_create)}\n"
            f"- Bloqueos: {len(bloqueos_to_create)}\n"
            f"- ProgAvisos (SLAs): {len(progavisos_to_create)}\n"
            f"Base de datos activa: SQLite ({connection.settings_dict['NAME']})"
        ))
