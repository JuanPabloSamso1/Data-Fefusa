"""Dashboard de Analytics — FEFUSA.

Arquitectura modular:
- Visión general
- Equipos
- Jugadores
- Predicciones
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path de Python para que encuentre el módulo 'dashboard'
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from dashboard.data_loader import load_data
from dashboard import filters, kpis, charts, tables, predictions

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

    goles = eventos[eventos["tipo_evento"] == "Gol"] if not eventos.empty else pd.DataFrame()
    eventos_top = eventos["tipo_evento"].value_counts().index[0] if not eventos.empty else None
    if not goles.empty:
        top = goles.groupby("equipo").size().sort_values(ascending=False)
        extra = f" El evento más frecuente es {eventos_top.lower()}." if eventos_top else ""
        return f"{top.index[0]} lidera en ataque con {int(top.iloc[0])} goles.{extra}"

    return "Hay partidos cargados, pero no se registran goles en esta vista filtrada."


def insight_jugadores(eventos: pd.DataFrame) -> str:
    if eventos.empty:
        return "No hay eventos para analizar jugadores."
    goles = eventos[eventos["tipo_evento"] == "Gol"]
    if goles.empty:
        return "No se registran goles para calcular incidencia ofensiva individual."
    top = goles.groupby("jugador").size().sort_values(ascending=False)
    return f"{top.index[0]} es el jugador con mayor incidencia ofensiva ({int(top.iloc[0])} goles)."


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
    return f"{s.index[0]} muestra la mejor forma reciente con {int(s.iloc[0])} victorias."


def insight_disciplina(eventos: pd.DataFrame) -> str:
    if eventos.empty:
        return "No hay eventos para analizar disciplina."
    eventos_disc = eventos[eventos["tipo_evento"].isin(["Falta", "Amarilla", "Azul I", "Azul D", "Roja"])]
    if eventos_disc.empty:
        return "No se registran eventos disciplinarios en este filtro."
    total = len(eventos_disc)
    faltas = int((eventos_disc["tipo_evento"] == "Falta").sum())
    pct = (faltas / total) * 100 if total else 0
    return f"Las faltas representan el {pct:.1f}% de las incidencias disciplinarias del contexto actual."


def players_summary_table(eventos: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    if eventos.empty:
        return pd.DataFrame()

    base = eventos.copy()
    base["jugador"] = base["jugador"].fillna("Sin jugador")
    base["equipo"] = base["equipo"].fillna("Sin equipo")

    goles = base[base["tipo_evento"] == "Gol"].groupby(["jugador", "equipo"]).size().reset_index(name="Goles")
    eventos_tot = base.groupby(["jugador", "equipo"]).size().reset_index(name="Eventos")
    partidos_p = base.groupby(["jugador", "equipo"])["partido_id"].nunique().reset_index(name="Partidos")

    out = eventos_tot.merge(goles, on=["jugador", "equipo"], how="left").merge(partidos_p, on=["jugador", "equipo"], how="left")
    out["Goles"] = out["Goles"].fillna(0).astype(int)
    out["Partidos"] = out["Partidos"].fillna(0).astype(int)
    out["Incidencia (goles/partido)"] = out.apply(
        lambda r: round(r["Goles"] / r["Partidos"], 2) if r["Partidos"] > 0 else 0,
        axis=1,
    )
    out = out.rename(columns={"jugador": "Jugador", "equipo": "Equipo"})
    return out.sort_values(["Goles", "Incidencia (goles/partido)", "Eventos"], ascending=False).head(top_n)


# ─── Carga de datos ───────────────────────────────────────────────────────────
eventos_raw, partidos_raw, personas, equipos, torneos = load_data()

# ─── Sidebar / Filtros ────────────────────────────────────────────────────────
sel = filters.render_sidebar(eventos_raw, personas)

# ─── Aplicar filtros ──────────────────────────────────────────────────────────
eventos = filters.apply_event_filters(eventos_raw, sel)
partidos = filters.apply_match_filters(partidos_raw, sel)

# ─── Header ──────────────────────────────────────────────────────────────────
display_cat = sel["categoria"] if sel["categoria"] != "Todas" else "Todas las Categorías"
display_temp = sel["temporada"] if sel["temporada"] != "Todas" else "Todas las Temporadas"

st.markdown(f"""
<div class="main-header">
    <h1>⚽ Dashboard de Rendimiento Deportivo</h1>
    <p>FEFUSA Mendoza &nbsp;·&nbsp; {display_cat} — {display_temp}</p>
</div>
""", unsafe_allow_html=True)

# ─── Navegación principal (módulos) ──────────────────────────────────────────
mod_general, mod_equipos, mod_jugadores, mod_pred = st.tabs(
    ["📌 Visión general", "🛡️ Equipos", "👤 Jugadores", "🔮 Predicciones"]
)

with mod_general:
    st.markdown("### 📌 Visión general")
    st.caption("Lectura rápida: volumen, rendimiento competitivo y distribución de eventos.")
    kpis.render(eventos, partidos, jugador_seleccionado=sel["jugador"])
    render_insight(insight_resumen(eventos, partidos))

    col_main, col_secondary = st.columns([3, 2], gap="medium")
    with col_main:
        charts.team_performance(partidos)
    with col_secondary:
        charts.events_by_type(eventos)

    st.markdown("### 🧾 Tabla clave")
    tables.league_standings(partidos, compact=True, top_n=10)

with mod_equipos:
    st.markdown("### 🛡️ Equipos")
    st.caption("Comparación de ataque y equilibrio rendimiento-disciplina por equipo.")
    render_insight(insight_equipos(partidos))

    col_eq_1, col_eq_2 = st.columns([2, 3], gap="medium")
    with col_eq_1:
        charts.goals_by_team(eventos)
    with col_eq_2:
        charts.efficiency_vs_discipline(eventos, partidos)

    st.markdown("### 🧾 Tabla clave")
    tables.elo_ranking(partidos_raw, partidos, compact=True, top_n=10)

with mod_jugadores:
    st.markdown("### 👤 Jugadores")
    st.caption("Foco en incidencia ofensiva individual y evolución por jornada.")
    render_insight(insight_jugadores(eventos))

    col_j_1, col_j_2 = st.columns([2, 3], gap="medium")
    with col_j_1:
        charts.top_scorers(eventos)
    with col_j_2:
        charts.top_scorers_timeline(eventos)

    st.markdown("### 🧾 Tabla clave")
    tabla_jugadores = players_summary_table(eventos)
    if tabla_jugadores.empty:
        st.info("Sin datos de jugadores para los filtros actuales.")
    else:
        st.dataframe(
            tabla_jugadores,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jugador": st.column_config.TextColumn("Jugador", width="medium"),
                "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
                "Eventos": st.column_config.NumberColumn("Eventos", format="%d"),
                "Goles": st.column_config.NumberColumn("Goles", format="%d"),
                "Partidos": st.column_config.NumberColumn("Partidos", format="%d"),
                "Incidencia (goles/partido)": st.column_config.NumberColumn("Incidencia", format="%.2f"),
            },
        )

with mod_pred:
    st.markdown("### 🔮 Predicciones")
    st.caption("Predicciones simples y explicables basadas en rendimiento ofensivo/defensivo y simulación de tabla.")

    base_matches = predictions.prepare_matches(partidos)
    equipos_pred = sorted(pd.concat([base_matches["equipo_local"], base_matches["equipo_visitante"]]).dropna().unique().tolist()) if not base_matches.empty else []

    if len(equipos_pred) < 2:
        st.info("No hay suficientes equipos con datos para generar predicciones en este contexto.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            team_a = st.selectbox("🛡️ Equipo A", equipos_pred, index=0)
        with col_b:
            idx_b = 1 if len(equipos_pred) > 1 else 0
            team_b = st.selectbox("🛡️ Equipo B", equipos_pred, index=idx_b)

        if team_a == team_b:
            st.warning("Seleccioná dos equipos distintos para calcular la predicción del próximo partido.")
        else:
            pred = predictions.predict_match(base_matches, team_a, team_b)
            probs = pred["probs"]
            render_insight(
                f"Para el próximo cruce estimado {team_a} vs {team_b}, la opción más probable es "
                f"{('victoria de ' + team_a) if probs['win_a'] >= max(probs['draw'], probs['win_b']) else ('empate' if probs['draw'] >= probs['win_b'] else ('victoria de ' + team_b))}."
            )

            st.markdown("### 1) Probabilidad de resultado del próximo partido")
            pcol1, pcol2, pcol3 = st.columns(3)
            pcol1.metric(f"Gana {team_a}", f"{probs['win_a']*100:.1f}%")
            pcol2.metric("Empate", f"{probs['draw']*100:.1f}%")
            pcol3.metric(f"Gana {team_b}", f"{probs['win_b']*100:.1f}%")
            st.caption("Modelo Poisson independiente sobre goles esperados. No depende fuertemente de localía.")

            st.markdown("### 2) Goles esperados del partido")
            xcol1, xcol2, xcol3 = st.columns(3)
            xcol1.metric(f"xG {team_a}", f"{pred['xg_a']:.2f}")
            xcol2.metric(f"xG {team_b}", f"{pred['xg_b']:.2f}")
            xcol3.metric("xG Total", f"{pred['xg_total']:.2f}")
            st.caption(f"Calidad de muestra: {pred['quality']} · {pred['details']}")

            st.markdown("### 3) Proyección simple de tabla (+1 fecha)")
            proj = predictions.project_table(base_matches, simulations=800)
            if proj.empty:
                st.info("No hay datos suficientes para proyectar la tabla.")
            else:
                chance_up = proj.sort_values("Prob. subir", ascending=False).iloc[0]
                chance_down = proj.sort_values("Prob. bajar", ascending=False).iloc[0]
                render_insight(
                    f"Mayor chance de subir: {chance_up['Equipo']} ({chance_up['Prob. subir']*100:.1f}%). "
                    f"Mayor riesgo de bajar: {chance_down['Equipo']} ({chance_down['Prob. bajar']*100:.1f}%)."
                )

                st.dataframe(
                    proj,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
                        "Pos actual": st.column_config.NumberColumn("Pos actual", format="%d"),
                        "PTS actuales": st.column_config.NumberColumn("PTS actuales", format="%d"),
                        "PTS esperados (+1 fecha)": st.column_config.NumberColumn("PTS esperados", format="%.2f"),
                        "Pos esperada": st.column_config.NumberColumn("Pos esperada", format="%.2f"),
                        "Prob. subir": st.column_config.ProgressColumn("Prob. subir", min_value=0.0, max_value=1.0, format="%.2f"),
                        "Prob. bajar": st.column_config.ProgressColumn("Prob. bajar", min_value=0.0, max_value=1.0, format="%.2f"),
                        "Cambio probable": st.column_config.TextColumn("Cambio probable", width="small"),
                    },
                )

            with st.expander("ℹ️ Cómo funciona este modelo"):
                st.markdown(
                    """
- **Features usadas**: goles a favor/contra por partido, partidos jugados y media de goles de la liga filtrada.
- **Probabilidades 1X2**: se calculan con una distribución de Poisson para ambos equipos y se agregan escenarios de victoria/empate/derrota.
- **Goles esperados (xG simples)**: media liga × fortaleza ofensiva del equipo × fragilidad defensiva rival.
- **Proyección de tabla**: simulación Monte Carlo básica de una fecha sintética (800 simulaciones) para estimar puntos y cambios probables de posición.
- **Supuesto clave**: no se usa localía como factor fuerte por baja confiabilidad del dato.
                    """
                )

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style="text-align:center; color:#8b949e; font-size:0.8rem; padding:8px 0;">
    FEFUSA · Dashboard Analytics &nbsp;|&nbsp; {display_cat} - {display_temp} &nbsp;|&nbsp; Datos al 10/03/2026
</div>
""", unsafe_allow_html=True)
