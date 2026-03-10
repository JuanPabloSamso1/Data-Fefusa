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
st.markdown("""
<div class="main-header">
    <h1>⚽ Dashboard de Rendimiento Deportivo</h1>
    <p>Federación de Fútbol de Mendoza &nbsp;·&nbsp; Primera FSP — Apertura 2026</p>
</div>
""", unsafe_allow_html=True)

# ─── KPIs ────────────────────────────────────────────────────────────────────
kpis.render(eventos, partidos)

# ─── Fila 1: Goles por equipo · Eventos por tipo ─────────────────────────────
col_a, col_b = st.columns([3, 2], gap="medium")
with col_a:
    charts.goals_by_team(eventos)
with col_b:
    charts.events_by_type(eventos)

# ─── Fila 2: Goles por jornada · Ranking goleadores ──────────────────────────
col_c, col_d = st.columns([2, 3], gap="medium")
with col_c:
    charts.goals_by_round(eventos)
with col_d:
    charts.top_scorers(eventos)
    
charts.top_scorers_timeline(eventos)

# ─── Fila 3: Goles Recibidos y Rústicos ────────────────────────────────────────
col_ef1, col_ef2 = st.columns([1, 1], gap="medium")
with col_ef1:
    charts.goals_conceded(eventos, partidos)
with col_ef2:
    charts.top_undisciplined(eventos)

# ─── Tabla disciplinaria ─────────────────────────────────────────────────────
col_g, col_h = st.columns([2, 2], gap="medium")
with col_g:
    tables.disciplinary(eventos)
with col_h:
    charts.disciplinary_timeline(eventos)

# ─── Tabla de Posiciones y Resultados ────────────────────────────────────────
col_pos, col_res = st.columns([3, 2], gap="medium")
with col_pos:
    tables.league_standings(partidos)
with col_res:
    tables.match_results(partidos)

# ─── Gráficos de dispersión (Scatter Plots) ──────────────────────────────────
col_s1, col_s2 = st.columns([1, 1], gap="medium")
with col_s1:
    charts.fouls_scatter(eventos, partidos)
with col_s2:
    charts.efficiency_vs_discipline(eventos, partidos)

# ─── Rendimiento ─────────────────────────────────────────────────────────────
charts.team_performance(partidos)

# ─── Distribución de eventos por minuto y Periodos ───────────────────────────
col_e, col_f = st.columns([2, 1], gap="medium")
with col_e:
    charts.events_by_minute(eventos)
with col_f:
    charts.goals_by_period(eventos)

# ─── Línea de tiempo (si hay 1 solo partido filtrado) ────────────────────────
charts.match_timeline(eventos)

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#8b949e; font-size:0.8rem; padding:8px 0;">
    FEFUSA · Dashboard Analytics &nbsp;|&nbsp; Apertura 2026 &nbsp;|&nbsp; Datos al 10/03/2026
</div>
""", unsafe_allow_html=True)
