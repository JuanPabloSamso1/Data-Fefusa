"""Agregaciones puras para el dashboard FEFUSA."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

GOAL_EVENTS = {"Gol", "Penal Gol"}
DISCIPLINE_EVENTS = {"Falta", "Amarilla", "Azul I", "Azul D", "Roja"}
CARD_EVENTS = {"Amarilla", "Azul I", "Azul D", "Roja"}
MOMENTUM_LABELS = ["0-5'", "5-10'", "10-15'", "15-20'", "20-25'", "25-30'", "30-35'", "35-40'"]
FIRST_HALF_PERIODS = {"1", "1T", "FIRST_HALF", "FIRSTHALF"}
SECOND_HALF_PERIODS = {"2", "2T", "SECOND_HALF", "SECONDHALF"}
IPD_WEIGHTS = {
    "Falta": 0.2,
    "Amarilla": 1.0,
    "Azul I": 2.0,
    "Azul D": 3.0,
    "Roja": 3.0,
}


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _clean_text(series: pd.Series, fallback: str) -> pd.Series:
    return (
        series.fillna(fallback)
        .astype(str)
        .replace({"nan": fallback, "None": fallback, "": fallback})
    )


def _sort_key_jornada(value) -> tuple[int, str]:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return (int(digits), text) if digits else (10**9, text)


def minute_to_bucket(value) -> str:
    """Normaliza minuto absoluto 0-40 en 8 bloques de 5 minutos."""
    try:
        minute = int(float(value))
    except (TypeError, ValueError):
        minute = 0

    minute = max(0, min(minute, 40))
    idx = min(minute // 5, len(MOMENTUM_LABELS) - 1)
    return MOMENTUM_LABELS[idx]


def add_momentum_bucket(df: pd.DataFrame, minute_col: str = "minuto", output_col: str = "Bloque") -> pd.DataFrame:
    out = df.copy()
    if minute_col not in out.columns:
        out[output_col] = pd.Series(index=out.index, dtype=object)
        return out
    out[output_col] = out[minute_col].apply(minute_to_bucket)
    return out


def _normalize_period(value) -> str:
    raw = str(value).strip().upper()
    if raw in {"", "NAN", "NONE"}:
        return ""
    if raw in FIRST_HALF_PERIODS:
        return "1T"
    if raw in SECOND_HALF_PERIODS:
        return "2T"
    return raw


def is_regular_period(value) -> bool:
    normalized = _normalize_period(value)
    return normalized in {"", "1T", "2T"}


def period_label(value) -> str:
    normalized = _normalize_period(value)
    if normalized in {"1T", "2T"}:
        return normalized
    if normalized == "5":
        return "Penales"
    return normalized or "Sin periodo"


def goal_events(eventos: pd.DataFrame, include_non_regular_periods: bool = False) -> pd.DataFrame:
    if eventos.empty or "tipo_evento" not in eventos.columns:
        return _empty(list(eventos.columns))
    goals = eventos[eventos["tipo_evento"].isin(GOAL_EVENTS)].copy()
    if goals.empty or include_non_regular_periods or "periodo" not in goals.columns:
        return goals
    return goals[goals["periodo"].apply(is_regular_period)].copy()


def discipline_events(eventos: pd.DataFrame) -> pd.DataFrame:
    if eventos.empty or "tipo_evento" not in eventos.columns:
        return _empty(list(eventos.columns))
    return eventos[eventos["tipo_evento"].isin(DISCIPLINE_EVENTS)].copy()


def matches_long(partidos: pd.DataFrame) -> pd.DataFrame:
    columns = ["partido_id", "team", "rival", "jornada", "fecha", "gf", "gc", "result", "pts", "marcador"]
    if partidos.empty:
        return _empty(columns)

    df = partidos.copy()
    needed = {"id", "equipo_local", "equipo_visitante", "goles_local", "goles_visitante"}
    if not needed.issubset(df.columns):
        return _empty(columns)

    df["goles_local"] = _safe_numeric(df["goles_local"]).astype(int)
    df["goles_visitante"] = _safe_numeric(df["goles_visitante"]).astype(int)
    df["jornada_sort"] = df["jornada"].apply(_sort_key_jornada) if "jornada" in df.columns else None
    df["fecha_sort"] = _coerce_datetime(df["fecha"]) if "fecha" in df.columns else pd.NaT

    home = pd.DataFrame(
        {
            "partido_id": df["id"],
            "team": _clean_text(df["equipo_local"], "Sin equipo"),
            "rival": _clean_text(df["equipo_visitante"], "Sin rival"),
            "jornada": df["jornada"] if "jornada" in df.columns else None,
            "fecha": df["fecha_sort"],
            "gf": df["goles_local"],
            "gc": df["goles_visitante"],
        }
    )
    away = pd.DataFrame(
        {
            "partido_id": df["id"],
            "team": _clean_text(df["equipo_visitante"], "Sin equipo"),
            "rival": _clean_text(df["equipo_local"], "Sin rival"),
            "jornada": df["jornada"] if "jornada" in df.columns else None,
            "fecha": df["fecha_sort"],
            "gf": df["goles_visitante"],
            "gc": df["goles_local"],
        }
    )

    long_df = pd.concat([home, away], ignore_index=True)
    long_df["result"] = long_df.apply(
        lambda row: "G" if row["gf"] > row["gc"] else "P" if row["gf"] < row["gc"] else "E",
        axis=1,
    )
    long_df["pts"] = long_df["result"].map({"G": 3, "E": 1, "P": 0}).astype(int)
    long_df["marcador"] = long_df["gf"].astype(str) + " - " + long_df["gc"].astype(str)
    return long_df[columns]


def build_standings(partidos: pd.DataFrame) -> pd.DataFrame:
    long_df = matches_long(partidos)
    if long_df.empty:
        return _empty(["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DIF", "PTS"])

    summary = (
        long_df.groupby("team", as_index=False)
        .agg(
            PJ=("partido_id", "nunique"),
            G=("result", lambda s: int((s == "G").sum())),
            E=("result", lambda s: int((s == "E").sum())),
            P=("result", lambda s: int((s == "P").sum())),
            GF=("gf", "sum"),
            GC=("gc", "sum"),
            PTS=("pts", "sum"),
        )
        .rename(columns={"team": "Equipo"})
    )
    summary["DIF"] = summary["GF"] - summary["GC"]
    summary = summary.sort_values(["PTS", "DIF", "GF", "Equipo"], ascending=[False, False, False, True]).reset_index(drop=True)
    summary.insert(0, "Pos", summary.index + 1)
    return summary[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DIF", "PTS"]]


def build_egr_table(partidos: pd.DataFrame) -> pd.DataFrame:
    long_df = matches_long(partidos)
    if long_df.empty:
        return _empty(["Equipo", "PJ", "GF", "GC", "GF/PJ", "GC/PJ", "EGR"])

    league_avg = long_df["gf"].mean()
    league_avg = league_avg if league_avg > 0 else 1.0

    summary = (
        long_df.groupby("team", as_index=False)
        .agg(PJ=("partido_id", "nunique"), GF=("gf", "sum"), GC=("gc", "sum"))
        .rename(columns={"team": "Equipo"})
    )
    summary["GF/PJ"] = (summary["GF"] / summary["PJ"]).round(2)
    summary["GC/PJ"] = (summary["GC"] / summary["PJ"]).round(2)
    summary["EGR"] = ((summary["GF"] / summary["PJ"]) / league_avg * 100).round(1)
    return summary.sort_values(["EGR", "GF", "Equipo"], ascending=[False, False, True]).reset_index(drop=True)


def build_current_streaks(partidos: pd.DataFrame) -> pd.DataFrame:
    long_df = matches_long(partidos)
    if long_df.empty:
        return _empty(["Equipo", "Racha", "Partidos", "Detalle"])

    long_df = long_df.copy()
    long_df["jornada_sort"] = long_df["jornada"].apply(_sort_key_jornada)
    long_df = long_df.sort_values(["fecha", "jornada_sort", "partido_id"], ascending=[True, True, True])
    rows = []
    for team, team_df in long_df.groupby("team"):
        results = team_df["result"].tolist()
        latest = results[-1]
        streak = 0
        for result in reversed(results):
            if result != latest:
                break
            streak += 1
        rows.append(
            {
                "Equipo": team,
                "Racha": f"{latest}{streak}",
                "Partidos": int(team_df["partido_id"].nunique()),
                "Detalle": {"G": "Victorias", "E": "Empates", "P": "Derrotas"}[latest],
            }
        )
    return pd.DataFrame(rows).sort_values(["Racha", "Equipo"], ascending=[False, True]).reset_index(drop=True)


def build_global_summary(eventos: pd.DataFrame, partidos: pd.DataFrame) -> dict[str, object]:
    standings = build_standings(partidos)
    egr = build_egr_table(partidos)
    total_matches = int(partidos["id"].nunique()) if not partidos.empty and "id" in partidos.columns else 0
    total_goals = int(goal_events(eventos).shape[0])
    avg_goals = round(total_goals / total_matches, 2) if total_matches else 0.0

    cleanest_team = "Sin datos"
    if not standings.empty:
        standings = standings.copy()
        standings["GC/PJ"] = (standings["GC"] / standings["PJ"]).round(2)
        cleanest_team = standings.sort_values(["GC/PJ", "Equipo"], ascending=[True, True]).iloc[0]["Equipo"]

    top_egr_team = egr.iloc[0]["Equipo"] if not egr.empty else "Sin datos"

    return {
        "partidos": total_matches,
        "goles": total_goals,
        "goles_por_partido": avg_goals,
        "equipo_menos_goleado": cleanest_team,
        "mejor_eficiencia": top_egr_team,
    }


def _discipline_template(label_col: str) -> pd.DataFrame:
    return _empty([label_col, "PJ", "Faltas", "Amarillas", "Azul I", "Azul D", "Rojas", "Tarjetas", "IPD", "Riesgo"])


def _risk_label(ipd: float) -> str:
    if ipd >= 3.0:
        return "Alto"
    if ipd >= 1.5:
        return "Medio"
    return "Bajo"


def build_team_discipline(eventos: pd.DataFrame, partidos: pd.DataFrame) -> pd.DataFrame:
    long_df = matches_long(partidos)
    if long_df.empty:
        return _discipline_template("Equipo")

    base = discipline_events(eventos)
    if base.empty:
        out = long_df.groupby("team", as_index=False).agg(PJ=("partido_id", "nunique")).rename(columns={"team": "Equipo"})
        out["Faltas"] = 0
        out["Amarillas"] = 0
        out["Azul I"] = 0
        out["Azul D"] = 0
        out["Rojas"] = 0
        out["Tarjetas"] = 0
        out["IPD"] = 0.0
        out["Riesgo"] = "Bajo"
        return out

    disc = base.copy()
    disc["equipo"] = _clean_text(disc["equipo"], "Sin equipo")
    summary = (
        disc.groupby("equipo", as_index=False)
        .agg(
            Faltas=("tipo_evento", lambda s: int((s == "Falta").sum())),
            Amarillas=("tipo_evento", lambda s: int((s == "Amarilla").sum())),
            **{
                "Azul I": ("tipo_evento", lambda s: int((s == "Azul I").sum())),
                "Azul D": ("tipo_evento", lambda s: int((s == "Azul D").sum())),
                "Rojas": ("tipo_evento", lambda s: int((s == "Roja").sum())),
            },
        )
        .rename(columns={"equipo": "Equipo"})
    )
    pj = long_df.groupby("team", as_index=False).agg(PJ=("partido_id", "nunique")).rename(columns={"team": "Equipo"})
    out = pj.merge(summary, on="Equipo", how="left").fillna(0)
    out["Tarjetas"] = out["Amarillas"] + out["Azul I"] + out["Azul D"] + out["Rojas"]
    out["IPD"] = (
        out["Amarillas"] * IPD_WEIGHTS["Amarilla"]
        + out["Azul I"] * IPD_WEIGHTS["Azul I"]
        + out["Azul D"] * IPD_WEIGHTS["Azul D"]
        + out["Rojas"] * IPD_WEIGHTS["Roja"]
        + out["Faltas"] * IPD_WEIGHTS["Falta"]
    ) / out["PJ"].replace(0, 1)
    out["IPD"] = out["IPD"].round(2)
    out["Riesgo"] = out["IPD"].apply(_risk_label)
    return out.sort_values(["IPD", "Tarjetas", "Equipo"], ascending=[False, False, True]).reset_index(drop=True)


def build_player_catalog(eventos: pd.DataFrame) -> pd.DataFrame:
    if eventos.empty:
        return _empty(["player_key", "Jugador", "Equipo", "label", "persona_id"])

    base = eventos.copy()
    base["jugador"] = _clean_text(base.get("jugador", pd.Series(dtype=object)), "Sin jugador")
    base["equipo"] = _clean_text(base.get("equipo", pd.Series(dtype=object)), "Sin equipo")
    if "persona_id" not in base.columns:
        base["persona_id"] = None

    base = base[base["jugador"] != "Sin jugador"].copy()
    if base.empty:
        return _empty(["player_key", "Jugador", "Equipo", "label", "persona_id"])

    base["player_key"] = base.apply(
        lambda row: row["persona_id"] if pd.notna(row["persona_id"]) else f"{row['jugador']}::{row['equipo']}",
        axis=1,
    )
    catalog = (
        base.groupby("player_key", as_index=False)
        .agg(
            Jugador=("jugador", "first"),
            Equipo=("equipo", "first"),
            persona_id=("persona_id", "first"),
        )
        .sort_values(["Jugador", "Equipo"], ascending=[True, True])
        .reset_index(drop=True)
    )
    catalog["label"] = catalog["Jugador"] + " · " + catalog["Equipo"]
    return catalog


def filter_events_for_player(eventos: pd.DataFrame, player_key: str | None) -> pd.DataFrame:
    if not player_key or eventos.empty:
        return _empty(list(eventos.columns))

    if "persona_id" in eventos.columns and player_key in set(eventos["persona_id"].dropna().astype(str)):
        return eventos[eventos["persona_id"].astype(str) == str(player_key)].copy()

    if "::" in str(player_key):
        jugador, equipo = str(player_key).split("::", 1)
        return eventos[(eventos["jugador"] == jugador) & (eventos["equipo"] == equipo)].copy()

    return _empty(list(eventos.columns))


def build_player_discipline(eventos: pd.DataFrame) -> pd.DataFrame:
    catalog = build_player_catalog(eventos)
    if catalog.empty:
        return _discipline_template("Jugador")

    rows = []
    for _, player in catalog.iterrows():
        player_events = filter_events_for_player(eventos, str(player["player_key"]))
        pj = int(player_events["partido_id"].nunique()) if "partido_id" in player_events.columns else 0
        foul_count = int((player_events["tipo_evento"] == "Falta").sum())
        yellow_count = int((player_events["tipo_evento"] == "Amarilla").sum())
        blue_i_count = int((player_events["tipo_evento"] == "Azul I").sum())
        blue_d_count = int((player_events["tipo_evento"] == "Azul D").sum())
        red_count = int((player_events["tipo_evento"] == "Roja").sum())
        ipd = (
            yellow_count * IPD_WEIGHTS["Amarilla"]
            + blue_i_count * IPD_WEIGHTS["Azul I"]
            + blue_d_count * IPD_WEIGHTS["Azul D"]
            + red_count * IPD_WEIGHTS["Roja"]
            + foul_count * IPD_WEIGHTS["Falta"]
        ) / (pj or 1)
        rows.append(
            {
                "Jugador": player["Jugador"],
                "Equipo": player["Equipo"],
                "PJ": pj,
                "Faltas": foul_count,
                "Amarillas": yellow_count,
                "Azul I": blue_i_count,
                "Azul D": blue_d_count,
                "Rojas": red_count,
                "Tarjetas": yellow_count + blue_i_count + blue_d_count + red_count,
                "IPD": round(ipd, 2),
                "Riesgo": _risk_label(ipd),
            }
        )
    return pd.DataFrame(rows).sort_values(["IPD", "Tarjetas", "Jugador"], ascending=[False, False, True]).reset_index(drop=True)


def build_goal_momentum(eventos: pd.DataFrame, team: str | None = None, partido_id: str | None = None) -> pd.DataFrame:
    goals = goal_events(eventos)
    if goals.empty:
        return pd.DataFrame({"Bloque": MOMENTUM_LABELS, "Goles": [0] * len(MOMENTUM_LABELS)})

    if team:
        goals = goals[goals["equipo"] == team]
    if partido_id:
        goals = goals[goals["partido_id"] == partido_id]

    goals = add_momentum_bucket(goals)
    data = goals.groupby("Bloque", as_index=False).size().rename(columns={"size": "Goles"})
    template = pd.DataFrame({"Bloque": MOMENTUM_LABELS})
    return template.merge(data, on="Bloque", how="left").fillna(0)


def build_match_momentum(eventos: pd.DataFrame, partido_id: str) -> pd.DataFrame:
    goals = goal_events(eventos)
    if goals.empty:
        return _empty(["Bloque", "Equipo", "Goles"])

    goals = goals[goals["partido_id"] == partido_id].copy()
    if goals.empty:
        return _empty(["Bloque", "Equipo", "Goles"])

    goals["equipo"] = _clean_text(goals["equipo"], "Sin equipo")
    goals = add_momentum_bucket(goals)
    data = goals.groupby(["Bloque", "equipo"], as_index=False).size().rename(columns={"equipo": "Equipo", "size": "Goles"})

    teams = data["Equipo"].dropna().unique().tolist()
    template = pd.MultiIndex.from_product([MOMENTUM_LABELS, teams], names=["Bloque", "Equipo"]).to_frame(index=False)
    return template.merge(data, on=["Bloque", "Equipo"], how="left").fillna(0)


def build_team_goal_balance(eventos: pd.DataFrame, partidos: pd.DataFrame, team: str) -> pd.DataFrame:
    match_ids = set(matches_long(partidos).query("team == @team")["partido_id"].tolist())
    if not match_ids:
        return _empty(["Bloque", "Tipo", "Goles"])

    goals = goal_events(eventos)
    goals = goals[goals["partido_id"].isin(match_ids)].copy()
    if goals.empty:
        return _empty(["Bloque", "Tipo", "Goles"])

    goals["Tipo"] = goals["equipo"].apply(lambda current: "A favor" if current == team else "En contra")
    goals = add_momentum_bucket(goals)
    data = goals.groupby(["Bloque", "Tipo"], as_index=False).size().rename(columns={"size": "Goles"})
    template = pd.MultiIndex.from_product([MOMENTUM_LABELS, ["A favor", "En contra"]], names=["Bloque", "Tipo"]).to_frame(index=False)
    return template.merge(data, on=["Bloque", "Tipo"], how="left").fillna(0)


def build_team_profile(eventos: pd.DataFrame, partidos: pd.DataFrame, team: str) -> dict[str, object]:
    long_df = matches_long(partidos)
    team_matches = long_df[long_df["team"] == team].copy()
    if team_matches.empty:
        return {}

    standings = build_standings(partidos)
    egr = build_egr_table(partidos)
    discipline = build_team_discipline(eventos, partidos)

    row = standings[standings["Equipo"] == team].iloc[0]
    egr_row = egr[egr["Equipo"] == team].iloc[0] if not egr[egr["Equipo"] == team].empty else None
    disc_row = discipline[discipline["Equipo"] == team].iloc[0] if not discipline[discipline["Equipo"] == team].empty else None

    team_matches = team_matches.copy()
    team_matches["jornada_sort"] = team_matches["jornada"].apply(_sort_key_jornada)
    team_matches = team_matches.sort_values(["fecha", "jornada_sort"], ascending=[False, False])
    last_five = team_matches.head(5).copy()
    last_five["Resultado"] = last_five["result"].map({"G": "Victoria", "E": "Empate", "P": "Derrota"})
    last_five["Detalle"] = last_five["team"] + " " + last_five["marcador"] + " " + last_five["rival"]
    per_match = pd.DataFrame(
        [
            {"Indicador": "GF por partido", "Valor": round(float(row["GF"] / row["PJ"]), 2)},
            {"Indicador": "GC por partido", "Valor": round(float(row["GC"] / row["PJ"]), 2)},
            {"Indicador": "PTS por partido", "Valor": round(float(row["PTS"] / row["PJ"]), 2)},
            {"Indicador": "Diferencia por partido", "Valor": round(float(row["DIF"] / row["PJ"]), 2)},
        ]
    )

    return {
        "summary": {
            "pj": int(row["PJ"]),
            "pg": int(row["G"]),
            "pe": int(row["E"]),
            "pp": int(row["P"]),
            "pts": int(row["PTS"]),
            "gf": int(row["GF"]),
            "gc": int(row["GC"]),
            "dif": int(row["DIF"]),
            "egr": float(egr_row["EGR"]) if egr_row is not None else 0.0,
            "ipd": float(disc_row["IPD"]) if disc_row is not None else 0.0,
        },
        "last_five": last_five[["jornada", "Resultado", "Detalle"]].rename(columns={"jornada": "Jornada"}),
        "per_match": per_match,
        "momentum": build_team_goal_balance(eventos, partidos, team),
    }


def build_player_goal_timeline(eventos: pd.DataFrame, player_key: str) -> pd.DataFrame:
    player_events = filter_events_for_player(eventos, player_key)
    if player_events.empty:
        return _empty(["Jornada", "Partido", "Goles"])

    base = (
        player_events.groupby(["partido_id", "jornada"], as_index=False)
        .size()
        .rename(columns={"size": "Eventos"})
    )
    goals = (
        goal_events(player_events)
        .groupby(["partido_id", "jornada"], as_index=False)
        .size()
        .rename(columns={"size": "Goles"})
    )
    out = base.merge(goals, on=["partido_id", "jornada"], how="left").fillna(0)
    out["Goles"] = out["Goles"].astype(int)
    out["Jornada_sort"] = out["jornada"].apply(_sort_key_jornada)
    out = out.sort_values(["Jornada_sort", "partido_id"]).reset_index(drop=True)
    out["Partido"] = out.index + 1
    return out.rename(columns={"jornada": "Jornada"})[["Jornada", "Partido", "Goles"]]


def build_player_profile(eventos: pd.DataFrame, player_key: str) -> dict[str, object]:
    player_events = filter_events_for_player(eventos, player_key)
    if player_events.empty:
        return {}

    player_events = player_events.copy()
    player_events["jugador"] = _clean_text(player_events["jugador"], "Sin jugador")
    player_events["equipo"] = _clean_text(player_events["equipo"], "Sin equipo")

    descriptor = player_events.iloc[0]
    matches = int(player_events["partido_id"].nunique()) if "partido_id" in player_events.columns else 0
    goals_count = int(goal_events(player_events).shape[0])
    foul_count = int((player_events["tipo_evento"] == "Falta").sum())
    yellow_count = int((player_events["tipo_evento"] == "Amarilla").sum())
    blue_i_count = int((player_events["tipo_evento"] == "Azul I").sum())
    blue_d_count = int((player_events["tipo_evento"] == "Azul D").sum())
    red_count = int((player_events["tipo_evento"] == "Roja").sum())

    ipd = (
        yellow_count * IPD_WEIGHTS["Amarilla"]
        + blue_i_count * IPD_WEIGHTS["Azul I"]
        + blue_d_count * IPD_WEIGHTS["Azul D"]
        + red_count * IPD_WEIGHTS["Roja"]
        + foul_count * IPD_WEIGHTS["Falta"]
    ) / (matches or 1)

    goals_by_block = build_goal_momentum(player_events)
    return {
        "label": f"{descriptor['jugador']} · {descriptor['equipo']}",
        "summary": {
            "goles": goals_count,
            "partidos": matches,
            "goles_por_partido": round(goals_count / matches, 2) if matches else 0.0,
            "faltas": foul_count,
            "amarillas": yellow_count,
            "azul_i": blue_i_count,
            "azul_d": blue_d_count,
            "rojas": red_count,
            "ipd": round(ipd, 2),
        },
        "timeline": build_player_goal_timeline(player_events, player_key),
        "momentum": goals_by_block,
    }


def build_match_selector(partidos: pd.DataFrame) -> pd.DataFrame:
    if partidos.empty:
        return _empty(["id", "label", "equipo_local", "equipo_visitante", "jornada", "fecha"])

    df = partidos.copy()
    df["fecha_sort"] = _coerce_datetime(df["fecha"]) if "fecha" in df.columns else pd.NaT
    df["goles_local"] = _safe_numeric(df["goles_local"]).astype(int)
    df["goles_visitante"] = _safe_numeric(df["goles_visitante"]).astype(int)
    if "jornada" in df.columns:
        df["jornada_sort"] = df["jornada"].apply(_sort_key_jornada)
    else:
        df["jornada"] = None
        df["jornada_sort"] = [(10**9, "")] * len(df)
    df["label"] = df.apply(
        lambda row: (
            f"J{row['jornada']} · {row['equipo_local']} {row['goles_local']}-{row['goles_visitante']} {row['equipo_visitante']}"
            if pd.notna(row.get("jornada"))
            else f"{row['equipo_local']} {row['goles_local']}-{row['goles_visitante']} {row['equipo_visitante']}"
        ),
        axis=1,
    )
    df = df.sort_values(["fecha_sort", "jornada_sort", "id"], ascending=[False, False, True]).reset_index(drop=True)
    return df[["id", "label", "equipo_local", "equipo_visitante", "jornada", "fecha_sort"]].rename(columns={"fecha_sort": "fecha"})


def build_match_dataset(eventos: pd.DataFrame, partidos: pd.DataFrame, partido_id: str) -> dict[str, object]:
    if not partido_id:
        return {}

    match_rows = partidos[partidos["id"] == partido_id]
    if match_rows.empty:
        return {}

    match = match_rows.iloc[0]
    match_events = eventos[eventos["partido_id"] == partido_id].copy()
    match_events = match_events.sort_values(["minuto", "segundo", "id"], ascending=[True, True, True])

    all_goals = goal_events(match_events, include_non_regular_periods=True)
    goals = goal_events(match_events)
    if not goals.empty:
        goals["Periodo"] = goals["periodo"].apply(period_label)
        goals["Equipo"] = _clean_text(goals["equipo"], "Sin equipo")
        period_summary = (
            goals.groupby(["Periodo", "Equipo"], as_index=False)
            .size()
            .rename(columns={"size": "Goles"})
        )
    else:
        period_summary = _empty(["Periodo", "Equipo", "Goles"])

    return {
        "match": {
            "id": match["id"],
            "local": match["equipo_local"],
            "visitante": match["equipo_visitante"],
            "goles_local": int(match["goles_local"]),
            "goles_visitante": int(match["goles_visitante"]),
            "jornada": match["jornada"],
            "fecha": match.get("fecha"),
        },
        "events": match_events,
        "period_summary": period_summary,
        "momentum": build_match_momentum(match_events, partido_id),
        "non_regular_goal_events": max(0, int(all_goals.shape[0] - goals.shape[0])),
    }


def build_discipline_timeline(eventos: pd.DataFrame) -> pd.DataFrame:
    disc = discipline_events(eventos)
    if disc.empty:
        return _empty(["Bloque", "tipo_evento", "Cantidad"])

    disc = add_momentum_bucket(disc)
    data = disc.groupby(["Bloque", "tipo_evento"], as_index=False).size().rename(columns={"size": "Cantidad"})
    return data


def build_player_comparison(eventos: pd.DataFrame, jugador_a: str, jugador_b: str) -> dict[str, object]:
    profile_a = build_player_profile(eventos, jugador_a)
    profile_b = build_player_profile(eventos, jugador_b)
    if not profile_a or not profile_b:
        return {}

    raw_metrics = [
        ("Goles", profile_a["summary"]["goles"], profile_b["summary"]["goles"], False),
        ("Partidos", profile_a["summary"]["partidos"], profile_b["summary"]["partidos"], False),
        ("Gol/Partido", profile_a["summary"]["goles_por_partido"], profile_b["summary"]["goles_por_partido"], False),
        ("IPD", profile_a["summary"]["ipd"], profile_b["summary"]["ipd"], True),
        ("Faltas", profile_a["summary"]["faltas"], profile_b["summary"]["faltas"], True),
    ]

    comparison_rows = []
    radar_rows = []
    for metric, value_a, value_b, invert in raw_metrics:
        comparison_rows.append({"Metrica": metric, profile_a["label"]: value_a, profile_b["label"]: value_b})
        max_value = max(float(value_a), float(value_b), 1.0)
        if invert:
            radar_a = 1 - (float(value_a) / max_value)
            radar_b = 1 - (float(value_b) / max_value)
        else:
            radar_a = float(value_a) / max_value
            radar_b = float(value_b) / max_value
        radar_rows.append({"Metrica": metric, "A": round(max(radar_a, 0.0), 3), "B": round(max(radar_b, 0.0), 3)})

    return {
        "label_a": profile_a["label"],
        "label_b": profile_b["label"],
        "table": pd.DataFrame(comparison_rows),
        "radar": pd.DataFrame(radar_rows),
    }


def format_last_updated(ts: datetime | pd.Timestamp | None) -> str:
    if ts is None or pd.isna(ts):
        return "Sin datos"
    if isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    return ts.strftime("%d/%m/%Y %H:%M")
