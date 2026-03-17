"""Render de vistas del dashboard redisenado."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard import analytics, charts, predictions

VIEW_CONFIG = {
    "liga": {
        "title": "Liga / Temporada",
        "subtitle": "Vision global del torneo",
        "caption": "KPIs globales, posiciones, eficiencia relativa y ritmo de gol del contexto filtrado.",
    },
    "equipo": {
        "title": "Perfil de equipo",
        "subtitle": "Rendimiento por club",
        "caption": "Lectura de forma, balance ofensivo-defensivo y perfil disciplinario del equipo seleccionado.",
    },
    "jugador": {
        "title": "Perfil de jugador",
        "subtitle": "Estadisticas individuales",
        "caption": "Produccion ofensiva, participacion y comportamiento disciplinario del jugador filtrado.",
    },
    "partido": {
        "title": "Analisis de partido",
        "subtitle": "Desglose por encuentro",
        "caption": "Marcador, cronologia de eventos, periodos y momentum de gol para un partido puntual.",
    },
    "disciplina": {
        "title": "Disciplina",
        "subtitle": "Tarjetas y faltas",
        "caption": "Ranking de riesgo, IPD e incidencias por bloque de tiempo para equipos y jugadores.",
    },
    "comparativa": {
        "title": "Comparativa",
        "subtitle": "Jugador vs jugador",
        "caption": "Comparacion side-by-side con radar y tabla de metricas sobre jugadores activos en el filtro.",
    },
    "predicciones": {
        "title": "Predicciones",
        "subtitle": "Simulacion de cruces",
        "caption": "Modelo Poisson explicable y proyeccion de tabla sobre el contexto filtrado actual.",
    },
}

TEAM_COLORS = ["#78b8ff", "#45d39c", "#f3c96b", "#ff9f5a", "#ff7272", "#8dc7ff", "#98e5cc"]
DISCIPLINE_COLORS = {
    "Falta": "#ff9f5a",
    "Amarilla": "#f3c96b",
    "Azul I": "#6fb4ff",
    "Azul D": "#3d8cff",
    "Roja": "#ff7272",
}


def _style(fig: go.Figure, height: int | None = None) -> go.Figure:
    kwargs = {
        "paper_bgcolor": "#102033",
        "plot_bgcolor": "#07111f",
        "font": {"family": "Inter", "color": "#eef4fb"},
        "margin": {"t": 36, "b": 20, "l": 20, "r": 20},
    }
    if height:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(gridcolor="rgba(120, 184, 255, 0.12)", linecolor="rgba(120, 184, 255, 0.14)")
    fig.update_yaxes(gridcolor="rgba(120, 184, 255, 0.12)", linecolor="rgba(120, 184, 255, 0.14)")
    return fig


def _section(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def _metric_cards(cards: list[dict[str, str]]) -> None:
    columns = st.columns(len(cards))
    for col, card in zip(columns, cards):
        note = f'<div class="metric-note">{card["note"]}</div>' if card.get("note") else ""
        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-kicker">{card["kicker"]}</div>
                <div class="metric-value">{card["value"]}</div>
                <div class="metric-label">{card["label"]}</div>
                {note}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _info(text: str) -> None:
    st.markdown(f'<div class="info-card">{text}</div>', unsafe_allow_html=True)


def _ensure_state_option(key: str, options: list[str], preferred: str | None = None) -> str | None:
    if not options:
        st.session_state[key] = None
        return None
    if st.session_state.get(key) not in options:
        st.session_state[key] = preferred if preferred in options else options[0]
    return st.session_state[key]


def _player_default_key(catalog: pd.DataFrame, selected_name: str) -> str | None:
    if catalog.empty:
        return None
    if selected_name != "Todos":
        matches = catalog[catalog["Jugador"] == selected_name]
        if not matches.empty:
            return str(matches.iloc[0]["player_key"])
    return str(catalog.iloc[0]["player_key"])


def _team_options(partidos: pd.DataFrame) -> list[str]:
    if partidos.empty:
        return []
    return sorted(set(partidos["equipo_local"].dropna().tolist()) | set(partidos["equipo_visitante"].dropna().tolist()))


def _render_header(view_key: str, sel: dict, last_updated_label: str) -> None:
    active_cfg = VIEW_CONFIG[view_key]
    category = sel["categoria"] if sel["categoria"] != "Todas" else "Todas las categorias"
    season = sel["temporada"] if sel["temporada"] != "Todas" else "Todas las temporadas"
    team = sel["equipo"] if sel["equipo"] != "Todos" else "Todos los equipos"
    player = sel["jugador"] if sel["jugador"] != "Todos" else "Todos los jugadores"
    st.markdown(
        f"""
        <div class="main-header">
            <div class="eyebrow">FEFUSA Dashboard v1</div>
            <h1>{active_cfg["title"]}</h1>
            <p>{active_cfg["caption"]}</p>
            <div class="context-row">
                <span class="context-pill">{category}</span>
                <span class="context-pill">{season}</span>
                <span class="context-pill">{team}</span>
                <span class="context-pill">{player}</span>
                <span class="context-pill">Actualizado {last_updated_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_league_view(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    summary = analytics.build_global_summary(eventos, partidos)
    standings = analytics.build_standings(partidos)
    egr = analytics.build_egr_table(partidos)
    momentum = analytics.build_goal_momentum(eventos)
    streaks = analytics.build_current_streaks(partidos).head(8)

    cards = [
        {"kicker": "Contexto", "value": str(summary["partidos"]), "label": "Partidos analizados"},
        {"kicker": "Ataque", "value": str(summary["goles"]), "label": "Goles registrados"},
        {"kicker": "Promedio", "value": f'{summary["goles_por_partido"]:.2f}', "label": "Goles por partido"},
        {"kicker": "EGR", "value": str(summary["mejor_eficiencia"]), "label": "Equipo mas eficiente"},
        {"kicker": "Defensa", "value": str(summary["equipo_menos_goleado"]), "label": "Equipo menos goleado"},
    ]
    _metric_cards(cards)

    if not egr.empty:
        top_team = egr.iloc[0]["Equipo"]
        top_egr = egr.iloc[0]["EGR"]
        _info(f"{top_team} lidera la eficiencia goleadora relativa con un EGR de {top_egr:.1f}.")

    col_left, col_right = st.columns([1.55, 1], gap="medium")
    with col_left:
        _section("Tabla de posiciones", "Ranking competitivo con GF, GC y puntos sobre el filtro activo.")
        if standings.empty:
            st.info("Sin partidos suficientes para armar la tabla.")
        else:
            st.dataframe(standings, width="stretch", hide_index=True)
    with col_right:
        _section("Momentum global", "Distribucion de goles en los 8 bloques de 5 minutos.")
        fig = px.bar(
            momentum,
            x="Bloque",
            y="Goles",
            text="Goles",
            color="Goles",
            color_continuous_scale=["#3d8cff", "#45d39c"],
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0, textposition="outside")
        st.plotly_chart(_style(fig, height=330), width="stretch")

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        _section("Ataque vs defensa", "Goles a favor y en contra por equipo.")
        if standings.empty:
            st.info("Sin datos de equipos.")
        else:
            melted = standings.melt(id_vars="Equipo", value_vars=["GF", "GC"], var_name="Tipo", value_name="Goles")
            fig = px.bar(
                melted,
                x="Equipo",
                y="Goles",
                color="Tipo",
                barmode="group",
                color_discrete_map={"GF": "#45d39c", "GC": "#ff7272"},
            )
            fig.update_traces(marker_line_width=0)
            fig.update_xaxes(title=" ")
            st.plotly_chart(_style(fig, height=360), width="stretch")
    with col_b:
        _section("Rachas actuales", "Lectura rapida de la forma reciente por equipo.")
        if streaks.empty:
            st.info("Sin historial suficiente para calcular rachas.")
        else:
            st.dataframe(streaks, width="stretch", hide_index=True)

    _section("Eficiencia goleadora relativa", "Comparacion del promedio de goles por equipo contra el promedio de la liga.")
    if egr.empty:
        st.info("Sin datos de eficiencia.")
    else:
        fig = px.bar(
            egr.head(10),
            x="EGR",
            y="Equipo",
            orientation="h",
            color="EGR",
            color_continuous_scale=["#3d8cff", "#78b8ff", "#45d39c"],
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0, text=egr.head(10)["EGR"], textposition="outside")
        fig.update_yaxes(title=" ", autorange="reversed")
        st.plotly_chart(_style(fig, height=360), width="stretch")


def _render_team_view(eventos: pd.DataFrame, partidos: pd.DataFrame, sel: dict) -> None:
    teams = _team_options(partidos)
    if not teams:
        st.info("No hay equipos disponibles para el contexto actual.")
        return

    preferred_team = sel["equipo"] if sel["equipo"] != "Todos" else teams[0]
    _ensure_state_option("perfil_equipo", teams, preferred_team)
    team = st.selectbox("Equipo", teams, key="perfil_equipo")
    profile = analytics.build_team_profile(eventos, partidos, team)
    if not profile:
        st.info("No hay datos suficientes para ese equipo.")
        return

    summary = profile["summary"]
    cards = [
        {"kicker": "Record", "value": f'{summary["pg"]}-{summary["pe"]}-{summary["pp"]}', "label": "PG / PE / PP"},
        {"kicker": "Puntos", "value": str(summary["pts"]), "label": "PTS acumulados"},
        {"kicker": "Balance", "value": f'{summary["gf"]}/{summary["gc"]}', "label": "GF / GC"},
        {"kicker": "EGR", "value": f'{summary["egr"]:.1f}', "label": "Eficiencia relativa"},
        {"kicker": "IPD", "value": f'{summary["ipd"]:.2f}', "label": "Indice disciplinario"},
    ]
    _metric_cards(cards)
    _info(f"{team} suma {summary['gf']} goles a favor, {summary['gc']} en contra y una diferencia de {summary['dif']}.")

    col_left, col_right = st.columns([1.15, 1], gap="medium")
    with col_left:
        _section("Ultimos 5 resultados", "Partidos mas recientes del equipo dentro del contexto activo.")
        st.dataframe(profile["last_five"], width="stretch", hide_index=True)
    with col_right:
        _section("Ritmo por partido", "Lectura neutral del volumen competitivo sin asumir condicion de localia.")
        st.dataframe(profile["per_match"], width="stretch", hide_index=True)

    _section("Momentum de gol del equipo", "Goles a favor y en contra por franja de 5 minutos.")
    momentum = profile["momentum"]
    if momentum.empty:
        st.info("No hay goles suficientes para construir el momentum.")
    else:
        fig = px.bar(
            momentum,
            x="Bloque",
            y="Goles",
            color="Tipo",
            barmode="group",
            color_discrete_map={"A favor": "#45d39c", "En contra": "#ff7272"},
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(_style(fig, height=360), width="stretch")


def _render_player_view(eventos: pd.DataFrame, sel: dict) -> None:
    catalog = analytics.build_player_catalog(eventos)
    if catalog.empty:
        st.info("No hay jugadores disponibles para el filtro actual.")
        return

    options = catalog["player_key"].astype(str).tolist()
    labels = dict(zip(catalog["player_key"].astype(str), catalog["label"]))
    preferred = _player_default_key(catalog, sel["jugador"])
    _ensure_state_option("perfil_jugador_key", options, preferred)
    player_key = st.selectbox("Jugador", options, key="perfil_jugador_key", format_func=lambda key: labels.get(str(key), str(key)))
    profile = analytics.build_player_profile(eventos, str(player_key))
    if not profile:
        st.info("No se pudieron construir metricas para el jugador seleccionado.")
        return

    summary = profile["summary"]
    cards = [
        {"kicker": "Jugador", "value": str(summary["goles"]), "label": "Goles totales"},
        {"kicker": "Participacion", "value": str(summary["partidos"]), "label": "Partidos con eventos"},
        {"kicker": "Tasa", "value": f'{summary["goles_por_partido"]:.2f}', "label": "Goles por partido"},
        {"kicker": "Disciplina", "value": str(summary["faltas"]), "label": "Faltas cometidas"},
        {"kicker": "IPD", "value": f'{summary["ipd"]:.2f}', "label": "Indice disciplinario"},
    ]
    _metric_cards(cards)
    _info(f"{profile['label']} combina {summary['goles']} goles con un IPD de {summary['ipd']:.2f} en el contexto filtrado.")

    col_left, col_right = st.columns(2, gap="medium")
    with col_left:
        _section("Evolucion por jornada", "Goles del jugador a lo largo de sus partidos registrados.")
        timeline = profile["timeline"]
        if timeline.empty:
            st.info("Sin suficientes partidos para graficar evolucion.")
        else:
            fig = px.line(
                timeline,
                x="Partido",
                y="Goles",
                markers=True,
                hover_data=["Jornada"],
                color_discrete_sequence=["#78b8ff"],
            )
            st.plotly_chart(_style(fig, height=340), width="stretch")
    with col_right:
        _section("Distribucion temporal de goles", "En que tramos del partido convierte con mayor frecuencia.")
        momentum = profile["momentum"]
        fig = px.bar(
            momentum,
            x="Bloque",
            y="Goles",
            text="Goles",
            color="Goles",
            color_continuous_scale=["#3d8cff", "#45d39c"],
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0, textposition="outside")
        st.plotly_chart(_style(fig, height=340), width="stretch")

    _section("Disciplina del jugador", "Detalle basico de tarjetas y faltas sobre el jugador activo.")
    breakdown = pd.DataFrame(
        [
            {"Metrica": "Amarillas", "Valor": summary["amarillas"]},
            {"Metrica": "Azul indirecta", "Valor": summary["azul_i"]},
            {"Metrica": "Azul directa", "Valor": summary["azul_d"]},
            {"Metrica": "Rojas", "Valor": summary["rojas"]},
            {"Metrica": "Faltas", "Valor": summary["faltas"]},
        ]
    )
    st.dataframe(breakdown, width="stretch", hide_index=True)


def _render_match_score(match: dict[str, object]) -> None:
    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-teams">
                <div>{match["local"]}</div>
                <div class="score-value">{match["goles_local"]} - {match["goles_visitante"]}</div>
                <div>{match["visitante"]}</div>
            </div>
            <div class="score-meta">Jornada {match["jornada"]} · {match.get("fecha", "Sin fecha")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_match_view(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    selector = analytics.build_match_selector(partidos)
    if selector.empty:
        st.info("No hay partidos disponibles para el contexto actual.")
        return

    options = selector["id"].astype(str).tolist()
    labels = dict(zip(selector["id"].astype(str), selector["label"]))
    _ensure_state_option("partido_id", options, options[0])
    match_id = st.selectbox("Partido", options, key="partido_id", format_func=lambda value: labels.get(str(value), str(value)))
    dataset = analytics.build_match_dataset(eventos, partidos, str(match_id))
    if not dataset:
        st.info("No se encontraron datos para el partido seleccionado.")
        return

    match = dataset["match"]
    _render_match_score(match)
    total_events = int(dataset["events"].shape[0])
    total_goals = int(analytics.goal_events(dataset["events"]).shape[0])
    total_cards = int(dataset["events"]["tipo_evento"].isin(list(analytics.CARD_EVENTS)).sum()) if not dataset["events"].empty else 0
    total_fouls = int((dataset["events"]["tipo_evento"] == "Falta").sum()) if not dataset["events"].empty else 0
    _metric_cards(
        [
            {"kicker": "Partido", "value": str(total_events), "label": "Eventos registrados"},
            {"kicker": "Goles", "value": str(total_goals), "label": "Goles del partido"},
            {"kicker": "Tarjetas", "value": str(total_cards), "label": "Tarjetas totales"},
            {"kicker": "Faltas", "value": str(total_fouls), "label": "Faltas totales"},
        ]
    )
    if int(dataset.get("non_regular_goal_events", 0)) > 0:
        st.caption("La cronologia puede incluir goles fuera de 1T/2T, como definiciones por penales. Esos eventos no se cuentan en los KPIs ni en los graficos de gol.")

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        _section("Momentum del partido", "Goles por bloque de 5 minutos y por equipo.")
        momentum = dataset["momentum"]
        if momentum.empty:
            st.info("Sin goles suficientes para graficar el momentum.")
        else:
            fig = px.bar(
                momentum,
                x="Bloque",
                y="Goles",
                color="Equipo",
                barmode="group",
                color_discrete_sequence=TEAM_COLORS,
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(_style(fig, height=340), width="stretch")
    with col_b:
        _section("Goles por periodo", "Desglose de goles entre primer y segundo tiempo.")
        period_summary = dataset["period_summary"]
        if period_summary.empty:
            st.info("Sin goles con periodo identificado.")
        else:
            fig = px.bar(
                period_summary,
                x="Periodo",
                y="Goles",
                color="Equipo",
                barmode="group",
                color_discrete_sequence=TEAM_COLORS,
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(_style(fig, height=340), width="stretch")

    st.caption("Cronologia completa de eventos ordenados por minuto.")
    charts.match_timeline(dataset["events"], equipo_izq=str(match["local"]), equipo_der=str(match["visitante"]))


def _render_discipline_view(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    team_disc = analytics.build_team_discipline(eventos, partidos)
    player_disc = analytics.build_player_discipline(eventos)
    timeline = analytics.build_discipline_timeline(eventos)

    cards = [
        {"kicker": "Incidencias", "value": str(int(analytics.discipline_events(eventos).shape[0])), "label": "Eventos disciplinarios"},
        {"kicker": "Equipos", "value": team_disc.iloc[0]["Equipo"] if not team_disc.empty else "Sin datos", "label": "Mayor IPD por equipo"},
        {"kicker": "Jugadores", "value": player_disc.iloc[0]["Jugador"] if not player_disc.empty else "Sin datos", "label": "Mayor IPD individual"},
        {"kicker": "Riesgo", "value": f'{team_disc.iloc[0]["IPD"]:.2f}' if not team_disc.empty else "0.00", "label": "IPD mas alto"},
    ]
    _metric_cards(cards)

    if not team_disc.empty:
        top_team = team_disc.iloc[0]
        _info(f'{top_team["Equipo"]} encabeza el riesgo disciplinario con IPD {top_team["IPD"]:.2f} y estado {top_team["Riesgo"].lower()}.')

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        _section("Ranking disciplinario por equipo", "IPD, faltas y tarjetas ponderadas por partidos.")
        if team_disc.empty:
            st.info("Sin datos disciplinarios por equipo.")
        else:
            view = team_disc.copy().head(10)
            fig = px.bar(
                view,
                x="IPD",
                y="Equipo",
                orientation="h",
                text="IPD",
                color="Riesgo",
                color_discrete_map={"Bajo": "#45d39c", "Medio": "#f3c96b", "Alto": "#ff7272"},
            )
            fig.update_traces(marker_line_width=0, textposition="outside")
            fig.update_yaxes(title=" ", autorange="reversed")
            st.plotly_chart(_style(fig, height=360), width="stretch")
    with col_b:
        _section("Minutos criticos", "Cuando se concentran las incidencias disciplinarias.")
        if timeline.empty:
            st.info("Sin datos disciplinarios para graficar.")
        else:
            fig = px.bar(
                timeline,
                x="Bloque",
                y="Cantidad",
                color="tipo_evento",
                barmode="stack",
                color_discrete_map=DISCIPLINE_COLORS,
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(_style(fig, height=360), width="stretch")

    col_team, col_player = st.columns(2, gap="medium")
    with col_team:
        _section("Tabla de equipos", "Detalle completo de riesgo por equipo.")
        if team_disc.empty:
            st.info("Sin datos de equipos.")
        else:
            st.dataframe(team_disc, width="stretch", hide_index=True)
    with col_player:
        _section("Tabla de jugadores", "Detalle completo de riesgo por jugador.")
        if player_disc.empty:
            st.info("Sin datos de jugadores.")
        else:
            st.dataframe(player_disc.head(20), width="stretch", hide_index=True)


def _render_comparison_view(eventos: pd.DataFrame) -> None:
    catalog = analytics.build_player_catalog(eventos)
    if len(catalog) < 2:
        st.info("Se necesitan al menos dos jugadores con datos para comparar.")
        return

    options = catalog["player_key"].astype(str).tolist()
    labels = dict(zip(catalog["player_key"].astype(str), catalog["label"]))

    preferred_a = st.session_state.get("jugador_a") if st.session_state.get("jugador_a") in options else options[0]
    preferred_b = st.session_state.get("jugador_b") if st.session_state.get("jugador_b") in options and st.session_state.get("jugador_b") != preferred_a else options[1]
    _ensure_state_option("jugador_a", options, preferred_a)

    col_a, col_b = st.columns(2)
    with col_a:
        player_a = st.selectbox("Jugador A", options, key="jugador_a", format_func=lambda key: labels.get(str(key), str(key)))

    remaining = [opt for opt in options if opt != player_a]
    _ensure_state_option("jugador_b", remaining, preferred_b if preferred_b in remaining else remaining[0])
    with col_b:
        player_b = st.selectbox("Jugador B", remaining, key="jugador_b", format_func=lambda key: labels.get(str(key), str(key)))

    comparison = analytics.build_player_comparison(eventos, str(player_a), str(player_b))
    if not comparison:
        st.info("No se pudo construir la comparativa para esos jugadores.")
        return

    _info(f'{comparison["label_a"]} vs {comparison["label_b"]}. El radar invierte IPD y faltas para que un valor mayor implique mejor perfil.')

    col_left, col_right = st.columns([1.05, 1], gap="medium")
    with col_left:
        _section("Radar comparativo", "Ataque, participacion y disciplina relativa entre ambos perfiles.")
        radar = comparison["radar"]
        categories = radar["Metrica"].tolist()
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=radar["A"].tolist() + [radar["A"].tolist()[0]],
                theta=categories + [categories[0]],
                mode="lines+markers",
                fill="toself",
                fillcolor="rgba(120, 184, 255, 0.24)",
                name=comparison["label_a"],
                line=dict(color="#78b8ff", width=3),
                marker=dict(size=8, color="#78b8ff"),
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=radar["B"].tolist() + [radar["B"].tolist()[0]],
                theta=categories + [categories[0]],
                mode="lines+markers",
                fill="toself",
                fillcolor="rgba(69, 211, 156, 0.24)",
                name=comparison["label_b"],
                line=dict(color="#45d39c", width=3),
                marker=dict(size=8, color="#45d39c"),
            )
        )
        fig.update_layout(
            polar=dict(
                bgcolor="#07111f",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(120, 184, 255, 0.14)"),
                angularaxis=dict(gridcolor="rgba(120, 184, 255, 0.12)"),
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        st.plotly_chart(_style(fig, height=420), width="stretch")
    with col_right:
        _section("Tabla side-by-side", "Metricas actuales sin depender de minutos jugados ni asistencias.")
        st.dataframe(comparison["table"], width="stretch", hide_index=True)
        bar_data = comparison["table"].melt(id_vars="Metrica", var_name="Jugador", value_name="Valor")
        fig = px.bar(
            bar_data,
            x="Metrica",
            y="Valor",
            color="Jugador",
            barmode="group",
            color_discrete_sequence=["#78b8ff", "#45d39c"],
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(_style(fig, height=320), width="stretch")


def render_dashboard_view(view_key: str, eventos: pd.DataFrame, partidos: pd.DataFrame, sel: dict, last_updated_label: str) -> None:
    _render_header(view_key, sel, last_updated_label)
    active_cfg = VIEW_CONFIG[view_key]
    _section(active_cfg["title"], active_cfg["caption"])

    if view_key == "liga":
        _render_league_view(eventos, partidos)
    elif view_key == "equipo":
        _render_team_view(eventos, partidos, sel)
    elif view_key == "jugador":
        _render_player_view(eventos, sel)
    elif view_key == "partido":
        _render_match_view(eventos, partidos)
    elif view_key == "disciplina":
        _render_discipline_view(eventos, partidos)
    elif view_key == "comparativa":
        _render_comparison_view(eventos)


def render_dashboard_tab(view_key: str, eventos: pd.DataFrame, partidos: pd.DataFrame, sel: dict, last_updated_label: str) -> None:
    render_dashboard_view(view_key, eventos, partidos, sel, last_updated_label)


def render_predictions_tab(partidos: pd.DataFrame, sel: dict, last_updated_label: str) -> None:
    _render_header("predicciones", sel, last_updated_label)
    active_cfg = VIEW_CONFIG["predicciones"]
    _section(active_cfg["title"], active_cfg["caption"])

    base_matches = predictions.prepare_matches(partidos)
    equipos_pred = (
        sorted(pd.concat([base_matches["equipo_local"], base_matches["equipo_visitante"]]).dropna().unique().tolist())
        if not base_matches.empty
        else []
    )

    if len(equipos_pred) < 2:
        st.info("No hay suficientes equipos con datos para generar predicciones en este contexto.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        team_a = st.selectbox("Equipo A", equipos_pred, index=0)

    team_b_options = [team for team in equipos_pred if team != team_a]
    with col_b:
        team_b = st.selectbox("Equipo B", team_b_options, index=0)

    pred = predictions.predict_match(base_matches, team_a, team_b)
    probs = pred["probs"]
    winner = (
        f"victoria de {team_a}"
        if probs["win_a"] >= max(probs["draw"], probs["win_b"])
        else "empate"
        if probs["draw"] >= probs["win_b"]
        else f"victoria de {team_b}"
    )
    _info(f"Resultado mas probable para el proximo cruce estimado: {winner}.")

    _metric_cards(
        [
            {"kicker": "1X2", "value": f'{probs["win_a"]*100:.1f}%', "label": f"Gana {team_a}"},
            {"kicker": "1X2", "value": f'{probs["draw"]*100:.1f}%', "label": "Empate"},
            {"kicker": "1X2", "value": f'{probs["win_b"]*100:.1f}%', "label": f"Gana {team_b}"},
            {"kicker": "xG", "value": f'{pred["xg_total"]:.2f}', "label": "Goles esperados totales", "note": pred["details"]},
        ]
    )

    _section("Goles esperados", "Modelo Poisson simple basado en fortalezas ofensivas y defensivas.")
    xg_df = pd.DataFrame(
        [
            {"Equipo": team_a, "xG": pred["xg_a"]},
            {"Equipo": team_b, "xG": pred["xg_b"]},
        ]
    )
    fig = px.bar(xg_df, x="Equipo", y="xG", text="xG", color="Equipo", color_discrete_sequence=["#78b8ff", "#45d39c"])
    fig.update_traces(marker_line_width=0, textposition="outside")
    st.plotly_chart(_style(fig, height=320), width="stretch")

    _section("Proyeccion de tabla (+1 fecha)", "Tabla a ancho completo para evitar que la simulacion quede comprimida.")
    proj = predictions.project_table(base_matches, simulations=800)
    if proj.empty:
        fallback = predictions.current_table(base_matches)
        if fallback.empty:
            st.info("No hay datos suficientes para proyectar ni mostrar una tabla base.")
        else:
            st.caption("La simulacion no devolvio una proyeccion usable; se muestra la tabla actual del contexto filtrado.")
            st.dataframe(fallback, width="stretch", hide_index=True, height=min(420, 56 + len(fallback) * 35))
    else:
        st.dataframe(proj, width="stretch", hide_index=True, height=min(420, 56 + len(proj) * 35))
