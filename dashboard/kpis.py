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


def render(eventos: pd.DataFrame, partidos: pd.DataFrame, jugador_seleccionado: str = "Todos") -> None:
    """Renderiza la fila de 5 KPIs con agregación consistente al filtro activo."""
    st.markdown('<div class="section-title">📊 Indicadores clave</div>', unsafe_allow_html=True)

    total_eventos = len(eventos)
    total_goles = int((eventos["tipo_evento"] == "Gol").sum()) if "tipo_evento" in eventos.columns else 0
    total_faltas = int((eventos["tipo_evento"] == "Falta").sum()) if "tipo_evento" in eventos.columns else 0
    total_tarjetas = int(
        eventos["tipo_evento"].isin(["Amarilla", "Roja", "Azul I", "Azul D"]).sum()
    ) if "tipo_evento" in eventos.columns else 0

    partidos_por_eventos = eventos["partido_id"].dropna().nunique() if "partido_id" in eventos.columns else 0
    partidos_por_fixture = partidos["id"].dropna().nunique() if "id" in partidos.columns else len(partidos)

    if jugador_seleccionado != "Todos":
        total_partidos = int(partidos_por_eventos)
        etiqueta_partidos = "Partidos con participación"
    else:
        total_partidos = int(partidos_por_fixture)
        etiqueta_partidos = "Partidos analizados"

    goles_por_partido = round(total_goles / total_partidos, 2) if total_partidos > 0 else 0

    cols = st.columns(5)
    _kpi_card(cols[0], "🏟️", total_partidos, etiqueta_partidos)
    _kpi_card(cols[1], "⚽", total_goles, "Goles")
    _kpi_card(cols[2], "📈", goles_por_partido, "Goles por partido")
    _kpi_card(cols[3], "📋", total_eventos, "Eventos registrados")
    _kpi_card(cols[4], "🟨", total_tarjetas + total_faltas, "Incidencias disciplinarias")

    st.markdown("<br>", unsafe_allow_html=True)
