"""Pipeline predictivo simple, robusto y explicable para el dashboard.

Enfoque:
- Ratings ofensivo/defensivo por equipo (a partir de GF/GC por partido).
- Goles esperados con ajuste multiplicativo (ataque propio x defensa rival x media liga).
- Probabilidades de resultado vía Poisson independiente.
- Proyección de tabla por Monte Carlo de una fecha sintética.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Tuple

import numpy as np
import pandas as pd


@dataclass
class TeamStrength:
    team: str
    pj: int
    gf_pg: float
    gc_pg: float
    atk: float
    deff: float


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def prepare_matches(partidos: pd.DataFrame) -> pd.DataFrame:
    if partidos.empty:
        return pd.DataFrame(columns=["equipo_local", "equipo_visitante", "goles_local", "goles_visitante", "jornada"])

    df = partidos.copy()
    needed = ["equipo_local", "equipo_visitante", "goles_local", "goles_visitante"]
    for c in needed:
        if c not in df.columns:
            return pd.DataFrame(columns=needed + ["jornada"])

    df = df.dropna(subset=["equipo_local", "equipo_visitante"])
    df["goles_local"] = _safe_numeric(df["goles_local"]).astype(int)
    df["goles_visitante"] = _safe_numeric(df["goles_visitante"]).astype(int)
    if "jornada" not in df.columns:
        df["jornada"] = 0
    return df


def build_team_strengths(partidos: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    df = prepare_matches(partidos)
    if df.empty:
        return pd.DataFrame(columns=["team", "pj", "gf_pg", "gc_pg", "atk", "deff"]), 1.0

    home = pd.DataFrame(
        {
            "team": df["equipo_local"],
            "gf": df["goles_local"],
            "gc": df["goles_visitante"],
        }
    )
    away = pd.DataFrame(
        {
            "team": df["equipo_visitante"],
            "gf": df["goles_visitante"],
            "gc": df["goles_local"],
        }
    )

    long = pd.concat([home, away], ignore_index=True)
    agg = long.groupby("team", as_index=False).agg(PJ=("gf", "count"), GF=("gf", "sum"), GC=("gc", "sum"))

    league_avg_goals = max(long["gf"].mean(), 0.2)
    agg["gf_pg"] = agg["GF"] / agg["PJ"]
    agg["gc_pg"] = agg["GC"] / agg["PJ"]
    agg["atk"] = (agg["gf_pg"] / league_avg_goals).clip(lower=0.3, upper=3.0)
    agg["deff"] = (agg["gc_pg"] / league_avg_goals).clip(lower=0.3, upper=3.0)

    return agg[["team", "PJ", "gf_pg", "gc_pg", "atk", "deff"]], league_avg_goals


def _poisson_pmf(k: int, lam: float) -> float:
    lam = max(lam, 0.01)
    return math.exp(-lam) * (lam**k) / math.factorial(k)


def outcome_probabilities(xg_a: float, xg_b: float, max_goals: int = 10) -> Dict[str, float]:
    p_a = [_poisson_pmf(i, xg_a) for i in range(max_goals + 1)]
    p_b = [_poisson_pmf(i, xg_b) for i in range(max_goals + 1)]

    win_a = draw = win_b = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = p_a[i] * p_b[j]
            if i > j:
                win_a += p
            elif i == j:
                draw += p
            else:
                win_b += p

    total = win_a + draw + win_b
    if total <= 0:
        return {"win_a": 1 / 3, "draw": 1 / 3, "win_b": 1 / 3}

    return {"win_a": win_a / total, "draw": draw / total, "win_b": win_b / total}


def predict_match(partidos: pd.DataFrame, team_a: str, team_b: str) -> Dict:
    strengths, league_avg = build_team_strengths(partidos)
    if strengths.empty or team_a not in strengths["team"].values or team_b not in strengths["team"].values:
        return {
            "xg_a": 1.0,
            "xg_b": 1.0,
            "xg_total": 2.0,
            "probs": {"win_a": 1 / 3, "draw": 1 / 3, "win_b": 1 / 3},
            "quality": "baja",
            "details": "Datos insuficientes para estimación robusta.",
        }

    sa = strengths.loc[strengths["team"] == team_a].iloc[0]
    sb = strengths.loc[strengths["team"] == team_b].iloc[0]

    xg_a = float(np.clip(league_avg * sa["atk"] * sb["deff"], 0.2, 8.0))
    xg_b = float(np.clip(league_avg * sb["atk"] * sa["deff"], 0.2, 8.0))
    probs = outcome_probabilities(xg_a, xg_b)

    pj_min = int(min(sa["PJ"], sb["PJ"]))
    quality = "alta" if pj_min >= 8 else "media" if pj_min >= 4 else "baja"

    return {
        "xg_a": round(xg_a, 2),
        "xg_b": round(xg_b, 2),
        "xg_total": round(xg_a + xg_b, 2),
        "probs": probs,
        "quality": quality,
        "details": f"Muestra mínima por equipo: {pj_min} partidos.",
        "strengths": strengths,
    }


def current_table(partidos: pd.DataFrame) -> pd.DataFrame:
    df = prepare_matches(partidos)
    if df.empty:
        return pd.DataFrame(columns=["Equipo", "PJ", "G", "E", "P", "GF", "GC", "DIF", "PTS"])

    stats = {}
    for _, row in df.iterrows():
        l_team = row["equipo_local"]
        v_team = row["equipo_visitante"]
        gl = int(row["goles_local"])
        gv = int(row["goles_visitante"])

        for team in [l_team, v_team]:
            if team not in stats:
                stats[team] = {"PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0}

        stats[l_team]["PJ"] += 1
        stats[v_team]["PJ"] += 1
        stats[l_team]["GF"] += gl
        stats[l_team]["GC"] += gv
        stats[v_team]["GF"] += gv
        stats[v_team]["GC"] += gl

        if gl > gv:
            stats[l_team]["G"] += 1
            stats[v_team]["P"] += 1
        elif gl < gv:
            stats[v_team]["G"] += 1
            stats[l_team]["P"] += 1
        else:
            stats[l_team]["E"] += 1
            stats[v_team]["E"] += 1

    table = pd.DataFrame.from_dict(stats, orient="index").reset_index().rename(columns={"index": "Equipo"})
    table["DIF"] = table["GF"] - table["GC"]
    table["PTS"] = table["G"] * 3 + table["E"]
    table = table.sort_values(["PTS", "DIF", "GF"], ascending=[False, False, False]).reset_index(drop=True)
    table["Pos"] = table.index + 1
    return table[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DIF", "PTS"]]


def project_table(partidos: pd.DataFrame, simulations: int = 1000, seed: int = 42) -> pd.DataFrame:
    df = prepare_matches(partidos)
    base = current_table(df)
    if base.empty:
        return pd.DataFrame()

    teams = base["Equipo"].tolist()
    pts_base = dict(zip(base["Equipo"], base["PTS"]))
    pos_base = dict(zip(base["Equipo"], base["Pos"]))

    rng = np.random.default_rng(seed)
    rank_records = {t: [] for t in teams}
    gain_records = {t: [] for t in teams}

    for _ in range(simulations):
        pts = pts_base.copy()

        for team in teams:
            rivals = [r for r in teams if r != team]
            if not rivals:
                continue
            rival = rng.choice(rivals)
            pred = predict_match(df, team, rival)
            probs = pred["probs"]

            outcome = rng.choice(["win", "draw", "loss"], p=[probs["win_a"], probs["draw"], probs["win_b"]])
            if outcome == "win":
                pts[team] += 3
            elif outcome == "draw":
                pts[team] += 1

        ranking = sorted(teams, key=lambda t: pts[t], reverse=True)
        rank_pos = {team: i + 1 for i, team in enumerate(ranking)}

        for t in teams:
            rank_records[t].append(rank_pos[t])
            gain_records[t].append(pts[t] - pts_base[t])

    rows = []
    for t in teams:
        base_pos = pos_base[t]
        ranks = np.array(rank_records[t])
        gains = np.array(gain_records[t], dtype=float)
        rows.append(
            {
                "Equipo": t,
                "Pos actual": base_pos,
                "PTS actuales": pts_base[t],
                "PTS esperados (+1 fecha)": round(float(pts_base[t] + gains.mean()), 2),
                "Pos esperada": round(float(ranks.mean()), 2),
                "Prob. subir": round(float((ranks < base_pos).mean()), 3),
                "Prob. bajar": round(float((ranks > base_pos).mean()), 3),
                "Cambio probable": "⬆️" if (ranks < base_pos).mean() > 0.45 else "⬇️" if (ranks > base_pos).mean() > 0.45 else "➡️",
            }
        )

    out = pd.DataFrame(rows).sort_values(["Pos actual", "PTS actuales"], ascending=[True, False]).reset_index(drop=True)
    return out
