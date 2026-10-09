"""
Operational Models mapping legacy operational tables (mct_*).
These models represent read-only operational entities in PostgreSQL (schema: traking).
In SQLite mode, these tables are populated with rich synthetic industrial data.
"""
from django.db import models


class MctCliente(models.Model):
    idcliente = models.BigIntegerField(primary_key=True)
    rut = models.CharField(max_length=50, null=True, blank=True)
    digito = models.CharField(max_length=5, null=True, blank=True)
    nombrecliente = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    idrubro = models.BigIntegerField(null=True, blank=True)
    idpais = models.BigIntegerField(null=True, blank=True)
    idciudad = models.BigIntegerField(null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)
    contacto = models.CharField(max_length=255, null=True, blank=True)
    nombrecorto = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_cliente"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombrecliente or self.nombrecorto or f"Cliente #{self.idcliente}"


class MctEstadoOrden(models.Model):
    idestadoorden = models.BigIntegerField(primary_key=True)
    nombreestado = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_estadoorden"
        verbose_name = "Estado de Orden"
        verbose_name_plural = "Estados de Orden"

    def __str__(self):
        return self.nombreestado or f"Estado #{self.idestadoorden}"


class MctProducto(models.Model):
    idproducto = models.BigIntegerField(primary_key=True)
    idmodelo = models.BigIntegerField(null=True, blank=True)
    idcliente = models.BigIntegerField(null=True, blank=True)
    nombreproducto = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)
    caudal = models.BigIntegerField(null=True, blank=True)
    rpm = models.BigIntegerField(null=True, blank=True)
    altura = models.BigIntegerField(null=True, blank=True)
    potencia = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_producto"
        verbose_name = "Producto / Bomba"
        verbose_name_plural = "Productos / Bombas"

    def __str__(self):
        return self.nombreproducto or f"Producto #{self.idproducto}"


class MctOrdenTrabajo(models.Model):
    idordentrabajo = models.BigIntegerField(primary_key=True)
    idcliente = models.BigIntegerField(null=True, blank=True)
    idcotizacion = models.BigIntegerField(null=True, blank=True)
    idtipoorden = models.BigIntegerField(null=True, blank=True)
    idproducto = models.BigIntegerField(null=True, blank=True)
    nombreordentrabajo = models.CharField(max_length=255, null=True, blank=True)
    fecharecepcion = models.DateTimeField(null=True, blank=True)
    fechaentrega = models.DateTimeField(null=True, blank=True)
    fechasolicitudentrega = models.DateTimeField(null=True, blank=True)
    fechacreacion = models.DateTimeField(null=True, blank=True)
    idestadoorden = models.BigIntegerField(null=True, blank=True)
    prioridad = models.IntegerField(null=True, blank=True)
    idfamilia = models.BigIntegerField(null=True, blank=True)
    otcliente = models.CharField(max_length=100, null=True, blank=True)
    contactocliente = models.CharField(max_length=255, null=True, blank=True)
    idusuario = models.BigIntegerField(null=True, blank=True)
    debaja = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_ordentrabajo"
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"

    def __str__(self):
        return f"OT-{self.idordentrabajo} {self.nombreordentrabajo or ''}"


class MctComponente(models.Model):
    idcomponente = models.BigIntegerField(primary_key=True)
    nombrecomponente = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)
    cantidad = models.BigIntegerField(null=True, blank=True)
    aplicafresa = models.BooleanField(null=True, blank=True)
    aplicaevaluacion = models.BooleanField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_componente"
        verbose_name = "Componente"
        verbose_name_plural = "Componentes"

    def __str__(self):
        return self.nombrecomponente or f"Componente #{self.idcomponente}"


class MctParte(models.Model):
    idparte = models.BigIntegerField(primary_key=True)
    nombreparte = models.CharField(max_length=255, null=True, blank=True)
    idcomponente = models.BigIntegerField(null=True, blank=True)
    idhojaruta = models.BigIntegerField(null=True, blank=True)
    idmaterial = models.BigIntegerField(null=True, blank=True)
    idtipoparte = models.BigIntegerField(null=True, blank=True)
    costofabricacion = models.IntegerField(null=True, blank=True)
    esprincipal = models.BigIntegerField(null=True, blank=True)
    escritico = models.BigIntegerField(null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_parte"
        verbose_name = "Parte"
        verbose_name_plural = "Partes"

    def __str__(self):
        return self.nombreparte or f"Parte #{self.idparte}"


class MctOrdenTrabajoParte(models.Model):
    idordentrabajoparte = models.BigIntegerField(primary_key=True)
    idordentrabajo = models.BigIntegerField(null=True, blank=True)
    idparte = models.BigIntegerField(null=True, blank=True)
    idcomponente = models.BigIntegerField(null=True, blank=True)
    itemparte = models.BigIntegerField(null=True, blank=True)
    itemcorr = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_ordentrabajoparte"
        verbose_name = "OT Parte"
        verbose_name_plural = "OT Partes"


class MctHojaRuta(models.Model):
    idhojaruta = models.BigIntegerField(primary_key=True)
    idordentrabajoparte = models.BigIntegerField(null=True, blank=True)
    codhojaruta = models.CharField(max_length=100, null=True, blank=True)
    fechacreacion = models.DateTimeField(null=True, blank=True)
    fechafundicion = models.DateTimeField(null=True, blank=True)
    modalidad = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_hojaruta"
        verbose_name = "Hoja de Ruta"
        verbose_name_plural = "Hojas de Ruta"

    def __str__(self):
        return self.codhojaruta or f"HR #{self.idhojaruta}"


class MctActividad(models.Model):
    idactividad = models.BigIntegerField(primary_key=True)
    nombreactividad = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_actividad"
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"

    def __str__(self):
        return self.nombreactividad or f"Actividad #{self.idactividad}"


class MctSeccion(models.Model):
    idseccion = models.BigIntegerField(primary_key=True)
    nombreseccion = models.CharField(max_length=255, null=True, blank=True)
    codigoseccion = models.CharField(max_length=100, null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_seccion"
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"

    def __str__(self):
        return self.nombreseccion or f"Sección #{self.idseccion}"


class MctMaquina(models.Model):
    idmaquina = models.BigIntegerField(primary_key=True)
    idsubseccion = models.BigIntegerField(null=True, blank=True)
    nombremaquina = models.CharField(max_length=255, null=True, blank=True)
    codigomaquina = models.CharField(max_length=100, null=True, blank=True)
    estado = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_maquina"
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"

    def __str__(self):
        return self.nombremaquina or self.codigomaquina or f"Máquina #{self.idmaquina}"


class MctOperador(models.Model):
    idoperador = models.BigIntegerField(primary_key=True)
    nombreoperador = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=50, null=True, blank=True)  # Protected: never show in UI
    idmaquina = models.BigIntegerField(null=True, blank=True)
    idseccionprincipal = models.BigIntegerField(null=True, blank=True)
    idperfil = models.BigIntegerField(null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_operador"
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"

    def __str__(self):
        # Confidentiality requirement: Never display RUT in representation
        return self.nombreoperador or f"Operador #{self.idoperador}"


class MctMovimientoOrdenTrabajo(models.Model):
    idmovimientoordentrabajo = models.BigIntegerField(primary_key=True)
    idordentrabajo = models.BigIntegerField(null=True, blank=True)
    idhojaruta = models.BigIntegerField(null=True, blank=True)
    codhojaruta = models.CharField(max_length=100, null=True, blank=True)
    idparte = models.BigIntegerField(null=True, blank=True)
    idmaquina = models.BigIntegerField(null=True, blank=True)
    idseccion = models.BigIntegerField(null=True, blank=True)
    idactividad = models.BigIntegerField(null=True, blank=True)
    idaccion = models.BigIntegerField(null=True, blank=True)
    fechainicio = models.DateTimeField(null=True, blank=True)
    fechatermino = models.DateTimeField(null=True, blank=True)
    codigoaccion = models.CharField(max_length=100, null=True, blank=True)
    estadoactividad = models.BigIntegerField(null=True, blank=True)
    numeroinspeccion = models.CharField(max_length=100, null=True, blank=True)
    idoperador = models.BigIntegerField(null=True, blank=True)
    tiempotrabajado = models.BigIntegerField(null=True, blank=True)
    idmotivocierre = models.BigIntegerField(null=True, blank=True)
    idcausacierre = models.BigIntegerField(null=True, blank=True)
    observacion = models.CharField(max_length=500, null=True, blank=True)
    reprocesosol = models.CharField(max_length=100, null=True, blank=True)
    reprocesocc = models.CharField(max_length=100, null=True, blank=True)
    checkncbomba = models.BooleanField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_movimientoordentrabajo"
        verbose_name = "Movimiento Orden Trabajo"
        verbose_name_plural = "Movimientos Orden Trabajo"

    @property
    def duracion_horas(self) -> float:
        """
        Calculates duration in hours.
        Falls back to fechatermino - fechainicio when tiempotrabajado is NULL.
        """
        if self.fechainicio and self.fechatermino:
            diff = self.fechatermino - self.fechainicio
            return max(0.0, round(diff.total_seconds() / 3600.0, 2))
        if self.tiempotrabajado is not None and self.tiempotrabajado > 0:
            return round(self.tiempotrabajado / 3600.0, 2)
        return 0.0

    @property
    def es_abierto(self) -> bool:
        return self.fechainicio is not None and self.fechatermino is None


class MctSla(models.Model):
    idsla = models.BigIntegerField(primary_key=True)
    nombresla = models.CharField(max_length=255, null=True, blank=True)
    diastramo = models.BigIntegerField(null=True, blank=True)
    escritico = models.BigIntegerField(null=True, blank=True)
    estado = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_sla"
        verbose_name = "SLA"
        verbose_name_plural = "SLAs"

    def __str__(self):
        return self.nombresla or f"SLA #{self.idsla}"


class MctProgAvisos(models.Model):
    idprogaviso = models.BigAutoField(primary_key=True)
    idordentrabajo = models.BigIntegerField()
    idsla = models.BigIntegerField()
    fecha_inicio = models.DateTimeField()
    fecha_termino = models.DateTimeField()
    fecha_inicio_aviso = models.DateTimeField(null=True, blank=True)
    dias_tramo = models.IntegerField(null=True, blank=True)
    estado = models.IntegerField(null=True, blank=True)
    fecha_real_termino = models.DateTimeField(null=True, blank=True)
    ordenproceso = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_progavisos"
        verbose_name = "Programación Aviso"
        verbose_name_plural = "Programación Avisos"


class MctMovimientoBloqueo(models.Model):
    idmovimientobloqueo = models.BigIntegerField(primary_key=True)
    idregistrotrabajo = models.BigIntegerField(null=True, blank=True)
    codhojaruta = models.CharField(max_length=100, null=True, blank=True)
    idoperador = models.BigIntegerField(null=True, blank=True)
    idseccion = models.BigIntegerField(null=True, blank=True)
    idmotivobloqueo = models.BigIntegerField(null=True, blank=True)
    fecharebloqueo = models.DateTimeField(null=True, blank=True)
    fechadesbloqueo = models.DateTimeField(null=True, blank=True)
    idoperadordesbloquea = models.BigIntegerField(null=True, blank=True)
    estadobloqueo = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mct_movimientobloqueo"
        verbose_name = "Movimiento Bloqueo"
        verbose_name_plural = "Movimientos Bloqueo"
