"""
POC-specific models (poc_*).
These tables are fully managed by Django migrations (managed = True).
They store prioritization parameters, generated production plans, simulation runs and audit events.
"""
from django.db import models


class PocConfigPriorizacion(models.Model):
    idconfig = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150, default="Configuración Estándar")
    peso_holgura = models.FloatField(default=0.35, help_text="Peso ponderador de holgura temporal")
    peso_criticidad_cliente = models.FloatField(default=0.25, help_text="Peso de nivel de cliente / contrato")
    peso_wspt = models.FloatField(default=0.20, help_text="Weighted Shortest Processing Time")
    peso_reproceso = models.FloatField(default=0.20, help_text="Castigo / urgencia por reproceso o bloqueo")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "poc_config_priorizacion"
        verbose_name = "Configuración Priorización"
        verbose_name_plural = "Configuraciones Priorización"

    def __str__(self):
        return f"{self.nombre} (H:{self.peso_holgura} C:{self.peso_criticidad_cliente} W:{self.peso_wspt} R:{self.peso_reproceso})"


class PocPlanificacion(models.Model):
    idplanificacion = models.BigAutoField(primary_key=True)
    codigo_plan = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    total_ordenes = models.IntegerField(default=0)
    makespan_horas = models.FloatField(default=0.0)
    cuellos_botella_detectados = models.IntegerField(default=0)
    estado = models.CharField(max_length=50, default="GENERADO")

    class Meta:
        managed = True
        db_table = "poc_planificacion"
        verbose_name = "Planificación"
        verbose_name_plural = "Planificaciones"

    def __str__(self):
        return f"{self.codigo_plan} - {self.descripcion} ({self.total_ordenes} OTs)"


class PocPlanificacionDetalle(models.Model):
    iddetalle = models.BigAutoField(primary_key=True)
    planificacion = models.ForeignKey(
        PocPlanificacion,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    idordentrabajo = models.BigIntegerField()
    nombreordentrabajo = models.CharField(max_length=255)
    cliente_nombre = models.CharField(max_length=255)
    posicion_secuencia = models.IntegerField()
    score_prioridad = models.FloatField()
    holgura_horas = models.FloatField()
    critical_ratio = models.FloatField()
    tiempo_estimado_horas = models.FloatField(default=0.0)
    fecha_inicio_programada = models.DateTimeField(null=True, blank=True)
    fecha_fin_programada = models.DateTimeField(null=True, blank=True)
    razon_principal = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = "poc_planificacion_detalle"
        verbose_name = "Detalle de Planificación"
        verbose_name_plural = "Detalles de Planificación"
        ordering = ["posicion_secuencia"]

    def __str__(self):
        return f"Pos {self.posicion_secuencia}: OT-{self.idordentrabajo} (Score: {self.score_prioridad})"


class PocSimulacion(models.Model):
    idsimulacion = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    tipo_simulacion = models.CharField(max_length=50, default="INSERCION_URGENTE")
    parametros_json = models.TextField(default="{}")
    resultado_json = models.TextField(default="{}")
    fecha_simulacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "poc_simulacion"
        verbose_name = "Simulación"
        verbose_name_plural = "Simulaciones"

    def __str__(self):
        return f"Simulación #{self.idsimulacion}: {self.nombre}"


class PocEventoPlanificacion(models.Model):
    idevento = models.BigAutoField(primary_key=True)
    tipo_evento = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "poc_evento_planificacion"
        verbose_name = "Evento de Planificación"
        verbose_name_plural = "Eventos de Planificación"

    def __str__(self):
        return f"[{self.fecha_evento:%Y-%m-%d %H:%M}] {self.tipo_evento}: {self.descripcion[:60]}"
