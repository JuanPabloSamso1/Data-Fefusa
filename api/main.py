"""FastAPI backend — serves all dashboard data as JSON."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.data_loader import load_data, get_last_data_update
from dashboard.analytics import (
    build_standings,
    build_egr_table,
    build_current_streaks,
    build_global_summary,
    build_team_discipline,
    build_player_discipline,
    build_player_catalog,
    build_team_profile,
    build_player_profile,
    build_player_comparison,
    build_match_selector,
    build_match_dataset,
    build_discipline_timeline,
    build_goal_momentum,
    build_goals_by_team,
    build_events_by_type,
    build_goals_by_round,
    build_top_scorers,
    build_goals_by_period,
    build_top_undisciplined,
    format_last_updated,
)
from api.filters import apply_event_filters, apply_match_filters
from dashboard.predictions import predict_match, project_table

@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.scheduler import start, stop
    start()
    yield
    stop()


app = FastAPI(title="FEFUSA API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static React build (mounted after all API routes) ─────────────────────────
DIST = ROOT / "frontend" / "dist"


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to JSON-safe list of dicts."""
    return df.replace({np.nan: None, float("inf"): None, float("-inf"): None}).to_dict(orient="records")


def _apply_filters(
    eventos: pd.DataFrame,
    partidos: pd.DataFrame,
    categoria: str,
    temporada: str,
    jornada: str,
    equipo: str,
    tipo: str,
    jugador: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sel = {
        "categoria": categoria,
        "temporada": temporada,
        "jornada": jornada,
        "equipo": equipo,
        "tipo": tipo,
        "jugador": jugador,
    }
    ev = apply_event_filters(eventos, sel)
    pa = apply_match_filters(partidos, sel)
    return ev, pa


# ── Filter options ────────────────────────────────────────────────────────────

@app.get("/api/filters")
def get_filters():
    eventos, partidos, personas, equipos, torneos = load_data()
    categorias = sorted(eventos["categoria"].dropna().unique().tolist())
    temporadas = sorted(eventos["temporada"].dropna().unique().tolist())
    jornadas = sorted(eventos["jornada"].dropna().unique().tolist())
    equipos_list = sorted(eventos["equipo"].dropna().unique().tolist())
    tipos = sorted(eventos["tipo_evento"].dropna().unique().tolist())
    jugadores = sorted(eventos["jugador"].dropna().unique().tolist())
    last_update = get_last_data_update()
    return {
        "categorias": categorias,
        "temporadas": temporadas,
        "jornadas": jornadas,
        "equipos": equipos_list,
        "tipos": tipos,
        "jugadores": jugadores,
        "last_update": format_last_updated(last_update),
    }


# ── Liga tab ──────────────────────────────────────────────────────────────────

@app.get("/api/liga")
def get_liga(
    categoria: str = "Todas",
    temporada: str = "Todas",
    jornada: str = "Todas",
    equipo: str = "Todos",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": jornada,
           "equipo": equipo, "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)
    pa = apply_match_filters(partidos, sel)

    standings = build_standings(pa)
    egr = build_egr_table(pa)
    streaks = build_current_streaks(pa)
    summary = build_global_summary(ev, pa)
    momentum = build_goal_momentum(ev)

    return {
        "standings": _df_to_records(standings),
        "egr": _df_to_records(egr),
        "streaks": _df_to_records(streaks),
        "goals_by_team": _df_to_records(build_goals_by_team(ev)),
        "events_by_type": _df_to_records(build_events_by_type(ev)),
        "goals_by_round": _df_to_records(build_goals_by_round(ev)),
        "top_scorers": _df_to_records(build_top_scorers(ev)),
        "goals_by_period": _df_to_records(build_goals_by_period(ev)),
        "summary": summary,
        "momentum": _df_to_records(momentum),
    }


# ── Equipos ───────────────────────────────────────────────────────────────────

@app.get("/api/equipos")
def get_equipos(categoria: str = "Todas", temporada: str = "Todas"):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": "Todos", "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)
    return {"equipos": sorted(ev["equipo"].dropna().unique().tolist())}


@app.get("/api/equipo/{team}")
def get_equipo(
    team: str,
    categoria: str = "Todas",
    temporada: str = "Todas",
    jornada: str = "Todas",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": jornada,
           "equipo": "Todos", "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)
    pa = apply_match_filters(partidos, sel)

    profile = build_team_profile(ev, pa, team)
    if not profile:
        return {"error": "Equipo sin datos"}

    result = {**profile}
    for key in ["last_five", "per_match", "momentum"]:
        if key in result and isinstance(result[key], pd.DataFrame):
            result[key] = _df_to_records(result[key])

    return result


# ── Jugadores ─────────────────────────────────────────────────────────────────

@app.get("/api/jugadores")
def get_jugadores(
    categoria: str = "Todas",
    temporada: str = "Todas",
    equipo: str = "Todos",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": equipo, "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)
    catalog = build_player_catalog(ev)
    return {"jugadores": _df_to_records(catalog)}


@app.get("/api/jugador/{player_key:path}")
def get_jugador(
    player_key: str,
    categoria: str = "Todas",
    temporada: str = "Todas",
    equipo: str = "Todos",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": equipo, "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)

    profile = build_player_profile(ev, player_key)
    if not profile:
        return {"error": "Jugador sin datos"}

    result = {**profile}
    for key in ["timeline", "momentum"]:
        if key in result and isinstance(result[key], pd.DataFrame):
            result[key] = _df_to_records(result[key])

    return result


# ── Partidos ──────────────────────────────────────────────────────────────────

@app.get("/api/partidos")
def get_partidos(
    categoria: str = "Todas",
    temporada: str = "Todas",
    jornada: str = "Todas",
    equipo: str = "Todos",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": jornada,
           "equipo": equipo, "tipo": "Todos", "jugador": "Todos"}
    pa = apply_match_filters(partidos, sel)
    selector = build_match_selector(pa)
    return {"partidos": _df_to_records(selector)}


@app.get("/api/partido/{partido_id}")
def get_partido(partido_id: str, categoria: str = "Todas", temporada: str = "Todas"):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": "Todos", "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)

    dataset = build_match_dataset(ev, partidos, partido_id)
    if not dataset:
        return {"error": "Partido no encontrado"}

    result = {**dataset}
    for key in ["events", "period_summary", "momentum"]:
        if key in result and isinstance(result[key], pd.DataFrame):
            result[key] = _df_to_records(result[key])

    if "match" in result and "fecha" in result["match"]:
        fecha = result["match"]["fecha"]
        if hasattr(fecha, "isoformat"):
            result["match"]["fecha"] = fecha.isoformat()
        elif pd.isna(fecha) if not isinstance(fecha, str) else False:
            result["match"]["fecha"] = None

    return result


# ── Disciplina ────────────────────────────────────────────────────────────────

@app.get("/api/disciplina")
def get_disciplina(
    categoria: str = "Todas",
    temporada: str = "Todas",
    jornada: str = "Todas",
    equipo: str = "Todos",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": jornada,
           "equipo": equipo, "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)
    pa = apply_match_filters(partidos, sel)

    team_disc = build_team_discipline(ev, pa)
    player_disc = build_player_discipline(ev)
    timeline = build_discipline_timeline(ev)

    return {
        "equipos": _df_to_records(team_disc),
        "jugadores": _df_to_records(player_disc),
        "timeline": _df_to_records(timeline),
        "top_undisciplined": _df_to_records(build_top_undisciplined(ev)),
    }


# ── Comparativa ───────────────────────────────────────────────────────────────

@app.get("/api/comparativa")
def get_comparativa(
    jugador_a: str = Query(...),
    jugador_b: str = Query(...),
    categoria: str = "Todas",
    temporada: str = "Todas",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": "Todos", "tipo": "Todos", "jugador": "Todos"}
    ev = apply_event_filters(eventos, sel)

    comp = build_player_comparison(ev, jugador_a, jugador_b)
    if not comp:
        return {"error": "Datos insuficientes para comparación"}

    result = {**comp}
    for key in ["table", "radar"]:
        if key in result and isinstance(result[key], pd.DataFrame):
            result[key] = _df_to_records(result[key])

    return result


# ── Predicciones ──────────────────────────────────────────────────────────────

@app.get("/api/predicciones")
def get_predicciones(
    equipo_a: str = Query(...),
    equipo_b: str = Query(...),
    categoria: str = "Todas",
    temporada: str = "Todas",
):
    eventos, partidos, personas, equipos, torneos = load_data()
    sel = {"categoria": categoria, "temporada": temporada, "jornada": "Todas",
           "equipo": "Todos", "tipo": "Todos", "jugador": "Todos"}
    pa = apply_match_filters(partidos, sel)

    prediction = predict_match(pa, equipo_a, equipo_b)
    projection = project_table(pa, simulations=500)

    result = {**prediction}
    if "strengths" in result and isinstance(result["strengths"], pd.DataFrame):
        result["strengths"] = _df_to_records(result["strengths"])

    return {
        "prediction": result,
        "projection": _df_to_records(projection) if not projection.empty else [],
    }


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.post("/api/admin/run-etl", include_in_schema=False)
async def trigger_etl_now():
    """Manual trigger — runs ETL immediately in background thread."""
    import asyncio
    from api.scheduler import run_etl
    asyncio.get_event_loop().run_in_executor(None, run_etl)
    return {"status": "ETL iniciado en background"}


# ── Serve React SPA (must be LAST — catch-all after all API routes) ───────────
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str = ""):
        return FileResponse(DIST / "index.html")
