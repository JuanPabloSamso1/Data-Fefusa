"""Pure-pandas filter functions — no Streamlit dependency."""
from __future__ import annotations

import pandas as pd


def apply_event_filters(df: pd.DataFrame, sel: dict, ignore_keys: set[str] | None = None) -> pd.DataFrame:
    ignore_keys = ignore_keys or set()
    if "categoria" not in ignore_keys and sel["categoria"] != "Todas":
        df = df[df["categoria"] == sel["categoria"]]
    if "temporada" not in ignore_keys and sel["temporada"] != "Todas":
        df = df[df["temporada"] == sel["temporada"]]
    if "jornada" not in ignore_keys and sel["jornada"] != "Todas":
        df = df[df["jornada"] == sel["jornada"]]
    if "equipo" not in ignore_keys and sel["equipo"] != "Todos":
        df = df[df["equipo"] == sel["equipo"]]
    if "tipo" not in ignore_keys and sel["tipo"] != "Todos":
        df = df[df["tipo_evento"] == sel["tipo"]]
    if "jugador" not in ignore_keys and sel["jugador"] != "Todos":
        df = df[df["jugador"] == sel["jugador"]]
    return df


def apply_match_filters(df: pd.DataFrame, sel: dict, ignore_keys: set[str] | None = None) -> pd.DataFrame:
    ignore_keys = ignore_keys or set()
    if "categoria" not in ignore_keys and sel["categoria"] != "Todas":
        df = df[df["categoria"] == sel["categoria"]]
    if "temporada" not in ignore_keys and sel["temporada"] != "Todas":
        df = df[df["temporada"] == sel["temporada"]]
    if "jornada" not in ignore_keys and sel["jornada"] != "Todas":
        df = df[df["jornada"] == sel["jornada"]]
    if "equipo" not in ignore_keys and sel["equipo"] != "Todos":
        df = df[
            (df["equipo_local"] == sel["equipo"]) |
            (df["equipo_visitante"] == sel["equipo"])
        ]
    return df
