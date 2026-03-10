"""
Tablas interactivas: tabla disciplinaria y resultados de partidos.
"""
import streamlit as st
import pandas as pd


# ─── Tabla disciplinaria ──────────────────────────────────────────────────────

def disciplinary(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🟨 Tabla Disciplinaria por Equipo <span style="font-size:0.8rem; font-weight:normal; color:#8b949e;">(Falta=1, 🟨/🟦=2, 🔵=3, 🟥=4)</span></div>', unsafe_allow_html=True)

    if eventos.empty:
        st.info("Sin datos disciplinarios.")
        return

    disc = eventos.pivot_table(
        index="equipo",
        columns="tipo_evento",
        values="id",
        aggfunc="count",
        fill_value=0,
    ).reset_index()

    # Asegurar que todas las columnas disciplinarias existan
    for col in ["Falta", "Amarilla", "Roja", "Azul I", "Azul D"]:
        if col not in disc.columns:
            disc[col] = 0

    disc["Puntos disciplinarios"] = (
        disc.get("Falta", 0)    * 1 +
        disc.get("Amarilla", 0) * 2 +
        disc.get("Azul I", 0)   * 2 +
        disc.get("Azul D", 0)   * 3 +
        disc.get("Roja", 0)     * 4
    )
    disc = disc.sort_values("Puntos disciplinarios", ascending=False)

    cols_show = ["equipo"] + [
        c for c in ["Falta","Amarilla","Azul I","Azul D","Roja","Puntos disciplinarios"]
        if c in disc.columns
    ]
    disc_show = disc[cols_show].rename(columns={
        "equipo":   "Equipo",
        "Falta":    "Faltas",
        "Amarilla": "🟨 Amarillas",
        "Roja":     "🟥 Rojas",
        "Azul I":   "🟦 Azul Ind.",
        "Azul D":   "🔵 Azul Dir.",
    })

    max_pts = int(disc_show["Puntos disciplinarios"].max()) if len(disc_show) > 0 else 1

    st.dataframe(
        disc_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Puntos disciplinarios": st.column_config.ProgressColumn(
                "Puntos discipl.", format="%d", min_value=0, max_value=max_pts
            )
        },
    )


# ─── Resultados de partidos ───────────────────────────────────────────────────

def match_results(partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🏟️ Resultados de Partidos</div>', unsafe_allow_html=True)

    if partidos.empty:
        st.info("Sin partidos para los filtros seleccionados.")
        return

    df = partidos.copy()

    def _resultado(row):
        if row["goles_local"] > row["goles_visitante"]:  return "Local"
        if row["goles_local"] < row["goles_visitante"]:  return "Visitante"
        return "Empate"

    df["Resultado"] = df.apply(_resultado, axis=1)
    df["Marcador"]  = df["goles_local"].astype(str) + " - " + df["goles_visitante"].astype(str)

    final = (
        df.rename(columns={"jornada": "Jornada", "equipo_local": "Local", "equipo_visitante": "Visitante"})
        [["Jornada", "Local", "Marcador", "Visitante", "Resultado"]]
        .sort_values("Jornada")
    )

    st.dataframe(
        final,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Jornada":   st.column_config.NumberColumn("Jornada", format="%d"),
            "Resultado": st.column_config.TextColumn("Resultado"),
        },
    )


# ─── Tabla de Posiciones ──────────────────────────────────────────────────────

def league_standings(partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🏆 Tabla de Posiciones</div>', unsafe_allow_html=True)
    
    if partidos.empty:
        st.info("Sin partidos suficientes para armar la tabla de posiciones.")
        return
        
    stats = {}
    
    for _, row in partidos.iterrows():
        l_team = row["equipo_local"]
        v_team = row["equipo_visitante"]
        gl = row["goles_local"]
        gv = row["goles_visitante"]
        
        # Init teams if not exist
        if l_team not in stats: stats[l_team] = {"PJ":0, "G":0, "E":0, "P":0, "GF":0, "GC":0}
        if v_team not in stats: stats[v_team] = {"PJ":0, "G":0, "E":0, "P":0, "GF":0, "GC":0}
            
        # Update PJ and goals
        stats[l_team]["PJ"] += 1; stats[v_team]["PJ"] += 1
        stats[l_team]["GF"] += gl; stats[l_team]["GC"] += gv
        stats[v_team]["GF"] += gv; stats[v_team]["GC"] += gl
        
        # Update W/D/L
        if gl > gv:
            stats[l_team]["G"] += 1; stats[v_team]["P"] += 1
        elif gl < gv:
            stats[l_team]["P"] += 1; stats[v_team]["G"] += 1
        else:
            stats[l_team]["E"] += 1; stats[v_team]["E"] += 1
            
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(stats, orient="index").reset_index().rename(columns={"index": "Equipo"})
    if df.empty:
        return
        
    df["DIF"] = df["GF"] - df["GC"]
    df["PTS"] = df["G"] * 3 + df["E"]
    
    # Sort by PTS (desc), then DIF (desc), then GF (desc)
    df = df.sort_values(["PTS", "DIF", "GF"], ascending=[False, False, False]).reset_index(drop=True)
    df.index = df.index + 1  # For ranking
    
    st.dataframe(
        df,
        use_container_width=True,
    )


# ─── Ranking Elo ──────────────────────────────────────────────────────────────

def elo_ranking(partidos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">📈 Ranking Elo</div>', unsafe_allow_html=True)

    if partidos.empty:
        st.info("Sin partidos suficientes para armar el ranking Elo.")
        return

    import math

    # Asegurar orden cronológico
    if "fecha" in partidos.columns:
        df = partidos.sort_values("fecha")
    else:
        df = partidos.sort_values("jornada")

    elo_ratings = {}
    INITIAL_RATING = 1500
    K = 24

    for _, row in df.iterrows():
        l_team = row["equipo_local"]
        v_team = row["equipo_visitante"]
        gl = row["goles_local"]
        gv = row["goles_visitante"]

        if pd.isna(l_team) or pd.isna(v_team) or pd.isna(gl) or pd.isna(gv):
            continue

        if l_team not in elo_ratings: elo_ratings[l_team] = INITIAL_RATING
        if v_team not in elo_ratings: elo_ratings[v_team] = INITIAL_RATING

        r_local = elo_ratings[l_team]
        r_visit = elo_ratings[v_team]

        # Probabilidad esperada (sin localía)
        exp_local = 1 / (1 + 10 ** ((r_visit - r_local) / 400))
        exp_visit = 1 / (1 + 10 ** ((r_local - r_visit) / 400))

        # Puntos obtenidos (0.5 para empate)
        if gl > gv:
            pts_local, pts_visit = 1, 0
        elif gl < gv:
            pts_local, pts_visit = 0, 1
        else:
            pts_local, pts_visit = 0.5, 0.5

        # Ajuste suave por diferencia de gol logarítmico (aseguramos no tener log(0))
        dif = abs(gl - gv)
        G = math.log(dif) + 1 if dif > 0 else 1.0

        change_local = K * G * (pts_local - exp_local)
        change_visit = K * G * (pts_visit - exp_visit)

        elo_ratings[l_team] += change_local
        elo_ratings[v_team] += change_visit

    # Convertir a DataFrame
    elo_df = pd.DataFrame(list(elo_ratings.items()), columns=["Equipo", "Elo"]).sort_values("Elo", ascending=False).reset_index(drop=True)
    elo_df.index = elo_df.index + 1
    
    # Formatear
    elo_df["Elo"] = elo_df["Elo"].round().astype(int)

    st.dataframe(
        elo_df,
        use_container_width=True,
    )

