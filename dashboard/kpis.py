"""
KPI cards — fila de métricas principales.
"""
import streamlit as st
import pandas as pd


def _kpi_card(col, icon: str, value, label: str) -> None:
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>""", unsafe_allow_html=True)


def render(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    """Renderiza la fila de 6 KPIs en el dashboard."""
    st.markdown('<div class="section-title">📊 Indicadores Clave</div>', unsafe_allow_html=True)

    total_eventos   = len(eventos)
    total_goles     = len(eventos[eventos["tipo_evento"] == "Gol"])
    total_faltas    = len(eventos[eventos["tipo_evento"] == "Falta"])
    total_amarillas = len(eventos[eventos["tipo_evento"] == "Amarilla"])
    total_rojas     = len(eventos[eventos["tipo_evento"] == "Roja"])
    total_partidos  = len(partidos)

    cols = st.columns(6)
    _kpi_card(cols[0], "📋", total_eventos,   "Total Eventos")
    _kpi_card(cols[1], "⚽", total_goles,     "Goles")
    _kpi_card(cols[2], "🦶", total_faltas,    "Faltas")
    _kpi_card(cols[3], "🟨", total_amarillas, "T. Amarillas")
    _kpi_card(cols[4], "🟥", total_rojas,     "T. Rojas")
    _kpi_card(cols[5], "🏟️", total_partidos,  "Partidos")

    st.markdown("<br>", unsafe_allow_html=True)
