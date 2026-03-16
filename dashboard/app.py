"""
Dashboard de Analytics — FEFUSA
================================
Punto de entrada: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path de Python para que encuentre el módulo 'dashboard'
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from dashboard.data_loader import load_data
from dashboard import filters, kpis, charts, tables

# ─── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="FEFUSA · Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos globales ─────────────────────────────────────────────────────────
from dashboard.styles import inject_css
inject_css()


# ─── Helpers de insights ───────────────────────────────────────────────────────
def render_insight(text: str) -> None:
    st.markdown(f'<div class="insight-banner">💡 {text}</div>', unsafe_allow_html=True)


def insight_resumen(eventos: pd.DataFrame, partidos: pd.DataFrame) -> str:
    if partidos.empty:
        return "No hay partidos para generar insight en esta selección."
    totales = (
        eventos[eventos["tipo_evento"] == "Gol"].groupby("equipo").size().sort_values(ascending=False)
        if not eventos.empty else pd.Series(dtype=int)
    )
    if not totales.empty:
        return f"{totales.index[0]} lidera en goles convertidos ({int(totales.iloc[0])})."
    return "Hay partidos cargados, pero no se registran goles en esta vista filtrada."


def insight_jugadores(eventos: pd.DataFrame) -> str:
    if eventos.empty:
        return "No hay eventos para analizar jugadores."
    goles = eventos[eventos["tipo_evento"] == "Gol"]
    if goles.empty:
        return "No se registran goles para calcular incidencia ofensiva individual."
    top = goles.groupby("jugador").size().sort_values(ascending=False)
    return f"{top.index[0]} concentra la mayor incidencia ofensiva con {int(top.iloc[0])} goles."


def insight_equipos(partidos: pd.DataFrame) -> str:
    if partidos.empty:
        return "No hay partidos suficientes para construir ranking de equipos."
    victorias = []
    for _, p in partidos.iterrows():
        if p["goles_local"] > p["goles_visitante"]:
            victorias.append(p["equipo_local"])
        elif p["goles_visitante"] > p["goles_local"]:
            victorias.append(p["equipo_visitante"])
    if not victorias:
        return "Predominan los empates en la muestra actual."
    s = pd.Series(victorias).value_counts()
    return f"{s.index[0]} es el equipo con más victorias recientes ({int(s.iloc[0])})."


def insight_disciplina(eventos: pd.DataFrame) -> str:
    if eventos.empty:
        return "No hay eventos para analizar disciplina."
    eventos_disc = eventos[eventos["tipo_evento"].isin(["Falta", "Amarilla", "Azul I", "Azul D", "Roja"])]
    if eventos_disc.empty:
        return "No se registran eventos disciplinarios en este filtro."
    total = len(eventos_disc)
    faltas = int((eventos_disc["tipo_evento"] == "Falta").sum())
    pct = (faltas / total) * 100 if total else 0
    return f"La falta representa el {pct:.1f}% de los eventos disciplinarios registrados."


# ─── Carga de datos ───────────────────────────────────────────────────────────
eventos_raw, partidos_raw, personas, equipos, torneos = load_data()

# ─── Sidebar / Filtros ────────────────────────────────────────────────────────
sel = filters.render_sidebar(eventos_raw, personas)

# ─── Aplicar filtros ──────────────────────────────────────────────────────────
eventos = filters.apply_event_filters(eventos_raw, sel)
partidos = filters.apply_match_filters(partidos_raw, sel)

# ─── Header ──────────────────────────────────────────────────────────────────
# Determinar título dinámico según filtros
display_cat = sel["categoria"] if sel["categoria"] != "Todas" else "Todas las Categorías"
display_temp = sel["temporada"] if sel["temporada"] != "Todas" else "Todas las Temporadas"

st.markdown(f"""
<div class="main-header">
    <h1>⚽ Dashboard de Rendimiento Deportivo</h1>
    <p>FEFUSA Mendoza &nbsp;·&nbsp; {display_cat} — {display_temp}</p>
</div>
""", unsafe_allow_html=True)

# ─── KPIs ────────────────────────────────────────────────────────────────────
kpis.render(eventos, partidos, jugador_seleccionado=sel["jugador"])

# ─── Navegación principal (páginas) ───────────────────────────────────────────
pagina = st.radio(
    "Navegación",
    ["📌 Resumen", "🛡️ Equipos", "👤 Jugadores", "📊 Partidos / Predicción"],
    horizontal=True,
    label_visibility="collapsed",
)

if pagina == "📌 Resumen":
    render_insight(insight_resumen(eventos, partidos))

    col_pos, col_elo, col_res = st.columns([3, 2, 3], gap="medium")
    with col_pos:
        tables.league_standings(partidos, compact=True, top_n=8)
    with col_elo:
        tables.elo_ranking(partidos_raw, partidos, compact=True, top_n=8)
    with col_res:
        tables.match_results(partidos, compact=True, top_n=8)

    col_perf, col_events = st.columns([3, 2], gap="medium")
    with col_perf:
        charts.team_performance(partidos)
    with col_events:
        charts.events_by_type(eventos)

elif pagina == "🛡️ Equipos":
    render_insight(insight_equipos(partidos))
    charts.goals_by_team(eventos)

    col_a, col_b = st.columns([2, 1], gap="medium")
    with col_a:
        charts.goals_conceded(eventos, partidos)
    with col_b:
        charts.goals_by_period(eventos)

    charts.tiros_castigo_bar(eventos, partidos)

elif pagina == "👤 Jugadores":
    render_insight(insight_jugadores(eventos))

    col_c, col_d = st.columns([2, 3], gap="medium")
    with col_c:
        charts.goals_by_round(eventos)
    with col_d:
        charts.top_scorers(eventos)

    charts.top_scorers_timeline(eventos)

    col_s1, col_s2 = st.columns([1, 1], gap="medium")
    with col_s1:
        charts.fouls_scatter(eventos, partidos)
    with col_s2:
        charts.efficiency_vs_discipline(eventos, partidos)

elif pagina == "📊 Partidos / Predicción":
    subtab_disc, subtab_match = st.tabs(["🟨 Disciplina", "⏳ Línea de Tiempo de Partido"])

    with subtab_disc:
        render_insight(insight_disciplina(eventos))
        col_tc1, col_tc2 = st.columns([1, 1], gap="medium")
        with col_tc1:
            charts.tiros_castigo_scatter(eventos)
        with col_tc2:
            charts.disciplinary_timeline(eventos)

        col_g, col_h = st.columns([2, 2], gap="medium")
        with col_g:
            tables.disciplinary(eventos, compact=True, top_n=8)
        with col_h:
            charts.top_undisciplined(eventos)

    with subtab_match:
        st.divider()
        st.markdown("### 🎛️ Filtros Específicos del Partido")
        st.caption("Seleccioná un partido específico para ver su evolución. Estos filtros son independientes de la barra lateral.")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cat_opts = sorted(partidos_raw["categoria"].dropna().unique().tolist())
            cat_def = cat_opts.index("Primera FSP") if "Primera FSP" in cat_opts else 0
            local_cat = st.selectbox("🏅 Categoría (Línea de Tiempo)", cat_opts, index=cat_def)
        with col_f2:
            temp_opts = sorted(partidos_raw["temporada"].dropna().unique().tolist())
            temp_def = temp_opts.index("Apertura 2026") if "Apertura 2026" in temp_opts else 0
            local_temp = st.selectbox("🏆 Temporada (Línea de Tiempo)", temp_opts, index=temp_def)

        p_locales = partidos_raw[(partidos_raw["categoria"] == local_cat) & (partidos_raw["temporada"] == local_temp)]
        equipos_disponibles = sorted(pd.concat([p_locales["equipo_local"], p_locales["equipo_visitante"]]).unique().tolist())

        with col_f3:
            local_eq1 = st.selectbox("🛡️ Equipo 1", equipos_disponibles if equipos_disponibles else ["Seleccione..."])

        rivales = []
        if local_eq1 in equipos_disponibles:
            m_jugados = p_locales[(p_locales["equipo_local"] == local_eq1) | (p_locales["equipo_visitante"] == local_eq1)]
            rivales_local = m_jugados[m_jugados["equipo_local"] != local_eq1]["equipo_local"].tolist()
            rivales_visitante = m_jugados[m_jugados["equipo_visitante"] != local_eq1]["equipo_visitante"].tolist()
            rivales = sorted(list(set(rivales_local + rivales_visitante)))

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            local_eq2 = st.selectbox("🛡️ Equipo 2 (Rival)", rivales if rivales else ["No hay rivales"])
        with col_f5:
            all_events = sorted(eventos_raw["tipo_evento"].dropna().unique().tolist())
            local_eventos = st.multiselect("📌 Mostrar Eventos", all_events, default=all_events)

        partido_seleccionado = p_locales[
            ((p_locales["equipo_local"] == local_eq1) & (p_locales["equipo_visitante"] == local_eq2)) |
            ((p_locales["equipo_local"] == local_eq2) & (p_locales["equipo_visitante"] == local_eq1))
        ]

        if not partido_seleccionado.empty:
            p_id = partido_seleccionado.iloc[0]["id"]
            eventos_timeline = eventos_raw[eventos_raw["partido_id"] == p_id].copy()
            charts.match_timeline(
                eventos_timeline,
                tipos_permitidos=local_eventos,
                equipo_izq=local_eq1,
                equipo_der=local_eq2,
            )
        else:
            st.warning(f"No se encontró un partido entre {local_eq1} y {local_eq2} en la seleccion.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style="text-align:center; color:#8b949e; font-size:0.8rem; padding:8px 0;">
    FEFUSA · Dashboard Analytics &nbsp;|&nbsp; {display_cat} - {display_temp} &nbsp;|&nbsp; Datos al 10/03/2026
</div>
""", unsafe_allow_html=True)
