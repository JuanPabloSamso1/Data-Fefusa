"""Data loader without Streamlit — used by FastAPI."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
import pandas as pd
from pathlib import Path

CSV_DIR = Path(__file__).parent.parent / "csv"

_TRACKED = ["eventos.csv", "partidos.csv", "equipos.csv", "torneos.csv", "personas.csv"]


def _csv_signature() -> tuple:
    sig = []
    for f in _TRACKED:
        p = CSV_DIR / f
        if p.exists():
            s = p.stat()
            sig.append((f, s.st_mtime_ns, s.st_size))
        else:
            sig.append((f, None, None))
    return tuple(sig)


def get_last_data_update() -> datetime | None:
    mtimes = [m for _, m, _ in _csv_signature() if m]
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes) / 1_000_000_000)


def _normalize_events_frame(eventos: pd.DataFrame) -> pd.DataFrame:
    if eventos.empty:
        return eventos.copy()

    out = eventos.copy()
    for col in ["id", "partido_id", "equipo_id", "jugador_id", "persona_id", "tipo_evento", "periodo"]:
        if col in out.columns:
            out[col] = out[col].replace("", pd.NA)

    if "persona_id" not in out.columns and "jugador_id" in out.columns:
        out = out.rename(columns={"jugador_id": "persona_id"})
    elif "jugador_id" in out.columns:
        if "persona_id" not in out.columns:
            out["persona_id"] = out["jugador_id"]
        else:
            out["persona_id"] = out["persona_id"].fillna(out["jugador_id"])
        out["jugador_id"] = out["jugador_id"].fillna(out["persona_id"])

    helper_cols: list[str] = []
    if "id" in out.columns:
        if "persona_id" in out.columns:
            out["_persona_rank"] = out["persona_id"].notna().astype(int)
            helper_cols.append("_persona_rank")
        if "jugador_id" in out.columns:
            out["_jugador_rank"] = out["jugador_id"].notna().astype(int)
            helper_cols.append("_jugador_rank")

        if helper_cols:
            out = out.sort_values(["id", *helper_cols], ascending=[True, *([False] * len(helper_cols))])
        out = out.drop_duplicates(subset=["id"], keep="first")

    return out.drop(columns=helper_cols, errors="ignore")


_cache: dict = {}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sig = _csv_signature()
    if _cache.get("sig") == sig:
        return _cache["data"]

    eventos = _normalize_events_frame(pd.read_csv(CSV_DIR / "eventos.csv"))
    partidos = pd.read_csv(CSV_DIR / "partidos.csv")
    equipos = pd.read_csv(CSV_DIR / "equipos.csv")
    torneos = pd.read_csv(CSV_DIR / "torneos.csv")

    personas_path = CSV_DIR / "personas.csv"
    if personas_path.exists():
        personas = pd.read_csv(personas_path).drop_duplicates(subset=["id"], keep="last")
    else:
        personas = pd.DataFrame(columns=["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"])

    if "persona_id" not in eventos.columns and "jugador_id" in eventos.columns:
        eventos = eventos.rename(columns={"jugador_id": "persona_id"})

    eventos = eventos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_id", "nombre": "equipo"}),
        on="equipo_id", how="left"
    )
    eventos = eventos.merge(
        personas[["id", "nombre", "tipo_persona", "rol_ct"]].rename(columns={"id": "persona_id", "nombre": "persona"}),
        on="persona_id", how="left"
    )
    eventos["jugador"] = eventos.get("persona")

    eventos = eventos.merge(
        partidos[["id", "torneo_id", "jornada"]].rename(columns={"id": "partido_id"}),
        on="partido_id", how="left"
    )
    eventos = eventos.merge(
        torneos[["id", "nombre", "temporada"]].rename(columns={"id": "torneo_id", "nombre": "categoria"}),
        on="torneo_id", how="left"
    )
    if "temporada" in eventos.columns:
        eventos["temporada"] = eventos["temporada"].apply(
            lambda x: str(x).split(" - ")[-1] if pd.notna(x) else x
        )

    partidos = partidos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_local_id", "nombre": "equipo_local"}),
        on="equipo_local_id", how="left"
    )
    partidos = partidos.merge(
        equipos[["id", "nombre"]].rename(columns={"id": "equipo_visitante_id", "nombre": "equipo_visitante"}),
        on="equipo_visitante_id", how="left"
    )
    partidos = partidos.merge(
        torneos[["id", "nombre", "temporada"]].rename(columns={"id": "torneo_id", "nombre": "categoria"}),
        on="torneo_id", how="left"
    )
    if "temporada" in partidos.columns:
        partidos["temporada"] = partidos["temporada"].apply(
            lambda x: str(x).split(" - ")[-1] if pd.notna(x) else x
        )

    result = (eventos, partidos, personas, equipos, torneos)
    _cache["sig"] = sig
    _cache["data"] = result
    return result
