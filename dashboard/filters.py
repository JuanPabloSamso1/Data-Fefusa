"""
Sidebar con selectboxes de filtrado y funciones para aplicarlos.
"""
import streamlit as st
import pandas as pd


def _default_index(options: list, preferred: str) -> int:
    return options.index(preferred) if preferred in options else 0


def _safe_state_value(key: str, options: list, preferred: str) -> None:
    """Garantiza que session_state tenga un valor válido para un selectbox."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = preferred if preferred in options else options[0]


def _reset_sidebar_filters() -> None:
    """Restablece todos los widgets de la barra lateral a sus valores por defecto."""
    st.session_state["f_categoria"] = "Primera FSP" if "Primera FSP" in st.session_state.get("_categorias_opts", []) else "Todas"
    st.session_state["f_temporada"] = "Apertura 2026" if "Apertura 2026" in st.session_state.get("_temporadas_opts", []) else "Todas"
    st.session_state["f_jornada"] = "Todas"
    st.session_state["f_equipo"] = "Todos"
    st.session_state["f_tipo"] = "Todos"
    st.session_state["f_jugador"] = "Todos"


def render_sidebar(eventos_raw: pd.DataFrame, personas_raw: pd.DataFrame) -> dict:
    """
    Muestra los controles de filtro en la sidebar y retorna un dict con las selecciones.
    """
    with st.sidebar:
        st.markdown("## ⚽ FEFUSA")
        st.markdown("### 🎛️ Filtros")

        categorias_opts = ["Todas"] + sorted(eventos_raw["categoria"].dropna().unique().tolist())
        temporadas_opts = ["Todas"] + sorted(eventos_raw["temporada"].dropna().unique().tolist())
        st.session_state["_categorias_opts"] = categorias_opts
        st.session_state["_temporadas_opts"] = temporadas_opts

        if st.button("🧹 Limpiar filtros", use_container_width=True):
            _reset_sidebar_filters()
            st.rerun()

        st.divider()

        _safe_state_value("f_categoria", categorias_opts, "Primera FSP")
        sel_categoria = st.selectbox(
            "🏅 Categoría",
            categorias_opts,
            index=_default_index(categorias_opts, "Primera FSP"),
            key="f_categoria",
        )

        _safe_state_value("f_temporada", temporadas_opts, "Apertura 2026")
        sel_temporada = st.selectbox(
            "🏆 Temporada",
            temporadas_opts,
            index=_default_index(temporadas_opts, "Apertura 2026"),
            key="f_temporada",
        )

        jornadas_opts = ["Todas"] + sorted(eventos_raw["jornada"].dropna().unique().tolist())
        _safe_state_value("f_jornada", jornadas_opts, "Todas")
        sel_jornada = st.selectbox("📅 Jornada", jornadas_opts, key="f_jornada")

        equipos_opts = ["Todos"] + sorted(eventos_raw["equipo"].dropna().unique().tolist())
        _safe_state_value("f_equipo", equipos_opts, "Todos")
        sel_equipo = st.selectbox("🛡️ Equipo", equipos_opts, key="f_equipo")

        tipos_opts = ["Todos"] + sorted(eventos_raw["tipo_evento"].dropna().unique().tolist())
        _safe_state_value("f_tipo", tipos_opts, "Todos")
        sel_tipo = st.selectbox("📌 Tipo de evento", tipos_opts, key="f_tipo")

        # Jugadores dinámicos según equipo seleccionado (incluye jugadores sin eventos)
        jugadores_base = personas_raw.copy()
        if "tipo_persona" in jugadores_base.columns:
            jugadores_base = jugadores_base[jugadores_base["tipo_persona"] == "JUGADOR"]

        if sel_equipo != "Todos":
            equipo_ids = eventos_raw.loc[eventos_raw["equipo"] == sel_equipo, "equipo_id"].dropna().unique().tolist()
            if equipo_ids:
                jugadores_base = jugadores_base[jugadores_base["equipo_id"].isin(equipo_ids)]
            else:
                jugadores_base = jugadores_base.iloc[0:0]

        jugadores_pool = jugadores_base["nombre"].dropna().unique().tolist()

        # Fallback por compatibilidad si no hay personas disponibles
        if not jugadores_pool:
            if sel_equipo != "Todos":
                jugadores_pool = (
                    eventos_raw[eventos_raw["equipo"] == sel_equipo]["jugador"]
                    .dropna().unique().tolist()
                )
            else:
                jugadores_pool = eventos_raw["jugador"].dropna().unique().tolist()

        jugadores_opts = ["Todos"] + sorted(jugadores_pool)
        _safe_state_value("f_jugador", jugadores_opts, "Todos")
        sel_jugador = st.selectbox("👤 Jugador", jugadores_opts, key="f_jugador")

        breadcrumb = " > ".join([
            sel_categoria if sel_categoria != "Todas" else "Todas las Categorías",
            sel_temporada if sel_temporada != "Todas" else "Todas las Temporadas",
            sel_equipo if sel_equipo != "Todos" else "Todos los Equipos",
            sel_jugador if sel_jugador != "Todos" else "Todos los Jugadores",
        ])
        st.info(f"📍 Contexto activo: {breadcrumb}")

        st.divider()
        st.caption("Datos actualizados al 10/03/2026")

    return {
        "categoria": sel_categoria,
        "temporada": sel_temporada,
        "jornada": sel_jornada,
        "equipo":  sel_equipo,
        "tipo":    sel_tipo,
        "jugador": sel_jugador,
    }


def apply_event_filters(df: pd.DataFrame, sel: dict) -> pd.DataFrame:
    """Aplica todos los filtros al DataFrame de eventos."""
    if sel["categoria"] != "Todas":  df = df[df["categoria"]     == sel["categoria"]]
    if sel["temporada"] != "Todas":  df = df[df["temporada"]     == sel["temporada"]]
    if sel["jornada"]   != "Todas":  df = df[df["jornada"]       == sel["jornada"]]
    if sel["equipo"]    != "Todos":  df = df[df["equipo"]        == sel["equipo"]]
    if sel["tipo"]      != "Todos":  df = df[df["tipo_evento"]   == sel["tipo"]]
    if sel["jugador"]   != "Todos":  df = df[df["jugador"]       == sel["jugador"]]
    return df


def apply_match_filters(df: pd.DataFrame, sel: dict) -> pd.DataFrame:
    """Aplica filtros de torneo, jornada y equipo al DataFrame de partidos."""
    if sel["categoria"] != "Todas":  df = df[df["categoria"] == sel["categoria"]]
    if sel["temporada"] != "Todas":  df = df[df["temporada"] == sel["temporada"]]
    if sel["jornada"]   != "Todas":  df = df[df["jornada"]   == sel["jornada"]]
    if sel["equipo"]    != "Todos":
        df = df[
            (df["equipo_local"] == sel["equipo"]) |
            (df["equipo_visitante"] == sel["equipo"])
        ]
    return df
