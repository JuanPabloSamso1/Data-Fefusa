"""
Carga y join de los CSV en DataFrames enriquecidos.
Se usa @st.cache_data para no re-leer en cada interacción.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

CSV_DIR = Path(__file__).parent.parent / "csv"


def _csv_signature() -> tuple:
    """
    Genera una firma estable de los CSV consumidos por el dashboard.
    Si cambia un archivo (mtime/tamaño), se invalida el caché.
    """
    tracked_files = [
        "eventos.csv",
        "partidos.csv",
        "equipos.csv",
        "torneos.csv",
        "personas.csv",
        "jugadores.csv",
        "cuerpo_tecnico.csv",
    ]

    signature = []
    for filename in tracked_files:
        path = CSV_DIR / filename
        if path.exists():
            stat = path.stat()
            signature.append((filename, stat.st_mtime_ns, stat.st_size))
        else:
            signature.append((filename, None, None))

    return tuple(signature)


@st.cache_data
def _load_data_cached(_signature: tuple):
    """
    Lee los CSVs y devuelve DataFrames con joins ya aplicados:
      - eventos_raw  : eventos + nombre equipo, persona, torneo, jornada
      - partidos_raw : partidos + nombre equipo local/visitante, torneo
      - personas, equipos, torneos : tablas de referencia limpias

    Mantiene alias legacy `jugador` para no romper componentes existentes.
    """
    eventos = pd.read_csv(CSV_DIR / "eventos.csv")
    partidos = pd.read_csv(CSV_DIR / "partidos.csv")
    equipos = pd.read_csv(CSV_DIR / "equipos.csv")
    torneos = pd.read_csv(CSV_DIR / "torneos.csv")

    personas_path = CSV_DIR / "personas.csv"
    if personas_path.exists():
        personas = pd.read_csv(personas_path)
    else:
        # Backward compatibility: construir personas desde jugadores/cuerpo_tecnico
        jugadores = pd.read_csv(CSV_DIR / "jugadores.csv") if (CSV_DIR / "jugadores.csv").exists() else pd.DataFrame(columns=["id", "equipo_id", "nombre"])
        staff = pd.read_csv(CSV_DIR / "cuerpo_tecnico.csv") if (CSV_DIR / "cuerpo_tecnico.csv").exists() else pd.DataFrame(columns=["id", "equipo_id", "nombre", "rol"])

        jugadores = jugadores.copy()
        jugadores["tipo_persona"] = "JUGADOR"
        jugadores["rol_ct"] = None

        staff = staff.rename(columns={"rol": "rol_ct"}).copy()
        staff["tipo_persona"] = "CT"

        personas = pd.concat([
            jugadores[["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"]],
            staff[["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"]],
        ], ignore_index=True).drop_duplicates(subset=["id"], keep="last")

    # Normalizar columna FK de eventos: persona_id (nuevo) o jugador_id (legacy)
    if "persona_id" not in eventos.columns and "jugador_id" in eventos.columns:
        eventos = eventos.rename(columns={"jugador_id": "persona_id"})

    # ── Enriquecer eventos ──────────────────────────────────────────────────
    eventos = eventos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_id", "nombre": "equipo"}),
        on="equipo_id", how="left"
    )
    eventos = eventos.merge(
        personas[["id", "nombre", "tipo_persona", "rol_ct"]].rename(columns={"id": "persona_id", "nombre": "persona"}),
        on="persona_id", how="left"
    )
    # Alias legacy de dashboard + etiqueta de tipo de persona
    eventos["persona_nombre_tipo"] = eventos.apply(
        lambda r: f"{r['persona']} ({r['tipo_persona']})" if pd.notna(r.get("persona")) and pd.notna(r.get("tipo_persona")) else r.get("persona"),
        axis=1
    )
    eventos["jugador"] = eventos.get("persona_nombre_tipo")

    eventos = eventos.merge(
        partidos[["id", "torneo_id", "jornada"]].rename(columns={"id": "partido_id"}),
        on="partido_id", how="left"
    )
    eventos = eventos.merge(
        torneos[["id", "nombre", "temporada"]].rename(columns={"id": "torneo_id", "nombre": "categoria"}),
        on="torneo_id", how="left"
    )
    if "temporada" in eventos.columns:
        eventos["temporada"] = eventos["temporada"].apply(lambda x: str(x).split(" - ")[-1] if pd.notna(x) else x)

    # ── Enriquecer partidos ─────────────────────────────────────────────────
    partidos = partidos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_local_id", "nombre": "equipo_local"}),
        on="equipo_local_id", how="left"
    )
    partidos = partidos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_visitante_id", "nombre": "equipo_visitante"}),
        on="equipo_visitante_id", how="left"
    )
    partidos = partidos.merge(
        torneos[["id", "nombre", "temporada"]].rename(columns={"id": "torneo_id", "nombre": "categoria"}),
        on="torneo_id", how="left"
    )
    if "temporada" in partidos.columns:
        partidos["temporada"] = partidos["temporada"].apply(lambda x: str(x).split(" - ")[-1] if pd.notna(x) else x)

    return eventos, partidos, personas, equipos, torneos


def load_data():
    """Wrapper no cacheado: invalida cache automáticamente cuando cambian los CSV."""
    return _load_data_cached(_csv_signature())
