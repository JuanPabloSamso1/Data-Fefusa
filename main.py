"""
Punto de entrada principal para el pipeline ETL de Sports Analytics (Futsal).
"""
import os
import logging
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from src.scraper import ScorefyScraper
from src.processor import DataProcessor
from src.db_manager import MySQLManager

# Configuración de rutas
CSV_DIR = Path("csv")
CSV_DIR.mkdir(exist_ok=True)

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Iniciando pipeline ETL de Futsal...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # URL del torneo a procesar
    # Debe configurarse en el entorno o .env, con un valor por defecto para evitar roturas
    url_torneo = os.getenv("TORNEO_URL", "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results")
    
    # Instanciar componentes
    scraper = ScorefyScraper()
    processor = DataProcessor()
    db_manager = MySQLManager()
    
    try:
        # --- 1. EXTRACCIÓN GLOBAL ---
        partidos_fixture = scraper.get_fixture_urls(url_torneo)
        
        if not partidos_fixture:
            logger.warning("No se encontraron partidos finalizados para procesar.")
            return

        logger.info(f"Se procesarán {len(partidos_fixture)} partidos.")
        
        # --- 2. ITERACIÓN POR PARTIDO ---
        for partido_idx, partido_info in enumerate(partidos_fixture, 1):
            match_id = partido_info.get("id")
            match_url = partido_info.get("url")
            
            logger.info(f"")
            logger.info(f"--- Procesando Partido {partido_idx}/{len(partidos_fixture)}: ID {match_id} ---")
            
            try:
                # a. Extracción pormenorizada del partido
                match_data = scraper.get_match_data(match_url)
                
                # Desempaquetar datos en crudo
                raw_events = match_data.get("initialFanLog", [])
                raw_players = match_data.get("convocadas", [])
                # match_metadata = match_data.get("matchFull", {})
                
                # b. Transformación (Procesamiento en memoria usando Pandas)
                match_metadata = match_data.get("matchFull", {})
                df_torneos, df_partidos = processor.process_metadata(match_metadata, match_id)
                
                df_eventos = processor.process_events(raw_events, match_id)
                df_jugadores = processor.process_players(raw_players)
                df_staff = processor.process_staff(raw_players)
                
                # Derivar Equipos desde matchFull (tiene los nombres reales del HTML)
                equipos_rows = []
                local_id = match_metadata.get("equipo_local_id")
                local_nombre = match_metadata.get("equipo_local_nombre") or f"Equipo ID: {local_id}"
                visitante_id = match_metadata.get("equipo_visitante_id")
                visitante_nombre = match_metadata.get("equipo_visitante_nombre") or f"Equipo ID: {visitante_id}"
                
                if local_id:
                    equipos_rows.append({"id": str(local_id), "nombre": local_nombre})
                if visitante_id:
                    equipos_rows.append({"id": str(visitante_id), "nombre": visitante_nombre})
                
                df_equipos = pd.DataFrame(equipos_rows).drop_duplicates(subset=['id'])
                
                # c. Carga a Base de Datos (Load)
                
                # 0. UPSERT Torneos
                if not df_torneos.empty:
                    db_manager.upsert_torneos(df_torneos)
                    
                # 1. UPSERT Equipos
                if not df_equipos.empty:
                    db_manager.upsert_equipos(df_equipos)
                    
                # 2. UPSERT Partidos
                if not df_partidos.empty:
                    db_manager.upsert_partidos(df_partidos)
                    
                # 3. UPSERT Jugadores
                if not df_jugadores.empty:
                    db_manager.upsert_jugadores(df_jugadores)
                    
                # 4. UPSERT Cuerpo Técnico
                if not df_staff.empty:
                    db_manager.upsert_staff(df_staff)
                    
                # 5. Insertar Eventos (Con Batch Processing interno y atómico)
                if not df_eventos.empty:
                    db_manager.insert_events(df_eventos, batch_size=500)
                    
                # d. Actualizar CSVs Locales Incrementalmente
                def _append_to_csv(df: pd.DataFrame, filename: str, subset_id: str):
                    if df.empty: return
                    filepath = CSV_DIR / filename
                    if filepath.exists():
                        existing_df = pd.read_csv(filepath)
                        # Concatenar y eliminar duplicados basándose en el ID principal
                        combined = pd.concat([existing_df, df]).drop_duplicates(subset=[subset_id], keep="last")
                        combined.to_csv(filepath, index=False)
                    else:
                        df.to_csv(filepath, index=False)

                _append_to_csv(df_torneos, "torneos.csv", "id")
                _append_to_csv(df_equipos, "equipos.csv", "id")
                _append_to_csv(df_partidos, "partidos.csv", "id")
                _append_to_csv(df_jugadores, "jugadores.csv", "id")
                _append_to_csv(df_eventos, "eventos.csv", "id")
                
                logger.info(f"Partido {match_id} procesado, guardado en DB y CSVs actualizados.")
                
            except Exception as e:
                # MANEJO ROBUSTO DE EXCEPCIONES: Si falla un partido, se loguea y continúa con el sgt.
                logger.error(f"Error procesando el partido {match_id} ({match_url}): {e}", exc_info=False)
                # Para un flujo de despliegue, omitimos exc_info=True para no inundar los logs. 
                # Si falla, simplemente continúa aislando el error.
                continue
                
    except Exception as e:
        logger.critical(f"Falla crítica en el orquestador principal del pipeline ETL: {e}", exc_info=True)
    finally:
        # Cierre ordenado de conexiones
        db_manager.close()
        logger.info("Pipeline ETL finalizado.")

if __name__ == "__main__":
    main()
