# SISTEMA DE PLANIFICACIÓN INDUSTRIAL PARA BOMBAS HIDRÁULICAS (POC)

Sistema profesional de analítica, priorización y secuenciamiento para talleres de reparación y fabricación de bombas hidráulicas mineras. Desarrollado con Django 5.1, Pandas, NumPy y soporte nativo dual para desarrollo local con **SQLite (Datos Sintéticos)** y validación operacional con **PostgreSQL (Datos Reales de Solo Lectura)**.

---

## 1. OBJETIVO PRINCIPAL

El sistema soporta dos fuentes de datos intercambiables mediante una **única variable de entorno explícita**:

* **MODO 0 (Por defecto)**: `USE_POSTGRES_REAL=0`
  * Base de datos: **SQLite** (`db.sqlite3`).
  * Entorno: Desarrollo, pruebas unitarias, experimentación y POC local offline.
  * Datos: Datos industriales sintéticos reproducibles (más de 200 órdenes y 3.000 movimientos).
* **MODO 1**: `USE_POSTGRES_REAL=1`
  * Base de datos: **PostgreSQL** (`Npdstrazabilidad`).
  * Entorno: Validación, análisis de planta y benchmarking con información operacional real.
  * Seguridad: **Estricto modo de SOLO LECTURA** sobre tablas `mct_*` (esquema `traking`).

El cambio entre ambos escenarios **no requiere modificar ninguna línea de código Python**.

---

## 2. ARQUITECTURA DE SOFTWARE

El sistema aplica arquitectura limpia en capas, desacoplando la lógica de negocio y las fórmulas de despacho del motor de base de datos subyacente:

```text
                         ┌────────────────────────────────────────┐
                         │           Django Web & UI              │
                         │  (Inspirado en template/IMG-*.jpg)     │
                         └───────────────────┬────────────────────┘
                                             │
                         ┌───────────────────▼────────────────────┐
                         │         Application Services           │
                         │    (Analytics, Planning, Quality)      │
                         └───────────────────┬────────────────────┘
                                             │
                         ┌───────────────────▼────────────────────┐
                         │              Django ORM                │
                         │        ReadOnlyPostgresRouter          │
                         └─────────┬────────────────────┬─────────┘
                                   │                    │
                  USE_POSTGRES_REAL=0                  USE_POSTGRES_REAL=1
                                   │                    │
                                   ▼                    ▼
                             ┌───────────┐        ┌───────────┐
                             │  SQLite   │        │PostgreSQL │
                             │(Sintético)│        │  (Real)   │
                             │db.sqlite3 │        │traking.mct│
                             └─────┬─────┘        └─────┬─────┘
                                   │                    │
                                   │             [ SOLO LECTURA ]
                                   │                    │
                                   └─────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │   Analytics / KPIs  │
                                  │  Pandas / NumPy     │
                                  │  WSPT & Slack Index │
                                  │  poc_* (Managed)    │
                                  └─────────────────────┘
```

### Capas del Sistema:
1. **Presentación (`templates/`, `static/`)**: Vistas delgadas, diseño industrial moderno responsive idéntico a la plantilla de referencia visual.
2. **Servicios de Aplicación (`apps/*/services.py`)**: Orquestación de casos de uso, transformaciones Pandas/NumPy, diagnósticos y auditorías.
3. **Dominio & Fórmulas (`apps/planning/engine.py`)**: Fórmulas puras desacopladas (Holguras, Critical Ratio, WSPT, Capacidad y Cuellos de Botella).
4. **Acceso a Datos & Seguridad (`apps/operational/`, `config/database.py`)**: Mapeo ORM (`managed = False` para `mct_*`, `managed = True` para `poc_*`) y router de protección de solo lectura.

---

## 3. REQUISITOS DEL SISTEMA

* **Sistema Operativo**: Windows 10/11, Linux o macOS.
* **Python**: 3.11, 3.12, 3.13 o 3.14.
* **PostgreSQL (Opcional para Modo 1)**: Versión 14 a 18 (instancia local o remota con base `Npdstrazabilidad`).
* **Librerías principales**:
  * `Django>=5.1,<5.2`
  * `psycopg[binary]>=3.1` (Driver oficial PostgreSQL 3)
  * `pandas>=2.0`
  * `numpy>=1.26`
  * `python-dotenv>=1.0`

---

## 4. INSTALACIÓN RÁPIDA

1. Clonar o abrir el directorio del proyecto:
   ```powershell
   cd c:\Users\amino\Documents\Desarrollo\Python\Planificador
   ```

2. Crear y activar el entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instalar dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

4. Crear el archivo de configuración `.env` a partir de la plantilla:
   ```powershell
   Copy-Item .env.example .env
   ```

---

## 5. CONFIGURACIÓN (`.env`)

El archivo `.env` centraliza toda la configuración sin exponer contraseñas en Git:

```env
# 0 = SQLite + sintético (default) | 1 = PostgreSQL real
USE_POSTGRES_REAL=0

# Parámetros PostgreSQL real (Npdstrazabilidad)
POSTGRES_DB=Npdstrazabilidad
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SCHEMA=traking

# Django
SECRET_KEY=clave-secreta-industrial-poc-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **IMPORTANTE**: La variable `USE_POSTGRES_REAL=0` viene predeterminada para que el proyecto siempre inicie de manera segura en SQLite.

---

## 6. MODO 0: SQLITE Y DATOS SINTÉTICOS

### Preparación y Poblado Inicial
Para ejecutar el sistema en desarrollo local con SQLite:

1. Aplicar migraciones iniciales de las tablas propias de la POC (`poc_*`):
   ```powershell
   python manage.py migrate
   ```

2. Generar el dataset industrial sintético:
   ```powershell
   python manage.py seed_synthetic_data --reset --count 200
   ```

3. Iniciar el servidor de desarrollo:
   ```powershell
   python manage.py runserver
   ```
   Abrir en el navegador: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Características de los Datos Sintéticos:
* Generación determinista y reproducible con semilla (`seed = 42`).
* 200 Órdenes de trabajo de bombas hidráulicas (Warman, Sulzer, Gorman-Rupp, Flowserve, KSB).
* Clientes mineros reales (Codelco Andina, Minera Escondida BHP, Los Pelambres, Anglo American, Collahuasi, etc.).
* Más de 600 partes y hojas de ruta.
* Más de 3.000 movimientos de taller asociados a máquinas y operadores.
* Casos normales y anómalos: movimientos abiertos, bloqueos operacionales, reprocesos, órdenes atrasadas con holgura negativa y urgencias de parada de planta.

---

## 7. MODO 1: POSTGRESQL REAL (SOLO LECTURA)

### Conmutación a PostgreSQL Real
1. Detener Django si está corriendo (`Ctrl + C`).
2. Abrir `.env` y cambiar:
   ```env
   USE_POSTGRES_REAL=1
   ```
3. Verificar la configuración de conexión:
   ```powershell
   python manage.py check
   ```
4. Iniciar el servidor:
   ```powershell
   python manage.py runserver
   ```
5. Confirmar en la interfaz web:
   * El banner superior advertirá: `⚠️ ATENCIÓN: Conectado a PostgreSQL con DATOS REALES (Solo Lectura)`.
   * El indicador del navbar mostrará: `● POSTGRESQL / DATOS REALES`.
   * Puede revisar el estado técnico en: [http://127.0.0.1:8000/quality/database/](http://127.0.0.1:8000/quality/database/)

### Volver a SQLite
1. Detener Django (`Ctrl + C`).
2. Abrir `.env` y reponer:
   ```env
   USE_POSTGRES_REAL=0
   ```
3. Iniciar de nuevo:
   ```powershell
   python manage.py runserver
   ```

---

## 8. PROTOCOLO DE SEGURIDAD Y PROTECCIÓN DE DATOS REALES

Cuando `USE_POSTGRES_REAL=1` está activo:
1. **Solo Lectura Enforzado (`ReadOnlyPostgresRouter`)**: Cualquier intento de ejecutar `INSERT`, `UPDATE`, `DELETE`, `DROP` o `ALTER` sobre tablas `mct_*` lanza inmediatamente `django.core.exceptions.PermissionDenied`.
2. **Bloqueo de Seed**: El comando `seed_synthetic_data` detecta si PostgreSQL está activo y **aborta de inmediato** con error para prevenir sobreescrituras accidentales.
3. **Tablas no gestionadas (`managed = False`)**: Django jamás intentará alterar el DDL de las tablas operacionales en PostgreSQL.
4. **Protección de Datos Personales**: Los números de RUT de operadores nunca son desplegados en la interfaz gráfica.
5. **Sin contraseñas en código**: La contraseña de PostgreSQL reside exclusivamente en el archivo `.env`, excluido del control de versiones mediante `.gitignore`.

---

## 9. MAPEO DE TABLAS OPERACIONALES (MCT)

| Tabla PostgreSQL (`traking.mct_*`) | Registros Reales | Propósito en el Sistema |
|---|---|---|
| `mct_ordentrabajo` | 4.583 | Órdenes maestras de bombas, clientes, fechas comprometidas y prioridades. |
| `mct_ordentrabajoparte` | 84.554 | Desglose de piezas y componentes asociados a cada OT. |
| `mct_componente` | 267 | Catálogo de componentes (Impulsores, Carcasas, Ejes, Rodamientos). |
| `mct_parte` | 426 | Partes físicas registradas. |
| `mct_hojaruta` | 65.000 | Trazabilidad de fabricación y reparación por ítem. |
| `mct_movimientoordentrabajo` | 405.953 | Registro de tiempos, máquinas, operadores y eventos en taller. |
| `mct_maquina` | 72 | Puestos de trabajo de mecanizado CNC, tornos, fresas y bancos de prueba. |
| `mct_operador` | 503 | Maestros y técnicos de maestranza. |
| `mct_progavisos` | 46.961 | Fechas planificadas vs fechas reales para cálculo de SLA y OTD. |
| `mct_movimientobloqueo` | 160 | Detenciones por reproceso, falta de material o no conformidad. |

---

## 10. RUTAS Y PANTALLAS PRINCIPALES

* `/` : **Dashboard Ejecutivo** (Idéntico a la plantilla de referencia en `template/IMG-20261004-WA0000.jpg`).
* `/operaciones/ordenes/` : Catálogo y buscador de Órdenes de Trabajo.
* `/operaciones/ordenes/<id>/` : Trazabilidad detallada OT → Partes → Hojas de Ruta → Movimientos.
* `/operaciones/movimientos/` : Auditoría de movimientos de taller y eventos abiertos.
* `/analytics/estadisticas/` : Distribución estadística (Media, P50, P75, P90, P95) con Pandas/NumPy.
* `/analytics/desviaciones/` : Cumplimiento de SLAs y desviaciones en días.
* `/planning/priorizacion/` : Ranking completo de priorización inteligente multicriterio.
* `/planning/secuencia/` : Secuencia de taller, cálculo de Makespan y fechas estimadas.
* `/planning/capacidad/` : Análisis de utilización de máquinas y cuellos de botella (> 100%).
* `/planning/simulacion/` : Simulador What-If de inserción de OT urgente y desplazamiento de carga.
* `/quality/` : Diagnóstico de gobernanza y calidad de datos.
* `/quality/database/` : Estado técnico de la base de datos (Motor, host, puerto, conteos).
* `/quality/database/mct/` : Explorador de tablas MCT con paginación y conteo de nulos.
* `/quality/database/compare/` : Comparador dinámico de registros SQLite vs PostgreSQL.
* `/quality/relations/` : Matriz de validación de las 9 relaciones del modelo.

---

## 11. EJECUCIÓN DE PRUEBAS AUTOMATIZADAS

El proyecto incluye 24 pruebas automatizadas que cubren configuración, conmutación, datos sintéticos, seguridad de solo lectura, validación relacional y compatibilidad de vistas:

```powershell
python manage.py test tests
```

Salida esperada:
```text
Ran 24 tests in 2.209s
OK
```

---

## 12. GUÍA DE RESOLUCIÓN DE PROBLEMAS (TROUBLESHOOTING)

* **PostgreSQL no conecta (`psycopg.OperationalError`)**:
  * Compruebe que el servicio `postgresql-x64-18` esté corriendo en Windows (`Get-Service *postgres*`).
  * Verifique que el puerto sea `5432` y el usuario sea `postgres`.
  * Confirme que la base `Npdstrazabilidad` exista.
* **SQLite no contiene datos sintéticos**:
  * Ejecute `python manage.py seed_synthetic_data --reset --count 200`.
* **Error de tabla inexistente `poc_planificacion` en PostgreSQL**:
  * Ejecute `python manage.py migrate` con `USE_POSTGRES_REAL=1` para que Django inicialice las tablas de gestión de la POC en PostgreSQL. Las tablas operacionales `mct_*` permanecerán intactas.
* **El comando seed arroja `CommandError`**:
  * Es el sistema de seguridad protegiendo los datos reales. Asegúrese de que `USE_POSTGRES_REAL=0` esté configurado en `.env` antes de regenerar datos sintéticos.

---

## 13. ARQUITECTURA FUTURA

Para etapas posteriores a la POC, la arquitectura está preparada para incorporar:
1. Conexión de réplica de lectura dedicada en PostgreSQL para faenas distribuidas.
2. Motor de optimización MILP (Programación Lineal Entera Mixta) con PuLP/OR-Tools.
3. Sincronización continua de eventos mediante Change Data Capture (CDC).
