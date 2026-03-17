import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ScorefyScraper:
    """
    Clase encargada de raspar datos web de Scorefy mediante peticiones HTTP
    y extracción de JSON inyectado en el HTML de la aplicación Next.js.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        )

    def _clean_escaped_json(self, escaped_str: str) -> str:
        """
        Limpia los caracteres escapados típicos de JSON inyectado como string.
        """
        return escaped_str.replace('\\"', '"').replace("\\\\", "\\")

    def _find_key_value_start(self, html: str, key: str, start: int = 0) -> Optional[int]:
        """
        Devuelve el índice donde comienza el valor JSON asociado a una clave
        dentro del payload serializado de Next.js.
        """
        candidates: List[Tuple[int, int]] = []
        for pattern in (f'\\"{key}\\":', f'"{key}":'):
            idx = html.find(pattern, start)
            if idx != -1:
                candidates.append((idx, idx + len(pattern)))

        if not candidates:
            return None

        _, value_start = min(candidates, key=lambda item: item[0])
        while value_start < len(html) and html[value_start].isspace():
            value_start += 1
        return value_start

    def _extract_balanced_json_fragment(self, html: str, start: int) -> Optional[str]:
        """
        Extrae un objeto/lista JSON balanceado a partir del primer "{" o "[".
        Respeta strings y escapes para no truncar arrays anidados.
        """
        if start >= len(html) or html[start] not in "[{":
            return None

        pairs = {"{": "}", "[": "]"}
        stack = [html[start]]
        in_string = False
        escaped = False

        for idx in range(start + 1, len(html)):
            char = html[idx]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char in pairs:
                stack.append(char)
                continue

            if char in "}]":
                if not stack:
                    return None
                last = stack.pop()
                if pairs[last] != char:
                    return None
                if not stack:
                    return html[start : idx + 1]

        return None

    def _extract_json_value(self, html: str, key: str, start: int = 0) -> Tuple[Optional[Any], int]:
        """
        Extrae y parsea el valor JSON asociado a una clave.
        Retorna (valor, siguiente_posición_de_búsqueda).
        """
        value_start = self._find_key_value_start(html, key, start)
        if value_start is None:
            return None, -1

        fragment = self._extract_balanced_json_fragment(html, value_start)
        if fragment is None:
            return None, value_start + 1

        try:
            return json.loads(self._clean_escaped_json(fragment)), value_start + len(fragment)
        except json.JSONDecodeError:
            return None, value_start + len(fragment)

    def _extract_all_json_values(self, html: str, key: str) -> List[Any]:
        """
        Extrae todas las ocurrencias JSON asociadas a una clave.
        """
        values: List[Any] = []
        cursor = 0

        while cursor != -1 and cursor < len(html):
            value, next_cursor = self._extract_json_value(html, key, cursor)
            if next_cursor == -1:
                break
            if value is not None:
                values.append(value)
            cursor = next_cursor

        return values

    def _pick_best_candidate(self, values: List[Any], expected_type: type) -> Optional[Any]:
        """
        Elige el candidato más útil entre múltiples ocurrencias de una clave.
        """
        typed_values = [value for value in values if isinstance(value, expected_type)]
        if not typed_values:
            return None

        if expected_type is list:
            return max(typed_values, key=len)
        if expected_type is dict:
            return max(typed_values, key=lambda value: len(value.keys()))

        return typed_values[0]

    def _derive_fecha_from_display(
        self,
        match_payload: Dict[str, Any],
        fallback_data: Dict[str, Any],
        torneo_id: str,
    ) -> Optional[str]:
        """
        Arma una fecha utilizable si no viene dateOriginal.
        """
        display_date = match_payload.get("date") or fallback_data.get("date")
        display_time = match_payload.get("startTime") or match_payload.get("time") or fallback_data.get("time")

        if not display_date:
            return None

        date_match = re.match(r"(\d{1,2})/(\d{1,2})", str(display_date))
        if not date_match:
            return None

        year_match = re.search(r"(\d{4})", torneo_id or "")
        year = year_match.group(1) if year_match else "2026"
        time_str = str(display_time or "00:00")

        day, month = date_match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d} {time_str}:00"[:19]

    def _extract_json_list_by_regex(self, html: str, patterns: List[str]) -> Optional[List[Any]]:
        """
        Intenta extraer una lista JSON usando regex directas, replicando el flujo
        original que funcionaba bien para bloques planos como initialFanLog.
        """
        for pattern in patterns:
            match = re.search(pattern, html)
            if not match:
                continue
            try:
                payload = json.loads(self._clean_escaped_json(match.group(1)))
                if isinstance(payload, list):
                    return payload
            except json.JSONDecodeError:
                continue
        return None

    def _extract_scalar_with_regex(self, html: str, patterns: List[str]) -> Optional[str]:
        """
        Extrae un valor escalar por regex, devolviendo el primer match.
        """
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def _merge_non_empty_dicts(self, base: Optional[Dict[str, Any]], overlay: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combina diccionarios priorizando valores no vacíos del overlay.
        """
        result = dict(base or {})
        for key, value in (overlay or {}).items():
            if value not in (None, "", [], {}):
                result[key] = value
        return result

    def _extract_fixture_match_data_from_html(self, html: str, match_id: str) -> Dict[str, Any]:
        """
        Extrae metadata estable del results page para un match específico.
        """
        pattern = (
            rf'\\"match\\":\{{\\"id\\":\\"{re.escape(match_id)}\\",'
            rf'.*?\\"date\\":\\"(?P<date>[^\\"]+)\\",'
            rf'.*?\\"time\\":\\"(?P<time>[^\\"]+)\\",'
            rf'.*?\\"round\\":(?P<round>\d+),'
            rf'.*?\\"teams\\":(?P<teams>\[.*?\]),'
            rf'.*?\\"categoryName\\":\\"(?P<category>[^\\"]+)\\",'
            rf'.*?\\"divisionName\\":\\"(?P<division>[^\\"]+)\\",'
            rf'.*?\\"tour_id\\":\\"(?P<tour_id>[^\\"]+)\\",'
            rf'.*?\\"dateOriginal\\":\\"\$D(?P<date_original>[^\\"]+)\\"'
        )
        match = re.search(pattern, html)
        if not match:
            return {"id": match_id}

        teams: List[Dict[str, Any]] = []
        try:
            teams = json.loads(self._clean_escaped_json(match.group("teams")))
        except json.JSONDecodeError:
            teams = []

        return {
            "id": match_id,
            "date": match.group("date"),
            "time": match.group("time"),
            "round": int(match.group("round")),
            "teams": teams,
            "categoryName": match.group("category"),
            "divisionName": match.group("division"),
            "tour_id": match.group("tour_id"),
            "dateOriginal": f"$D{match.group('date_original')}",
        }

    def _is_truthy(self, value: Any) -> bool:
        """
        Normaliza flags booleanos provenientes de payloads inconsistentes.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if value is None:
            return False
        return str(value).strip().lower() in {"true", "1", "yes", "si"}

    def _is_finished_match(self, match: Dict[str, Any]) -> bool:
        """
        Determina si un match está finalizado y tiene player scores.
        """
        return str(match.get("statusId")) == "57" and self._is_truthy(match.get("hasPlayerScores"))

    def _extract_tournament_id(
        self,
        html: str,
        url_partido: str,
        fallback_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Prioriza fuentes confiables para el identificador del torneo sin depender
        de slugs inventados ni de la URL del scoreboard.
        """
        if fallback_data:
            fallback_tour = fallback_data.get("tour_id") or fallback_data.get("tournamentId")
            if fallback_tour:
                return str(fallback_tour)

        patterns = [
            r'\\"tour_id\\":\\"([^\\"]+)\\"',
            r'\\"tournamentId\\":\\"([^\\"]+)\\"',
            r'"tour_id":"([^"]+)"',
            r'"tournamentId":"([^"]+)"',
            r'<meta property="og:url" content="https://scorefy\.app/[^"]+/([^"/]+)"',
            r'/([A-Z]{3,}-[A-Z]-[A-Z]-[A-Z]{2,}-[A-Z]-\d{4})(?:/|")',
        ]

        for pattern in patterns:
            match = re.search(pattern, html) or re.search(pattern, url_partido)
            if match:
                return match.group(1)

        return "DESCONOCIDO"

    def _extract_season_name(self, html: str, torneo_nombre: str) -> str:
        """
        Deriva una etiqueta de temporada legible a partir del título HTML.
        """
        title_match = re.search(r"<title>(.*?)Scoreboard", html) or re.search(r"<title>(.*?)Resultados", html)
        if not title_match:
            return "Desconocida"

        title_text = (
            title_match.group(1)
            .replace("FEFUSA Mendoza", "")
            .replace("Primera", "")
            .strip(" -")
            .strip()
        )

        if torneo_nombre != "Torneo Desconocido" and title_text:
            return f"{torneo_nombre} - {title_text}"

        return title_text or "Desconocida"

    def _build_match_full(
        self,
        html: str,
        url_partido: str,
        match_payload: Optional[Dict[str, Any]] = None,
        fallback_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Normaliza metadata de partido combinando scoreboard + fallback del results page.
        """
        match_payload = match_payload or {}
        fallback_data = fallback_data or {}

        torneo_id = self._extract_tournament_id(html, url_partido, fallback_data)
        categoria = fallback_data.get("categoryName") or match_payload.get("categoryName") or ""
        division = fallback_data.get("divisionName") or match_payload.get("divisionName") or ""
        torneo_nombre = f"{categoria} {division}".strip() or "Torneo Desconocido"
        temporada = self._extract_season_name(html, torneo_nombre)
        fecha = fallback_data.get("dateOriginal") or match_payload.get("dateOriginal")
        if not fecha:
            fecha = self._derive_fecha_from_display(match_payload, fallback_data, torneo_id)
        jornada = fallback_data.get("round")
        if jornada is None:
            jornada = match_payload.get("round")

        teams = fallback_data.get("teams")
        if not isinstance(teams, list) or len(teams) < 2:
            teams = match_payload.get("teams") or []
        goles_local = 0
        goles_visitante = 0
        equipo_local_id = None
        equipo_visitante_id = None
        equipo_local_nombre = None
        equipo_visitante_nombre = None

        if isinstance(teams, list) and len(teams) >= 2:
            equipo_local = teams[0] or {}
            equipo_visitante = teams[1] or {}
            equipo_local_id = equipo_local.get("id")
            equipo_local_nombre = equipo_local.get("name")
            goles_local = equipo_local.get("goals", 0) or 0
            equipo_visitante_id = equipo_visitante.get("id")
            equipo_visitante_nombre = equipo_visitante.get("name")
            goles_visitante = equipo_visitante.get("goals", 0) or 0

        equipo_local = match_payload.get("localTeam") or {}
        equipo_visitante = match_payload.get("visitorTeam") or {}
        if isinstance(equipo_local, dict):
            equipo_local_id = equipo_local_id or equipo_local.get("id")
            equipo_local_nombre = equipo_local_nombre or equipo_local.get("name")
            if not goles_local:
                goles_local = equipo_local.get("goals", 0) or 0
        if isinstance(equipo_visitante, dict):
            equipo_visitante_id = equipo_visitante_id or equipo_visitante.get("id")
            equipo_visitante_nombre = equipo_visitante_nombre or equipo_visitante.get("name")
            if not goles_visitante:
                goles_visitante = equipo_visitante.get("goals", 0) or 0

        return {
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

        fixture_finalizado: List[Dict[str, Any]] = []
        seen_ids = set()
        matches = self._extract_all_json_values(response.text, "match")
        pattern = r'\\"id\\":\\"([a-z0-9]+)\\",\\"date.*?(?:\\"statusId\\":57).*?\\"hasPlayerScores\\":true'

        logger.debug(f"Se encontraron {len(matches)} estructuras de partido en el fixture.")

        structured_by_id: Dict[str, Dict[str, Any]] = {}
        structured_candidate_ids: List[str] = []

        for match in matches:
            try:
                if not isinstance(match, dict):
                    continue

                match_id = match.get("id")
                if not match_id:
                    continue

                match_id = str(match_id)
                current_match = structured_by_id.get(match_id)
                if current_match is None or len(match) > len(current_match):
                    structured_by_id[match_id] = match

                if self._is_finished_match(match) and match_id not in structured_candidate_ids:
                    structured_candidate_ids.append(match_id)
            except Exception as e:
                logger.warning(f"Error inesperado al procesar un match del fixture: {e}")

        regex_candidate_ids = list(dict.fromkeys(re.findall(pattern, response.text)))
        candidate_ids = regex_candidate_ids + [match_id for match_id in structured_candidate_ids if match_id not in regex_candidate_ids]

        for match_id in candidate_ids:
            try:
                if match_id in seen_ids:
                    continue

                seen_ids.add(match_id)
                fixture_data = self._extract_fixture_match_data_from_html(response.text, match_id)
                fixture_data = self._merge_non_empty_dicts(structured_by_id.get(match_id), fixture_data)
                fixture_finalizado.append(
                    {
                        "id": match_id,
                        "url": f"https://scorefy.app/cast/scoreboard/{match_id}",
                        "data": fixture_data,
                    }
                )
            except Exception as e:
                logger.warning(f"Error inesperado al consolidar un match del fixture: {e}")

        if not fixture_finalizado:
            logger.warning(
                "No se pudieron consolidar partidos válidos desde payload estructurado ni regex de seguridad."
            )

        logger.info(f"Se obtuvieron {len(fixture_finalizado)} partidos válidos (finalizados y con puntuación).")
        return fixture_finalizado

    def get_match_data(self, url_partido: str, fallback_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extrae los datos detallados de un partido:
        initialFanLog (eventos), convocadas (planteles) y metadata del partido.
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
            "matchFull": {},
        }

        fanlog = self._extract_json_list_by_regex(
            html,
            [
                r'\\"initialFanLog\\":(\[.*?\])',
                r'"initialFanLog":(\[.*?\])',
            ],
        )
        if not isinstance(fanlog, list):
            fanlog = self._pick_best_candidate(self._extract_all_json_values(html, "initialFanLog"), list)
        if isinstance(fanlog, list):
            match_data_extract["initialFanLog"] = fanlog
        elif fanlog is None:
            logger.warning(f"No se pudo extraer 'initialFanLog' para URL: {url_partido}")

        try:
            matchfull_anchor = self._find_key_value_start(html, "matchFull")

            convocadas = self._extract_json_list_by_regex(
                html,
                [
                    r'\\"convocadas\\":(\[.*?\])',
                    r'"convocadas":(\[.*?\])',
                ],
            )
            embedded_convocadas = None
            local_team = None
            visitor_team = None
            match_payload = None

            if matchfull_anchor is not None:
                local_team, _ = self._extract_json_value(html, "localTeam", matchfull_anchor)
                visitor_team, _ = self._extract_json_value(html, "visitorTeam", matchfull_anchor)
                embedded_convocadas, _ = self._extract_json_value(html, "convocadas", matchfull_anchor)

            if not isinstance(convocadas, list):
                convocadas = self._pick_best_candidate(self._extract_all_json_values(html, "convocadas"), list)
            if not isinstance(convocadas, list) and isinstance(embedded_convocadas, list):
                convocadas = embedded_convocadas
            if not isinstance(match_payload, dict):
                match_payload = self._pick_best_candidate(self._extract_all_json_values(html, "matchFull"), dict)
            if not isinstance(match_payload, dict):
                match_payload = self._pick_best_candidate(self._extract_all_json_values(html, "match"), dict)

            round_value = self._extract_scalar_with_regex(
                html,
                [
                    r'\\"round\\":(\d+)',
                    r'"round":(\d+)',
                ],
            )
            direct_match_payload = {
                "tournamentId": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"tournamentId\\":\\"([^\\"]+)\\"',
                        r'"tournamentId":"([^"]+)"',
                    ],
                ),
                "round": int(round_value) if round_value is not None else None,
                "categoryName": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"categoryName\\":\\"([^\\"]+)\\"',
                        r'"categoryName":"([^"]+)"',
                    ],
                ),
                "divisionName": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"divisionName\\":\\"([^\\"]+)\\"',
                        r'"divisionName":"([^"]+)"',
                    ],
                ),
                "dateOriginal": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"dateOriginal\\":\\"\$D([^\\"]+)\\"',
                        r'"dateOriginal":"\$D([^"]+)"',
                    ],
                ),
                "date": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"date\\":\\"([^\\"]+)\\"',
                        r'"date":"([^"]+)"',
                    ],
                ),
                "startTime": self._extract_scalar_with_regex(
                    html,
                    [
                        r'\\"startTime\\":\\"([^\\"]+)\\"',
                        r'"startTime":"([^"]+)"',
                    ],
                ),
                "localTeam": local_team if isinstance(local_team, dict) else None,
                "visitorTeam": visitor_team if isinstance(visitor_team, dict) else None,
            }
            match_payload = self._merge_non_empty_dicts(match_payload, direct_match_payload)

            if isinstance(convocadas, list):
                match_data_extract["convocadas"] = convocadas
            else:
                logger.warning(f"No se pudo extraer 'convocadas' para URL: {url_partido}")

            match_data_extract["matchFull"] = self._build_match_full(
                html=html,
                url_partido=url_partido,
                match_payload=match_payload if isinstance(match_payload, dict) else None,
                fallback_data=fallback_data,
            )
        except Exception as e:
            logger.warning(f"Error extrayendo 'matchFull' para URL: {url_partido}. {e}")

        return match_data_extract
