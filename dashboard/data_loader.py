"""
Carga y join de los CSV en DataFrames enriquecidos.
Se usa @st.cache_data para no re-leer en cada interacción.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

CSV_DIR = Path(__file__).parent.parent / "csv"


@st.cache_data
def load_data():
    """
    Lee los 5 CSVs y devuelve DataFrames con joins ya aplicados:
      - eventos_raw  : eventos + nombre equipo, jugador, torneo, jornada
      - partidos_raw : partidos + nombre equipo local/visitante, torneo
      - jugadores, equipos, torneos : tablas de referencia limpias
    """
    eventos   = pd.read_csv(CSV_DIR / "eventos.csv")
    partidos  = pd.read_csv(CSV_DIR / "partidos.csv")
    jugadores = pd.read_csv(CSV_DIR / "jugadores.csv")
    equipos   = pd.read_csv(CSV_DIR / "equipos.csv")
    torneos   = pd.read_csv(CSV_DIR / "torneos.csv")

    # ── Enriquecer eventos ──────────────────────────────────────────────────
    eventos = eventos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_id", "nombre": "equipo"}),
        on="equipo_id", how="left"
    )
    eventos = eventos.merge(
        jugadores[["id", "nombre"]].rename(columns={"id": "jugador_id", "nombre": "jugador"}),
        on="jugador_id", how="left"
    )
    eventos = eventos.merge(
        partidos[["id", "torneo_id", "jornada"]].rename(columns={"id": "partido_id"}),
        on="partido_id", how="left"
    )
    eventos = eventos.merge(
        torneos[["id", "nombre"]].rename(columns={"id": "torneo_id", "nombre": "torneo"}),
        on="torneo_id", how="left"
    )

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
        torneos[["id", "nombre"]].rename(columns={"id": "torneo_id", "nombre": "torneo"}),
        on="torneo_id", how="left"
    )

    return eventos, partidos, jugadores, equipos, torneos
