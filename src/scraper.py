import re
import json
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ScorefyScraper:
    """
    Clase encargada de raspar datos web de Scorefy mediante peticiones HTTP
    y extracción de JSON inyectado en el HTML de la aplicación Next.js.
    """

    def __init__(self):
        self.session = requests.Session()
        # Configurar un User-Agent general para evitar bloqueos simples
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        })

    def _clean_escaped_json(self, escaped_str: str) -> str:
        """
        Limpia los caracteres escapados típicos de JSON inyectado como string.
        """
        return escaped_str.replace('\\"', '"').replace('\\\\', '\\')

    def get_fixture_urls(self, url_torneo: str) -> List[Dict[str, Any]]:
        """
        Obtiene las URLs de los partidos del fixture para un torneo específico,
        filtrando solo los que están finalizados y tienen puntuaciones de jugadores.
        """
        logger.info(f"Extrayendo fixture desde: {url_torneo}")
        
        try:
            response = self.session.get(url_torneo, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error realizando la petición a {url_torneo}: {e}")
            return []

        # Regex para ubicar los IDs de los partidos dentro del JSON inyectado en la página de Scorefy (Next.js)
        # Busca el patrón que contenga "hasPlayerScores":true y extrae el id del partido anterior a ese flag.
        pattern = r'\\"id\\":\\"([a-z0-9]+)\\",\\"date.*?(?:\\"statusId\\":57).*?\\"hasPlayerScores\\":true'
        
        raw_matches_ids = re.findall(pattern, response.text)
        # Filtrar duplicados manteniendo el orden
        match_ids = list(dict.fromkeys(raw_matches_ids))
        
        logger.debug(f"Se encontraron {len(match_ids)} IDs de partidos finalizados con puntuación.")

        fixture_finalizado: List[Dict[str, Any]] = []

        for match_id in match_ids:
            try:
                fixture_finalizado.append({
                    "id": match_id,
                    "url": f"https://scorefy.app/cast/scoreboard/{match_id}",
                    "data": {"id": match_id} # Dummy data since we only need the ID to build the URL
                })
            except Exception as e:
                logger.warning(f"Error inesperado al procesar un match_id {match_id}: {e}")

        logger.info(f"Se obtuvieron {len(fixture_finalizado)} partidos válidos (finalizados y con puntuación).")
        return fixture_finalizado

    def get_match_data(self, url_partido: str) -> Dict[str, Any]:
        """
        Extrae los datos detallados de un partido en específico: 
        initialFanLog (eventos), convocadas (planteles) y matchFull (metadatos del partido).
        """
        logger.info(f"Extrayendo datos pormenorizados del partido: {url_partido}")
        
        try:
            response = self.session.get(url_partido, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error realizando la petición al partido {url_partido}: {e}")
            return {}

        html = response.text
        
        match_data_extract = {
            "initialFanLog": [],
            "convocadas": [],
            "matchFull": {}
        }

        # Extracción del bloque initialFanLog (minuto a minuto)
        fanlog_pattern = r'\\"initialFanLog\\":(\[.*?\])'
        fanlog_match = re.search(fanlog_pattern, html)
        if fanlog_match:
            try:
                match_data_extract["initialFanLog"] = json.loads(self._clean_escaped_json(fanlog_match.group(1)))
            except json.JSONDecodeError:
                logger.warning(f"Error parseando 'initialFanLog' para URL: {url_partido}")

        # Extracción del bloque convocadas (planteles)
        convocadas_pattern = r'\\"convocadas\\":(\[.*?\])'
        convocadas_match = re.search(convocadas_pattern, html)
        if convocadas_match:
            try:
                match_data_extract["convocadas"] = json.loads(self._clean_escaped_json(convocadas_match.group(1)))
            except json.JSONDecodeError:
                logger.warning(f"Error parseando 'convocadas' para URL: {url_partido}")

        # Extracción Metadata del Partido y Torneo
        # Reemplaza la lógica json rota por regex directas a las llaves inyectadas en HTML Next.js
        try:
            # 1. Torneo ID / Nombre (tour_id, categoryName, divisionName)
            # 1. Torneo ID / Nombre
            tour_match = re.search(r'\\"tournamentId\\":\\"([^\\"]+)\\"', html)
            torneo_id = tour_match.group(1) if tour_match else None
            
            # Fallback for tournament ID from the URL
            if not torneo_id:
                # E.g. https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/...
                url_match = re.search(r'fefusa-mendoza/([^/]+)/', html)
                if url_match:
                    torneo_id = url_match.group(1)
                else:
                    torneo_id = "DESCONOCIDO"
                    
            # Nombre y Temporada
            cat_match = re.search(r'\\"categoryName\\":\\"([^\\"]+)\\"', html)
            div_match = re.search(r'\\"divisionName\\":\\"([^\\"]+)\\"', html)
            categoria = cat_match.group(1) if cat_match else ""
            division = div_match.group(1) if div_match else ""
            torneo_nombre = f"{categoria} {division}".strip() or "Torneo Desconocido"
            
            # Temporada (ej: Apertura 2026) extraerla del title tag
            # <title>FEFUSA Mendoza Primera Apertura 2026 Scoreboard - Futsal Mend...</title>
            title_match = re.search(r'<title>(.*?)Scoreboard', html)
            temporada = "Desconocida"
            if title_match:
                title_text = title_match.group(1).replace("FEFUSA Mendoza", "").replace("Primera", "").strip()
                temporada_suffix = title_text # Ej: "Apertura 2026"
                if torneo_nombre != "Torneo Desconocido" and temporada_suffix:
                    temporada = f"{torneo_nombre} - {temporada_suffix}" # "Primera FSP - Apertura 2026"
                else:
                    temporada = title_text or "Desconocida"


            # 2. Fecha / Jornada
            date_match = re.search(r'\\"dateOriginal\\":\\"\$D([^\\"]+)\\"', html)
            fecha = date_match.group(1) if date_match else None
            
            round_match = re.search(r'\\"round\\":(\d+)', html)
            jornada = int(round_match.group(1)) if round_match else None

            # 3. Datos del Partido y Equipos: "teams":[{"id":..., "goals":...}, {"id":..., "goals":...}]
            teams_pattern = r'\\"teams\\":(\[.*?\])'
            teams_match = re.search(teams_pattern, html)
            goles_local, goles_visitante = 0, 0
            equipo_local_id, equipo_visitante_id = None, None
            equipo_local_nombre, equipo_visitante_nombre = None, None
            
            if teams_match:
                try:
                    teams_json = json.loads(self._clean_escaped_json(teams_match.group(1)))
                    if len(teams_json) >= 2:
                        equipo_local_id = teams_json[0].get("id")
                        equipo_local_nombre = teams_json[0].get("name")
                        goles_local = teams_json[0].get("goals", 0)
                        
                        equipo_visitante_id = teams_json[1].get("id")
                        equipo_visitante_nombre = teams_json[1].get("name")
                        goles_visitante = teams_json[1].get("goals", 0)
                except json.JSONDecodeError:
                    logger.warning(f"Error parseando array 'teams' para URL: {url_partido}")
            
            # Construimos un objeto `matchFull` consolidado para Processor
            match_data_extract["matchFull"] = {
                "torneo_id": torneo_id,
                "torneo_nombre": torneo_nombre,
                "temporada": temporada,
                "fecha": fecha,
                "jornada": jornada,
                "equipo_local_id": equipo_local_id,
                "equipo_local_nombre": equipo_local_nombre,
                "equipo_visitante_id": equipo_visitante_id,
                "equipo_visitante_nombre": equipo_visitante_nombre,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
            }
            
        except Exception as e:
            logger.warning(f"Error extrayendo 'matchFull' (metadata) para URL: {url_partido}. {e}")

        return match_data_extract
