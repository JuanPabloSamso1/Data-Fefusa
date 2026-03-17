"""Dashboard FEFUSA redisenado sobre Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from dashboard import analytics, filters, views  # noqa: E402
from dashboard.data_loader import get_last_data_update, load_data  # noqa: E402
from dashboard.styles import inject_css  # noqa: E402

st.set_page_config(
    page_title="FEFUSA · Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

eventos_raw, partidos_raw, personas, equipos, torneos = load_data()
last_update_label = analytics.format_last_updated(get_last_data_update())

sel = filters.render_sidebar(eventos_raw, personas, last_data_label=last_update_label)
eventos = filters.apply_event_filters(eventos_raw, sel)
partidos = filters.apply_match_filters(partidos_raw, sel)

display_category = sel["categoria"] if sel["categoria"] != "Todas" else "Todas las categorias"
display_season = sel["temporada"] if sel["temporada"] != "Todas" else "Todas las temporadas"
context_label = f"{display_category} · {display_season} · actualizado {last_update_label}"

tab_liga, tab_equipo, tab_jugador, tab_partido, tab_disciplina, tab_comparativa, tab_predictions = st.tabs(
    [
        "Liga / Temporada",
        "Perfil de equipo",
        "Perfil de jugador",
        "Analisis de partido",
        "Disciplina",
        "Comparativa",
        "Predicciones",
    ]
)

with tab_liga:
    views.render_dashboard_tab("liga", eventos, partidos, sel, last_update_label)

with tab_equipo:
    views.render_dashboard_tab("equipo", eventos, partidos, sel, last_update_label)

with tab_jugador:
    views.render_dashboard_tab("jugador", eventos, partidos, sel, last_update_label)

with tab_partido:
    views.render_dashboard_tab("partido", eventos, partidos, sel, last_update_label)

with tab_disciplina:
    views.render_dashboard_tab("disciplina", eventos, partidos, sel, last_update_label)

with tab_comparativa:
    views.render_dashboard_tab("comparativa", eventos, partidos, sel, last_update_label)

with tab_predictions:
    views.render_predictions_tab(partidos, sel, last_update_label)

st.divider()
st.markdown(
    f'<div class="footer-line">FEFUSA · Dashboard Analytics · {display_category} · {display_season} · Datos al {last_update_label}</div>',
    unsafe_allow_html=True,
)
