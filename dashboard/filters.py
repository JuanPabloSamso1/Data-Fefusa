"""
Sidebar con selectboxes de filtrado y funciones para aplicarlos.
"""
import streamlit as st
import pandas as pd


def render_sidebar(eventos_raw: pd.DataFrame) -> dict:
    """
    Muestra los controles de filtro en la sidebar y retorna un dict con las selecciones.
    """
    with st.sidebar:
        st.markdown("## ⚽ FEFUSA")
        st.markdown("### 🎛️ Filtros")
        st.divider()

        torneos_opts = ["Todos"] + sorted(eventos_raw["torneo"].dropna().unique().tolist())
        sel_torneo = st.selectbox("🏆 Torneo", torneos_opts)

        jornadas_opts = ["Todas"] + sorted(eventos_raw["jornada"].dropna().unique().tolist())
        sel_jornada = st.selectbox("📅 Jornada", jornadas_opts)

        equipos_opts = ["Todos"] + sorted(eventos_raw["equipo"].dropna().unique().tolist())
        sel_equipo = st.selectbox("🛡️ Equipo", equipos_opts)

        tipos_opts = ["Todos"] + sorted(eventos_raw["tipo_evento"].dropna().unique().tolist())
        sel_tipo = st.selectbox("📌 Tipo de evento", tipos_opts)

        # Jugadores dinámicos según equipo seleccionado
        if sel_equipo != "Todos":
            jugadores_pool = (
                eventos_raw[eventos_raw["equipo"] == sel_equipo]["jugador"]
                .dropna().unique().tolist()
            )
        else:
            jugadores_pool = eventos_raw["jugador"].dropna().unique().tolist()
        jugadores_opts = ["Todos"] + sorted(jugadores_pool)
        sel_jugador = st.selectbox("👤 Jugador", jugadores_opts)

        st.divider()
        st.caption("Datos actualizados al 10/03/2026")

    return {
        "torneo":  sel_torneo,
        "jornada": sel_jornada,
        "equipo":  sel_equipo,
        "tipo":    sel_tipo,
        "jugador": sel_jugador,
    }


def apply_event_filters(df: pd.DataFrame, sel: dict) -> pd.DataFrame:
    """Aplica todos los filtros al DataFrame de eventos."""
    if sel["torneo"]  != "Todos":  df = df[df["torneo"]      == sel["torneo"]]
    if sel["jornada"] != "Todas":  df = df[df["jornada"]     == sel["jornada"]]
    if sel["equipo"]  != "Todos":  df = df[df["equipo"]      == sel["equipo"]]
    if sel["tipo"]    != "Todos":  df = df[df["tipo_evento"] == sel["tipo"]]
    if sel["jugador"] != "Todos":  df = df[df["jugador"]     == sel["jugador"]]
    return df


def apply_match_filters(df: pd.DataFrame, sel: dict) -> pd.DataFrame:
    """Aplica filtros de torneo, jornada y equipo al DataFrame de partidos."""
    if sel["torneo"]  != "Todos":  df = df[df["torneo"]  == sel["torneo"]]
    if sel["jornada"] != "Todas":  df = df[df["jornada"] == sel["jornada"]]
    if sel["equipo"]  != "Todos":
        df = df[
            (df["equipo_local"] == sel["equipo"]) |
            (df["equipo_visitante"] == sel["equipo"])
        ]
    return df
