"""
Tablas interactivas: tabla disciplinaria y resultados de partidos.
"""
import streamlit as st
import pandas as pd


# ─── Tabla disciplinaria ──────────────────────────────────────────────────────

def disciplinary(eventos: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🟨 Tabla Disciplinaria por Equipo <span style="font-size:0.8rem; font-weight:normal; color:#8b949e;">(🟨/🟦=1pt, 🔵=2pts, 🟥=3pts)</span></div>', unsafe_allow_html=True)

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
        disc.get("Amarilla", 0) * 1 +
        disc.get("Roja", 0)     * 3 +
        disc.get("Azul I", 0)  * 1 +
        disc.get("Azul D", 0)  * 2
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
