import os
import pandas as pd
import logging
from src.scraper import ScorefyScraper
from src.processor import DataProcessor

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def run_dry_test():
    """Ejecuta una prueba en seco de Extracción y Transformación sin usar Base de Datos."""
    
    # URL específica del torneo Scorefy a analizar
    url_torneo = "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results"
    
    # Instanciar únicamente Scraper y Processor
    scraper = ScorefyScraper()
    processor = DataProcessor()
    
    # Extracción de URLs del fixture
    logger.info("Obteniendo URLs de partidos finalizados...")
    fixture = scraper.get_fixture_urls(url_torneo)
    
    if not fixture:
        logger.error("No se encontraron partidos para la prueba.")
        return

    # Procesar todos los partidos del fixture
    fixture_test = fixture
    
    logger.info(f"Se procesarán {len(fixture_test)} partido(s) para el Test.")
    
    all_events = []
    all_players = []
    all_staff = []
    all_torneos = []
    all_partidos = []
    
    for idx, match_info in enumerate(fixture_test, 1):
        match_id = match_info.get("id")
        match_url = match_info.get("url")
        
        logger.info(f"--- Procesando Test Partido {idx}: {match_id} ---")
        
        # Extracción
        match_data = scraper.get_match_data(match_url)
        raw_events = match_data.get("initialFanLog", [])
        raw_players = match_data.get("convocadas", [])
        
        # Transformación con Pandas
        # Extract MatchFull Metadata
        match_metadata = match_data.get("matchFull", {})
        df_torneos_partido, df_partidos_partido = processor.process_metadata(match_metadata, match_id)
        
        df_eventos_partido = processor.process_events(raw_events, match_id)
        df_jugadores_partido = processor.process_players(raw_players)
        df_staff_partido = processor.process_staff(raw_players)
        
        all_events.append(df_eventos_partido)
        all_players.append(df_jugadores_partido)
        all_staff.append(df_staff_partido)
        all_torneos.append(df_torneos_partido)
        all_partidos.append(df_partidos_partido)
        logger.info(f"Extraídos datos para el partido {match_id}.")

    # Consolidar los DataFrames resultantes
    df_eventos_final = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()
    df_jugadores_final = pd.concat(all_players, ignore_index=True) if all_players else pd.DataFrame()
    df_staff_final = pd.concat(all_staff, ignore_index=True) if all_staff else pd.DataFrame()
    df_torneos_final = pd.concat(all_torneos, ignore_index=True).drop_duplicates(subset=['id']) if all_torneos else pd.DataFrame()
    df_partidos_final = pd.concat(all_partidos, ignore_index=True) if all_partidos else pd.DataFrame()

    # --- Validación Matemática e Inspección de Schema en Consola ---
    print("\n" + "="*50)
    print("VALIDACIÓN DE SCHEMA EVENTOS: df_eventos.info()")
    print("="*50)
    df_eventos_final.info()
    
    print("\n" + "="*50)
    print("MUESTRA REPRESENTATIVA DE EVENTOS (Regla de Temporizadores): df_eventos.head(10)")
    print("="*50)
    # Selecciona solo columnas de tiempo para ver la matemática limpia
    cols_tiempo_futsal = [
        col for col in ['id', 'partido_id', 'periodo', 'minuto', 'segundo', 'tipo_evento'] 
        if col in df_eventos_final.columns
    ]
    print(df_eventos_final[cols_tiempo_futsal].head(10))
    print("\n======================================================\n")

    # --- Exportación a CSV (Output Directory) ---
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    path_eventos = os.path.join(output_dir, "eventos_test.csv")
    path_jugadores = os.path.join(output_dir, "jugadores_test.csv")
    path_staff = os.path.join(output_dir, "cuerpo_tecnico_test.csv")
    path_torneos = os.path.join(output_dir, "torneos_test.csv")
    path_partidos = os.path.join(output_dir, "partidos_test.csv")
    
    df_eventos_final.to_csv(path_eventos, index=False)
    df_jugadores_final.to_csv(path_jugadores, index=False)
    df_staff_final.to_csv(path_staff, index=False)
    df_torneos_final.to_csv(path_torneos, index=False)
    df_partidos_final.to_csv(path_partidos, index=False)
    
    logger.info(f"Se crearon los CSV de prueba exitosamente en: {output_dir}")
    logger.info(f"- {path_eventos}")
    logger.info(f"- {path_jugadores}")
    logger.info(f"- {path_staff}")
    logger.info(f"- {path_torneos}")
    logger.info(f"- {path_partidos}")

if __name__ == "__main__":
    run_dry_test()
