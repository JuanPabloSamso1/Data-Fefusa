"""
Carga y join de los CSV en DataFrames enriquecidos.
Se usa @st.cache_data para no re-leer en cada interacción.
"""
from __future__ import annotations

from datetime import datetime
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


def get_last_data_update() -> datetime | None:
    """Retorna la última fecha de modificación entre los CSV consumidos."""
    mtimes = [mtime_ns for _, mtime_ns, _ in _csv_signature() if mtime_ns]
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes) / 1_000_000_000)


def _normalize_events_frame(eventos: pd.DataFrame) -> pd.DataFrame:
    """
    Unifica claves legacy de persona/jugador y colapsa eventos duplicados por `id`.
    Algunos CSVs repiten el mismo evento dos veces: una fila con `jugador_id` y otra
    con `persona_id`. El dashboard debe tratarlos como un unico evento.
    """
    if eventos.empty:
        return eventos.copy()

    out = eventos.copy()

    for col in ["id", "partido_id", "equipo_id", "jugador_id", "persona_id", "tipo_evento", "periodo"]:
        if col in out.columns:
            out[col] = out[col].replace("", pd.NA)

    if "persona_id" not in out.columns and "jugador_id" in out.columns:
        out = out.rename(columns={"jugador_id": "persona_id"})
    elif "jugador_id" in out.columns:
        if "persona_id" not in out.columns:
            out["persona_id"] = out["jugador_id"]
        else:
            out["persona_id"] = out["persona_id"].fillna(out["jugador_id"])
        out["jugador_id"] = out["jugador_id"].fillna(out["persona_id"])

    helper_cols: list[str] = []
    if "id" in out.columns:
        if "persona_id" in out.columns:
            out["_persona_rank"] = out["persona_id"].notna().astype(int)
            helper_cols.append("_persona_rank")
        if "jugador_id" in out.columns:
            out["_jugador_rank"] = out["jugador_id"].notna().astype(int)
            helper_cols.append("_jugador_rank")

        if helper_cols:
            out = out.sort_values(["id", *helper_cols], ascending=[True, *([False] * len(helper_cols))])
        out = out.drop_duplicates(subset=["id"], keep="first")

    return out.drop(columns=helper_cols, errors="ignore")


@st.cache_data
def _load_data_cached(_signature: tuple):
    """
    Lee los CSVs y devuelve DataFrames con joins ya aplicados:
      - eventos_raw  : eventos + nombre equipo, persona, torneo, jornada
      - partidos_raw : partidos + nombre equipo local/visitante, torneo
      - personas, equipos, torneos : tablas de referencia limpias

    Mantiene alias legacy `jugador` para no romper componentes existentes.
    """
    eventos = _normalize_events_frame(pd.read_csv(CSV_DIR / "eventos.csv"))
    partidos = pd.read_csv(CSV_DIR / "partidos.csv")
    equipos = pd.read_csv(CSV_DIR / "equipos.csv")
    torneos = pd.read_csv(CSV_DIR / "torneos.csv")

    personas_path = CSV_DIR / "personas.csv"
    if personas_path.exists():
        personas = pd.read_csv(personas_path).drop_duplicates(subset=["id"], keep="last")
    else:
        personas = pd.DataFrame(columns=["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"])

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
    # Alias legacy: mantener columna `jugador` con el nombre limpio (sin sufijo de tipo)
    eventos["jugador"] = eventos.get("persona")

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
