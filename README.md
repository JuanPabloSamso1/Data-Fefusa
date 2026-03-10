# Fefusa ETL Pipeline

Pipeline automático para scraping y carga de datos de torneos de Fútsal (Scorefy → MySQL).

---

## Requisitos previos

- Python 3.10+
- MySQL Server corriendo localmente
- El archivo `.env` correctamente configurado (ver `.env.example`)

---

## Instalación inicial

```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activar el entorno virtual
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear la base de datos y tablas (solo la primera vez)
python create_db.py
```

---

## Ejecución manual

```bash
.venv\Scripts\activate
python main.py
```

Los logs se guardan en `logs\etl.log`.

---

## Ejecución automática — Windows Task Scheduler

Para programar el pipeline para que corra automáticamente (ej: todos los días a las 6am):

1. Abrir **Programador de Tareas** (`taskschd.msc`)
2. Click en **Crear tarea básica...**
3. **Nombre**: `Fefusa ETL Pipeline`
4. **Desencadenador**: Diariamente, a las `06:00`
5. **Acción**: Iniciar un programa
   - Programa: `C:\Users\jusam\OneDrive\Escritorio\Data Fefusa\run.bat`
   - Iniciar en: `C:\Users\jusam\OneDrive\Escritorio\Data Fefusa`
6. Guardar y activar la tarea

> **Nota**: Asegurarse de que MySQL esté corriendo antes del horario programado.

---

## Estructura del proyecto

```
Data Fefusa/
├── src/
│   ├── scraper.py       # Extracción (Scorefy → JSON)
│   ├── processor.py     # Transformación (JSON → DataFrames)
│   └── db_manager.py    # Carga (DataFrames → MySQL)
├── sql/
│   └── schema.sql       # Definición de tablas y vistas
├── logs/
│   └── etl.log          # Logs de ejecución automática
├── main.py              # Punto de entrada del pipeline
├── create_db.py         # Script de inicialización de base de datos
├── run.bat              # Script para ejecución automática
├── requirements.txt     # Dependencias del proyecto
└── .env                 # Credenciales (no subir a git)
```
