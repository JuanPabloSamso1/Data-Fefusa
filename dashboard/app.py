"""
Dashboard de Analytics — FEFUSA
================================
Punto de entrada: streamlit run dashboard/app.py
"""
import sys
import os
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

# ─── Carga de datos ───────────────────────────────────────────────────────────
eventos_raw, partidos_raw, jugadores, equipos, torneos = load_data()

# ─── Sidebar / Filtros ────────────────────────────────────────────────────────
sel = filters.render_sidebar(eventos_raw)

# ─── Aplicar filtros ──────────────────────────────────────────────────────────
eventos  = filters.apply_event_filters(eventos_raw, sel)
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

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_general, tab_goles, tab_disciplina, tab_partido = st.tabs([
    "🏠 Visión General", 
    "⚽ Análisis de Goles", 
    "🟨 Disciplina y Castigos", 
    "📊 Análisis del Partido"
])

# ─── Tab: Visión General ─────────────────────────────────────────────────────
with tab_general:
    # ─── Tabla de Posiciones, Ranking Elo y Resultados ─────────────────────────
    col_pos, col_elo, col_res = st.columns([3, 2, 3], gap="medium")
    with col_pos:
        tables.league_standings(partidos)
    with col_elo:
        tables.elo_ranking(partidos_raw, partidos)
    with col_res:
        tables.match_results(partidos)

    # ─── Rendimiento y distribución global de eventos ──────────────────────────
    col_perf, col_events = st.columns([3, 2], gap="medium")
    with col_perf:
        charts.team_performance(partidos)
    with col_events:
        charts.events_by_type(eventos)

# ─── Tab: Análisis de Goles ──────────────────────────────────────────────────
with tab_goles:
    # ─── Goles por equipo ─────────────────────────────────────────────────
    charts.goals_by_team(eventos)

    # ─── Goles por jornada · Ranking goleadores ──────────────────────────
    col_c, col_d = st.columns([2, 3], gap="medium")
    with col_c:
        charts.goals_by_round(eventos)
    with col_d:
        charts.top_scorers(eventos)
        
    charts.top_scorers_timeline(eventos)

    # ─── Goles Recibidos y por Periodo ────────────────────────────────────────
    col_e, col_f = st.columns([2, 1], gap="medium")
    with col_e:
        charts.goals_conceded(eventos, partidos)
    with col_f:
        charts.goals_by_period(eventos)

# ─── Tab: Disciplina y Castigos ──────────────────────────────────────────────
with tab_disciplina:
    # ─── Tiros Castigo ───────────────────────────────────────────────────────────
    col_tc1, col_tc2 = st.columns([1, 1], gap="medium")
    with col_tc1:
        charts.tiros_castigo_bar(eventos, partidos)
    with col_tc2:
        charts.tiros_castigo_scatter(eventos)

    # ─── Tabla disciplinaria ─────────────────────────────────────────────────────
    col_g, col_h = st.columns([2, 2], gap="medium")
    with col_g:
        tables.disciplinary(eventos)
    with col_h:
        charts.disciplinary_timeline(eventos)
        
    # ─── Top Indisciplinados ─────────────────────────────────────────────────────
    charts.top_undisciplined(eventos)

    # ─── Gráficos de dispersión (Scatter Plots) ──────────────────────────────────
    col_s1, col_s2 = st.columns([1, 1], gap="medium")
    with col_s1:
        charts.fouls_scatter(eventos, partidos)
    with col_s2:
        charts.efficiency_vs_discipline(eventos, partidos)

# ─── Tab: Análisis del Partido ───────────────────────────────────────────────
with tab_partido:
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
        
    # Filtrar equipos disponibles para esa categoria y temporada
    p_locales = partidos_raw[(partidos_raw["categoria"] == local_cat) & (partidos_raw["temporada"] == local_temp)]
    equipos_disponibles = sorted(pd.concat([p_locales["equipo_local"], p_locales["equipo_visitante"]]).unique().tolist())
    
    with col_f3:
        local_eq1 = st.selectbox("🛡️ Equipo 1", equipos_disponibles if equipos_disponibles else ["Seleccione..."])
        
    # Buscar rivales que hayan jugado contra Equipo 1
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
        
    # Encontrar el partido
    partido_seleccionado = p_locales[
        ((p_locales["equipo_local"] == local_eq1) & (p_locales["equipo_visitante"] == local_eq2)) |
        ((p_locales["equipo_local"] == local_eq2) & (p_locales["equipo_visitante"] == local_eq1))
    ]
    
    if not partido_seleccionado.empty:
        # Si jugaron más de 1 vez, tomamos el primero (o podríamos dejar que el usuario elija jornada)
        p_id = partido_seleccionado.iloc[0]["id"]
        
        # Filtrar eventos y partidos puros para esta seccion
        eventos_timeline = eventos_raw[eventos_raw["partido_id"] == p_id].copy()
        partidos_timeline = partidos_raw[partidos_raw["id"] == p_id].copy()
        
        # ─── Línea de tiempo ────────────────────────
        charts.match_timeline(eventos_timeline, tipos_permitidos=local_eventos)
    else:
        st.warning(f"No se encontró un partido entre {local_eq1} y {local_eq2} en la seleccion.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style="text-align:center; color:#8b949e; font-size:0.8rem; padding:8px 0;">
    FEFUSA · Dashboard Analytics &nbsp;|&nbsp; {display_cat} - {display_temp} &nbsp;|&nbsp; Datos al 10/03/2026
</div>
""", unsafe_allow_html=True)
