"""
Todos los gráficos Plotly del dashboard.
Cada función recibe un DataFrame ya filtrado y renderiza con st.plotly_chart.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# ─── Constantes de tema ───────────────────────────────────────────────────────
COLORS = {
    "Gol":      "#3fb950",      # Verde claro (éxito)
    "Falta":    "#ff8800",      # Naranja (advertencia/infracción leve)
    "Amarilla": "#d29922",      # Amarillo oscuro
    "Roja":     "#ff4444",      # Rojo puro
    "Azul I":   "#58a6ff",      # Celeste/Azul claro (indirecta)
    "Azul D":   "#1f6feb",      # Azul oscuro (directa)
    "Lesionado":"#8b949e",      # Gris
    "Penal Gol": "#2ea043",     # Verde chillón
    "Penal Errado": "#a371f7",  # Morado / Púrpura
}

_TEMPLATE = "plotly_dark"
_BG_PAPER = "#161b22"
_BG_PLOT  = "#0d1117"


def _style(fig, height: int | None = None):
    """Aplica el tema oscuro a cualquier figura Plotly."""
    kwargs = dict(
        paper_bgcolor=_BG_PAPER,
        plot_bgcolor=_BG_PLOT,
        font=dict(family="Inter", color="#e6edf3"),
        margin=dict(t=40, b=20, l=20, r=20),
        title_font_size=14,
    )
    if height:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(gridcolor="#21262d", linecolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d", linecolor="#21262d")
    return fig


# ─── Gráficos ─────────────────────────────────────────────────────────────────

def goals_by_team(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">⚽ Goles por Equipo</div>', unsafe_allow_html=True)
    data = (
        eventos[eventos["tipo_evento"] == "Gol"]
        .groupby("equipo", as_index=False).size()
        .rename(columns={"size": "Goles"})
        .sort_values("Goles", ascending=True)
    )
    if data.empty:
        st.info("Sin datos de goles para los filtros seleccionados.")
        return
    fig = px.bar(
        data, x="Goles", y="equipo", orientation="h",
        color="Goles", color_continuous_scale=["#1f6feb","#58a6ff","#79c0ff"],
        template=_TEMPLATE,
    )
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}: %{x} goles<extra></extra>")
    fig.update_coloraxes(showscale=False, colorbar_title_text="")
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title=" ")
    st.plotly_chart(_style(fig), width="stretch")


def events_by_type(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">📌 Eventos por Tipo</div>', unsafe_allow_html=True)
    data = (
        eventos.groupby("tipo_evento", as_index=False).size()
        .rename(columns={"size": "Cantidad"})
        .sort_values("Cantidad", ascending=False)
    )
    if data.empty:
        st.info("Sin datos para los filtros seleccionados.")
        return
    fig = px.pie(
        data, names="tipo_evento", values="Cantidad",
        hole=0.55, color="tipo_evento", color_discrete_map=COLORS,
        template=_TEMPLATE,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
    fig.update_layout(
        showlegend=False, paper_bgcolor=_BG_PAPER, plot_bgcolor=_BG_PLOT,
        font=dict(family="Inter", color="#e6edf3"), margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, width="stretch")


def goals_by_round(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">📅 Goles por Jornada</div>', unsafe_allow_html=True)
    data = (
        eventos[eventos["tipo_evento"] == "Gol"]
        .groupby("jornada", as_index=False).size()
        .rename(columns={"size": "Goles"})
        .sort_values("jornada")
    )
    if data.empty:
        st.info("Sin datos de goles.")
        return
    data["jornada"] = data["jornada"].astype(str)
    fig = px.bar(
        data, x="jornada", y="Goles",
        color_discrete_sequence=["#3fb950"],
        labels={"jornada": "Jornada"}, template=_TEMPLATE, text="Goles",
    )
    fig.update_traces(textposition="outside", textfont_color="#e6edf3", marker_line_width=0)
    st.plotly_chart(_style(fig), width="stretch")


def top_scorers(eventos: pd.DataFrame, top_n: int = 10) -> None:
    st.markdown('<div class="section-title">🏅 Ranking de Goleadores</div>', unsafe_allow_html=True)
    goles = eventos[eventos["tipo_evento"] == "Gol"].copy()
    if goles.empty:
        st.info("Sin goleadores para los filtros seleccionados.")
        return
        
    goles["jugador_equipo"] = goles["jugador"] + " (" + goles["equipo"] + ")"
    data = (
        goles.groupby(["jugador_equipo", "equipo"], as_index=False).size()
        .rename(columns={"size": "Goles"})
        .sort_values("Goles", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    if data.empty:
        st.info("Sin goleadores para los filtros seleccionados.")
        return
    fig = px.bar(
        data, x="Goles", y="jugador_equipo", orientation="h",
        color="Goles", color_continuous_scale=["#1a4731","#3fb950"],
        hover_data=["equipo"], template=_TEMPLATE,
    )
    fig.update_traces(marker_line_width=0, text=data["Goles"].values, textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_yaxes(title=" ")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(_style(fig, height=360), width="stretch")


def team_performance(partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">📈 Rendimiento por Equipo (G / E / P)</div>', unsafe_allow_html=True)
    if partidos.empty:
        st.info("Sin partidos para los filtros seleccionados.")
        return

    rows = []
    for _, row in partidos.iterrows():
        gl, gv = row["goles_local"], row["goles_visitante"]
        local, visit = row["equipo_local"], row["equipo_visitante"]
        if gl > gv:
            rows += [{"equipo": local, "G":1,"E":0,"P":0}, {"equipo": visit, "G":0,"E":0,"P":1}]
        elif gl < gv:
            rows += [{"equipo": local, "G":0,"E":0,"P":1}, {"equipo": visit, "G":1,"E":0,"P":0}]
        else:
            rows += [{"equipo": local, "G":0,"E":1,"P":0}, {"equipo": visit, "G":0,"E":1,"P":0}]

    if not rows:
        return

    df = pd.DataFrame(rows).groupby("equipo", as_index=False).sum()
    df["Puntos"] = df["G"] * 3 + df["E"]
    df = df.sort_values("Puntos", ascending=False)

    df_melt = df.melt(id_vars="equipo", value_vars=["G","E","P"], var_name="Resultado", value_name="Cantidad")
    df_melt["Resultado"] = df_melt["Resultado"].map({"G":"Ganados","E":"Empatados","P":"Perdidos"})
    color_map = {"Ganados":"#3fb950","Empatados":"#d29922","Perdidos":"#f85149"}

    fig = px.bar(
        df_melt, x="equipo", y="Cantidad", color="Resultado",
        color_discrete_map=color_map, barmode="stack",
        labels={"Cantidad": "Partidos"}, template=_TEMPLATE,
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.08, font_size=11))
    fig.update_xaxes(title=" ")
    st.plotly_chart(_style(fig), width="stretch")





def goals_by_period(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">⏱️ Goles por Periodo (1T vs 2T)</div>', unsafe_allow_html=True)
    goles = eventos[eventos["tipo_evento"] == "Gol"].copy()
    if goles.empty:
        st.info("Sin datos de goles para analizar periodos.")
        return
        
    goles["Periodo"] = goles["periodo"].map({1: "Primer Tiempo", 2: "Segundo Tiempo"})
    data = goles.groupby("Periodo", as_index=False).size().rename(columns={"size": "Goles"})
    
    fig = px.pie(
        data, names="Periodo", values="Goles", hole=0.5,
        color="Periodo", color_discrete_map={"Primer Tiempo": "#1f6feb", "Segundo Tiempo": "#58a6ff"},
        template=_TEMPLATE
    )
    fig.update_traces(textposition="inside", textinfo="percent+label+value", textfont_size=12)
    fig.update_layout(showlegend=False, paper_bgcolor=_BG_PAPER, plot_bgcolor=_BG_PLOT)
    st.plotly_chart(fig, width="stretch")


def match_timeline(eventos: pd.DataFrame, tipos_permitidos: list = None) -> None:
    st.markdown('<div class="section-title">⏳ Evolución del Marcador y Eventos (Línea de Tiempo)</div>', unsafe_allow_html=True)
    
    partidos_unicos = eventos["partido_id"].nunique()
    if partidos_unicos != 1:
        st.info("⏳ Seleccioná los filtros de arriba para encontrar un partido específico y ver su línea de tiempo detallada.")
        return
        
    if not tipos_permitidos:
        tipos_permitidos = ["Gol", "Amarilla", "Roja", "Azul I", "Azul D"]
        
    data = eventos[eventos["tipo_evento"].isin(tipos_permitidos)].copy()
    
    if data.empty:
        st.info("Sin eventos destacados para este partido bajo los filtros seleccionados.")
        return
        
    data = data.sort_values(["equipo", "minuto", "tipo_evento", "jugador"]).copy()
    data["minuto_str"] = data["minuto"].astype(str) + "'"
    data["etiqueta"] = data["jugador"].fillna("Sin jugador") + " (" + data["equipo"].fillna("Sin equipo") + ")"

    # Evita solapamiento visual cuando hay múltiples eventos del mismo equipo/minuto
    equipos_orden = data["equipo"].dropna().unique().tolist()
    team_to_y = {equipo: idx for idx, equipo in enumerate(equipos_orden)}
    data["base_y"] = data["equipo"].map(team_to_y)

    # 1) Sub-carriles por tipo de evento dentro de cada equipo (separación vertical estable)
    tipos_orden = ["Gol", "Falta", "Amarilla", "Roja", "Azul I", "Azul D", "Lesionado", "Penal Gol", "Penal Errado"]
    tipos_presentes = [t for t in tipos_orden if t in data["tipo_evento"].unique().tolist()]
    if not tipos_presentes:
        tipos_presentes = sorted(data["tipo_evento"].dropna().unique().tolist())
    n_tipos = len(tipos_presentes)
    if n_tipos > 1:
        type_offsets = {t: (i - (n_tipos - 1) / 2) * 0.10 for i, t in enumerate(tipos_presentes)}
    else:
        type_offsets = {tipos_presentes[0]: 0.0}
    data["tipo_offset"] = data["tipo_evento"].map(type_offsets).fillna(0.0)

    # 2) Jitter horizontal y vertical adicional para duplicados exactos (equipo+minuto+tipo)
    data["dup_tipo_idx"] = data.groupby(["equipo", "minuto", "tipo_evento"]).cumcount()
    data["dup_tipo_total"] = data.groupby(["equipo", "minuto", "tipo_evento"])["tipo_evento"].transform("size")

    x_jitter = 0.24
    y_jitter = 0.035
    data["x_plot"] = data["minuto"] + (data["dup_tipo_idx"] - (data["dup_tipo_total"] - 1) / 2) * x_jitter
    data["y_plot"] = data["base_y"] + data["tipo_offset"] + (data["dup_tipo_idx"] - (data["dup_tipo_total"] - 1) / 2) * y_jitter

    fig = px.scatter(
        data,
        x="x_plot",
        y="y_plot",
        color="tipo_evento",
        custom_data=["etiqueta", "tipo_evento", "minuto_str"],
        text="minuto_str",
        color_discrete_map=COLORS,
        template=_TEMPLATE,
        labels={"x_plot": "Minuto del Partido", "y_plot": "Equipo"},
    )
    fig.update_traces(
        marker=dict(size=11, opacity=0.95, line=dict(width=1, color="white")),
        textposition="top center",
        hovertemplate="<b>%{customdata[0]}</b><br>Evento: %{customdata[1]}<br>Minuto: %{customdata[2]}<extra></extra>",
    )
    x_min = max(-0.5, float(data["x_plot"].min()) - 1.0)
    x_max = min(40.5, float(data["x_plot"].max()) + 1.0)
    fig.update_xaxes(range=[x_min, x_max], dtick=5, title="Minuto del Partido")

    y_min = -0.7
    y_max = max(len(equipos_orden) - 1, 0) + 0.7
    fig.update_yaxes(
        title=" ",
        tickmode="array",
        tickvals=list(range(len(equipos_orden))),
        ticktext=equipos_orden,
        range=[y_min, y_max],
    )

    # Forzar título vacío para evitar que algunos renders muestren "undefined"
    fig.update_layout(title_text="")

    # Aplicar estilo primero, luego sobrescribir márgenes para que no se pisen
    fig = _style(fig, height=320)
    fig.update_layout(margin=dict(t=40, l=150, r=20, b=20))
    st.plotly_chart(fig, width="stretch")


def fouls_scatter(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">⚔️ Faltas Cometidas vs Recibidas</div>', unsafe_allow_html=True)
    if eventos.empty or partidos.empty:
        st.info("Sin datos suficientes.")
        return

    # Faltas cometidas
    cometidas = eventos[eventos["tipo_evento"] == "Falta"].groupby("equipo").size().reset_index(name="Cometidas")
    
    # Calcular faltas recibidas infiriendo rivales
    recibidas_list = []
    faltas_raw = eventos[eventos["tipo_evento"] == "Falta"]
    for _, f in faltas_raw.iterrows():
        partido = partidos[partidos["id"] == f["partido_id"]]
        if not partido.empty:
            p = partido.iloc[0]
            infractor = f["equipo"]
            victima = p["equipo_visitante"] if p["equipo_local"] == infractor else p["equipo_local"]
            recibidas_list.append(victima)
            
    recibidas = pd.Series(recibidas_list).value_counts().reset_index()
    recibidas.columns = ["equipo", "Recibidas"]
    
    df = pd.merge(cometidas, recibidas, on="equipo", how="outer").fillna(0)
    if df.empty:
        st.info("Sin datos de faltas.")
        return
        
    fig = px.scatter(
        df, x="Cometidas", y="Recibidas", text="equipo", size="Cometidas",
        color="equipo", template=_TEMPLATE,
        labels={"Cometidas": "Faltas Cometidas", "Recibidas": "Faltas Recibidas"}
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(showlegend=False)
    # Lína diagonal x=y para ver quién pega más de lo que recibe
    max_val = max(df["Cometidas"].max(), df["Recibidas"].max())
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="#8b949e", dash="dash"))
    st.plotly_chart(_style(fig), width="stretch")


def disciplinary_timeline(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🟥 Evolución de Tarjetas por Bloques (10 min)</div>', unsafe_allow_html=True)
    tarjetas = eventos[eventos["tipo_evento"].isin(["Amarilla", "Roja", "Azul I", "Azul D"])].copy()
    if tarjetas.empty:
        st.info("Sin tarjetas para los filtros seleccionados.")
        return
        
    # Crear tramos de 10 minutos
    bins = [0, 10, 20, 30, 40]
    labels = ["0-10'", "10-20'", "20-30'", "30-40'"]
    tarjetas["Tramo"] = pd.cut(tarjetas["minuto"], bins=bins, labels=labels, include_lowest=True)
    
    data = tarjetas.groupby(["Tramo", "tipo_evento"], as_index=False, observed=False).size().rename(columns={"size": "Cantidad"})
    
    fig = px.bar(
        data, x="Tramo", y="Cantidad", color="tipo_evento",
        barmode="group", color_discrete_map=COLORS, template=_TEMPLATE,
        labels={"Tramo": "Minuto de Partido", "tipo_evento": "Tarjeta"}
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(_style(fig), width="stretch")


def goals_conceded(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🛡️ Goles Recibidos por Equipo</div>', unsafe_allow_html=True)
    if eventos.empty or partidos.empty:
        st.info("Sin datos para calcular goles recibidos.")
        return
        
    goles = eventos[eventos["tipo_evento"] == "Gol"]
    if goles.empty:
        st.info("Sin datos de goles.")
        return
        
    # Calcular goles recibidos infiriendo rivales
    recibidos_list = []
    for _, g in goles.iterrows():
        partido = partidos[partidos["id"] == g["partido_id"]]
        if not partido.empty:
            p = partido.iloc[0]
            anotador = g["equipo"]
            victima = p["equipo_visitante"] if p["equipo_local"] == anotador else p["equipo_local"]
            recibidos_list.append(victima)
            
    if not recibidos_list:
        return
        
    data = pd.Series(recibidos_list).value_counts().reset_index()
    data.columns = ["equipo", "Goles Recibidos"]
    data = data.sort_values("Goles Recibidos", ascending=True)
    
    fig = px.bar(
        data, x="Goles Recibidos", y="equipo", orientation="h",
        text="Goles Recibidos",
        color="Goles Recibidos", color_continuous_scale=["#1f6feb", "#f85149"],
        template=_TEMPLATE
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    fig.update_yaxes(title=" ")
    st.plotly_chart(_style(fig), width="stretch")


def top_undisciplined(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🪓 Top Jugadores más Indisciplinados <span style="font-size:0.8rem; font-weight:normal; color:#8b949e;">(Falta=1, 🟨/🟦=2, 🔵=3, 🟥=4)</span></div>', unsafe_allow_html=True)
    tarjetas = eventos[eventos["tipo_evento"].isin(["Falta", "Amarilla", "Roja", "Azul I", "Azul D"])].copy()
    if tarjetas.empty:
        st.info("Sin datos de indisciplina.")
        return
        
    pesos = {"Falta": 1, "Amarilla": 2, "Azul I": 2, "Azul D": 3, "Roja": 4}
    tarjetas["Peso"] = tarjetas["tipo_evento"].map(pesos)
    tarjetas["jugador_equipo"] = tarjetas["jugador"] + " (" + tarjetas["equipo"] + ")"
    
    data = tarjetas.groupby(["jugador_equipo", "equipo"], as_index=False)["Peso"].sum().rename(columns={"Peso": "Puntaje Malo"})
    data = data.sort_values("Puntaje Malo", ascending=False).head(10).reset_index(drop=True)
    
    fig = px.bar(
        data, x="Puntaje Malo", y="jugador_equipo", orientation="h",
        color="Puntaje Malo", color_continuous_scale=["#ff8800", "#ff4444"],
        hover_data=["equipo"], template=_TEMPLATE, labels={"Puntaje Malo": "Puntaje de Infracciones"}
    )
    fig.update_traces(text=data["Puntaje Malo"], textposition="outside", marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    fig.update_yaxes(title=" ")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(_style(fig, height=360), width="stretch")


def efficiency_vs_discipline(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">⚖️ Eficiencia Ofensiva vs Disciplina</div>', unsafe_allow_html=True)
    if eventos.empty or partidos.empty:
        st.info("Sin datos para analizar eficiencia y disciplina.")
        return
        
    # Calcular partidos jugados por equipo
    pj = pd.concat([partidos["equipo_local"], partidos["equipo_visitante"]]).value_counts().reset_index()
    pj.columns = ["equipo", "PJ"]
    
    # Goles
    goles = eventos[eventos["tipo_evento"] == "Gol"].groupby("equipo").size().reset_index(name="Goles")
    
    # Indisciplina
    tarjetas = eventos[eventos["tipo_evento"].isin(["Falta", "Amarilla", "Roja", "Azul I", "Azul D"])].copy()
    pesos = {"Falta": 1, "Amarilla": 2, "Azul I": 2, "Azul D": 3, "Roja": 4}
    tarjetas["Peso"] = tarjetas["tipo_evento"].map(pesos)
    disc = tarjetas.groupby("equipo", as_index=False)["Peso"].sum().rename(columns={"Peso": "Puntos_Disc"})
    
    # Merge
    df = pd.merge(pj, goles, on="equipo", how="left").fillna({"Goles": 0})
    df = pd.merge(df, disc, on="equipo", how="left").fillna({"Puntos_Disc": 0})
    
    df = df[df["PJ"] > 0]
    if df.empty:
        st.info("No hay partidos jugados.")
        return
        
    df["Goles/Partido"] = round(df["Goles"] / df["PJ"], 2)
    df["Disc/Partido"] = round(df["Puntos_Disc"] / df["PJ"], 2)
    
    # Asegurar que el tamaño mínimo para visualmente ver los puntos sea mayor a 0
    # Add a small base value so teams with 0 matches don't crash (though they are filtered)
    
    fig = px.scatter(
        df, x="Goles/Partido", y="Disc/Partido", text="equipo", size="PJ",
        color="equipo", hover_data=["Goles", "Puntos_Disc", "PJ"],
        template=_TEMPLATE,
        labels={
            "Goles/Partido": "Goles por Partido (Ataque)",
            "Disc/Partido": "Puntos Disc. por Partido",
            "PJ": "Partidos Jugados"
        }
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(showlegend=False)
    
    # Cuadrantes (medias)
    if not df.empty and len(df) > 1:
        mean_x = df["Goles/Partido"].mean()
        mean_y = df["Disc/Partido"].mean()
        fig.add_vline(x=mean_x, line_width=1, line_dash="dash", line_color="#8b949e", annotation_text="Media Goles")
        fig.add_hline(y=mean_y, line_width=1, line_dash="dash", line_color="#8b949e", annotation_text="Media Disc.")
        
    st.plotly_chart(_style(fig), width="stretch")


def top_scorers_timeline(eventos: pd.DataFrame, top_n: int = 5) -> None:
    st.markdown('<div class="section-title">📉 Carrera de Goleadores (Acumulado por Jornada)</div>', unsafe_allow_html=True)
    goles = eventos[eventos["tipo_evento"] == "Gol"].copy()
    
    if goles.empty or "jornada" not in goles.columns:
        st.info("Sin datos de goles con jornada para dibujar la línea de tiempo.")
        return
        
    # Obtener los top N goleadores históricos para filtrar
    top_jugadores = (
        goles.groupby("jugador").size()
        .sort_values(ascending=False).head(top_n).index.tolist()
    )
    
    if not top_jugadores:
        return
        
    goles_top = goles[goles["jugador"].isin(top_jugadores)].copy()
    goles_top["jugador_equipo"] = goles_top["jugador"] + " (" + goles_top["equipo"] + ")"
    
    # Contar goles por jugador y jornada
    daily = goles_top.groupby(["jugador_equipo", "jornada"]).size().reset_index(name="Goles")
    
    # Crear un grid completo de todas las jornadas para todos los jugadores top
    jornadas = sorted(goles["jornada"].dropna().unique())
    grid = pd.MultiIndex.from_product([daily["jugador_equipo"].unique(), jornadas], names=["jugador_equipo", "jornada"]).to_frame(index=False)
    
    # Unir y calcular suma acumulada
    merged = pd.merge(grid, daily, on=["jugador_equipo", "jornada"], how="left").fillna({"Goles": 0})
    merged = merged.sort_values(["jugador_equipo", "jornada"])
    merged["Goles Acumulados"] = merged.groupby("jugador_equipo")["Goles"].cumsum()
    
    fig = px.line(
        merged, x="jornada", y="Goles Acumulados", color="jugador_equipo",
        markers=True, template=_TEMPLATE,
        labels={"jornada": "Jornada", "Goles Acumulados": "Goles Totales", "jugador_equipo": "Jugador"}
    )
    
    fig.update_xaxes(type="category") 
    fig.update_yaxes(title=None, dtick=1)
    
    # We move the legend so it doesn't overlap lines/titles if the plot gets crowded 
    # and we ensure text isn't placed on the chart if text is not strictly needed.
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.15, font_size=11), margin=dict(t=60))
    st.plotly_chart(_style(fig), width="stretch")




def tiros_castigo_bar(eventos: pd.DataFrame, partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🛑 Tiros Castigo (Cometidos vs A Favor)</div>', unsafe_allow_html=True)
    if eventos.empty or partidos.empty:
        st.info("Sin datos para analizar Tiros Castigo.")
        return
        
    faltas = eventos[eventos["tipo_evento"] == "Falta"].copy()
    if faltas.empty:
        st.info("Sin datos de faltas.")
        return
        
    f_agg = faltas.groupby(["partido_id", "periodo", "equipo"]).size().reset_index(name="Faltas")
    f_agg["Tiros_Castigo_Cometidos"] = f_agg["Faltas"].apply(lambda x: max(0, x - 5))
    tc_df = f_agg[f_agg["Tiros_Castigo_Cometidos"] > 0]
    
    if tc_df.empty:
        st.info("Ningún equipo alcanzó el límite de 5 faltas por tiempo para cometer un Tiro Castigo.")
        return
        
    records = []
    for _, row in tc_df.iterrows():
        p_id = row["partido_id"]
        infractor = row["equipo"]
        tc = row["Tiros_Castigo_Cometidos"]
        
        partido = partidos[partidos["id"] == p_id]
        if not partido.empty:
            p = partido.iloc[0]
            victima = p["equipo_visitante"] if p["equipo_local"] == infractor else p["equipo_local"]
            
            records.append({"equipo": infractor, "Tipo": "Cometidos", "Cantidad": tc})
            records.append({"equipo": victima, "Tipo": "A Favor", "Cantidad": tc})
            
    df_tc = pd.DataFrame(records)
    if df_tc.empty:
        return
        
    df_grouped = df_tc.groupby(["equipo", "Tipo"], as_index=False).sum()
    df_grouped = df_grouped.sort_values(by="Cantidad", ascending=True)

    fig = px.bar(
        df_grouped, x="Cantidad", y="equipo", color="Tipo", orientation="h",
        barmode="group", color_discrete_map={"Cometidos": "#f85149", "A Favor": "#3fb950"},
        template=_TEMPLATE, text="Cantidad"
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.08, font_size=11))
    fig.update_xaxes(title="Tiros Castigo", dtick=1)
    fig.update_yaxes(title=" ")
    st.plotly_chart(_style(fig, height=max(300, len(df_grouped["equipo"].unique()) * 30)), width="stretch")

def tiros_castigo_scatter(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🎯 Faltas vs Tiros Castigos Cometidos</div>', unsafe_allow_html=True)
    if eventos.empty:
        st.info("Sin datos de eventos.")
        return
        
    faltas = eventos[eventos["tipo_evento"] == "Falta"].copy()
    if faltas.empty:
        st.info("Sin datos de faltas.")
        return

    f_agg = faltas.groupby(["partido_id", "periodo", "equipo"]).size().reset_index(name="Faltas")
    f_agg["Tiros_Castigo_Cometidos"] = f_agg["Faltas"].apply(lambda x: max(0, x - 5))
    
    totales = f_agg.groupby("equipo").agg(
        Total_Faltas=("Faltas", "sum"),
        Total_TC=("Tiros_Castigo_Cometidos", "sum")
    ).reset_index()
    
    totales["size"] = totales["Total_TC"] * 10 + 20
    
    fig = px.scatter(
        totales, x="Total_Faltas", y="Total_TC", text="equipo", size="size",
        color="equipo", template=_TEMPLATE, hover_data={"Total_Faltas": True, "Total_TC": True, "size": False},
        labels={"Total_Faltas": "Cantidad de Faltas Cometidas", "Total_TC": "Tiros Castigos Cometidos"}
    )
    
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(showlegend=False)
    fig.update_yaxes(dtick=1)
    
    st.plotly_chart(_style(fig), width="stretch")

