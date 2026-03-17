"""
Punto de entrada principal para el pipeline ETL de Sports Analytics (Futsal).
"""
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.processor import DataProcessor
from src.scraper import ScorefyScraper

CSV_DIR = Path("csv")
CSV_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def append_deduped_csv(df: pd.DataFrame, filename: str, subset_id: str) -> None:
    """
    Escribe o actualiza un CSV deduplicando siempre por el identificador
    principal, incluso en la primera corrida y con tipos heterogéneos.
    """
    if df.empty:
        return

    filepath = CSV_DIR / filename
    incoming_df = df.copy()

    if subset_id in incoming_df.columns:
        incoming_df[subset_id] = incoming_df[subset_id].astype(str)

    frames = [incoming_df]
    if filepath.exists():
        dtype_map = {subset_id: str} if subset_id in incoming_df.columns else None
        existing_df = pd.read_csv(filepath, dtype=dtype_map)
        if subset_id in existing_df.columns:
            existing_df[subset_id] = existing_df[subset_id].astype(str)
        frames.insert(0, existing_df)

    combined = pd.concat(frames, ignore_index=True)
    if subset_id in combined.columns:
        combined = combined.drop_duplicates(subset=[subset_id], keep="last")

    combined.to_csv(filepath, index=False)


def main() -> None:
    logger.info("Iniciando pipeline ETL de Futsal...")

    load_dotenv()

    url_torneo = os.getenv(
        "TORNEO_URL",
        "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results",
    )

    scraper = ScorefyScraper()
    processor = DataProcessor()
    try:
        partidos_fixture = scraper.get_fixture_urls(url_torneo)
        if not partidos_fixture:
            logger.warning("No se encontraron partidos finalizados para procesar.")
            return

        logger.info(f"Se procesarán {len(partidos_fixture)} partidos.")

        for partido_idx, partido_info in enumerate(partidos_fixture, 1):
            match_id = partido_info.get("id")
            match_url = partido_info.get("url")

            logger.info("")
            logger.info(f"--- Procesando Partido {partido_idx}/{len(partidos_fixture)}: ID {match_id} ---")

            try:
                match_data = scraper.get_match_data(match_url, fallback_data=partido_info.get("data"))

                raw_events = match_data.get("initialFanLog", [])
                raw_players = match_data.get("convocadas", [])
                match_metadata = match_data.get("matchFull", {})

                df_torneos, df_partidos = processor.process_metadata(match_metadata, match_id)
                if df_partidos.empty:
                    logger.warning(
                        f"Se omite el partido {match_id} por metadata incompleta. "
                        "No se insertan eventos ni personas para evitar inconsistencias."
                    )
                    continue

                df_eventos = processor.process_events(raw_events, match_id)
                df_jugadores = processor.process_players(raw_players)
                df_staff = processor.process_staff(raw_players)

                equipos_rows = []
                local_id = match_metadata.get("equipo_local_id")
                local_nombre = match_metadata.get("equipo_local_nombre") or f"Equipo ID: {local_id}"
                visitante_id = match_metadata.get("equipo_visitante_id")
                visitante_nombre = match_metadata.get("equipo_visitante_nombre") or f"Equipo ID: {visitante_id}"

                if local_id:
                    equipos_rows.append({"id": str(local_id), "nombre": local_nombre})
                if visitante_id:
                    equipos_rows.append({"id": str(visitante_id), "nombre": visitante_nombre})

                df_equipos = pd.DataFrame(equipos_rows).drop_duplicates(subset=["id"]) if equipos_rows else pd.DataFrame()

                df_personas = pd.DataFrame(columns=["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"])
                if not df_jugadores.empty:
                    tmp_j = df_jugadores.copy()
                    tmp_j["tipo_persona"] = "JUGADOR"
                    tmp_j["rol_ct"] = None
                    df_personas = pd.concat(
                        [df_personas, tmp_j[["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"]]],
                        ignore_index=True,
                    )

                if not df_staff.empty:
                    tmp_ct = df_staff.rename(columns={"rol": "rol_ct"}).copy()
                    tmp_ct["tipo_persona"] = "CT"
                    df_personas = pd.concat(
                        [df_personas, tmp_ct[["id", "equipo_id", "nombre", "tipo_persona", "rol_ct"]]],
                        ignore_index=True,
                    )

                if not df_personas.empty:
                    df_personas.drop_duplicates(subset=["id"], keep="last", inplace=True)

                append_deduped_csv(df_torneos, "torneos.csv", "id")
                append_deduped_csv(df_equipos, "equipos.csv", "id")
                append_deduped_csv(df_partidos, "partidos.csv", "id")
                if not df_personas.empty:
                    append_deduped_csv(df_personas, "personas.csv", "id")
                append_deduped_csv(df_eventos, "eventos.csv", "id")

                logger.info(f"Partido {match_id} procesado y CSVs actualizados.")

            except Exception as e:
                logger.error(f"Error procesando el partido {match_id} ({match_url}): {e}", exc_info=False)
                continue

    except Exception as e:
        logger.critical(f"Falla crítica en el orquestador principal del pipeline ETL: {e}", exc_info=True)
    finally:
        logger.info("Pipeline ETL finalizado.")


if __name__ == "__main__":
    main()
