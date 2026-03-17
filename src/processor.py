import pandas as pd
import logging
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Clase encargada de transformar y limpiar los datos crudos extraídos
    por el scraper, adaptándolos al esquema de base de datos relacional.
    """

    def __init__(self):
        pass

    def _generate_uuid(self) -> str:
        """Genera un UUID v4 como string, utilizado para IDs faltantes."""
        return str(uuid.uuid4())

    def _extract_people_entries(self, raw_players: Any) -> List[Dict[str, Any]]:
        """
        Aplana estructuras heterogéneas de "convocadas" y devuelve entidades de personas.

        En Scorefy el bloque de planteles puede cambiar de forma entre torneos:
        - Lista plana de personas.
        - Lista de equipos con claves anidadas (players, squad, starters, substitutes, staff, etc.).
        - Objetos anidados en distintos niveles.

        Esta función recorre recursivamente el payload y se queda con diccionarios
        que parecen representar personas (id + nombre o señales de CT/jugador).
        """
        if not raw_players:
            return []

        people_entries: List[Dict[str, Any]] = []

        def walk(node: Any):
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return

            if not isinstance(node, dict):
                return

            # Si este nodo parece ser una persona, lo guardamos.
            has_person_signals = any(
                key in node
                for key in ['name', 'firstName', 'lastName', 'isCT', 'ctRole']
            )
            if node.get('id') is not None and has_person_signals:
                people_entries.append(node)

            # Continuar el recorrido por estructuras anidadas frecuentes.
            for key, value in node.items():
                if isinstance(value, (list, dict)):
                    walk(value)

        walk(raw_players)

        # Deduplicar por id manteniendo orden
        unique_people: List[Dict[str, Any]] = []
        seen_ids = set()
        for person in people_entries:
            person_id = str(person.get('id'))
            if person_id in seen_ids:
                continue
            seen_ids.add(person_id)
            unique_people.append(person)

        return unique_people

    def process_events(self, raw_events: List[Dict[str, Any]], match_id: str) -> pd.DataFrame:
        """
        Procesa la lista de eventos puros (initialFanLog) de un partido.
        Aplica reglas de negocio de futsal para transformar el tiempo.
        """
        if not raw_events:
            logger.warning(f"No hay eventos provistos para el partido {match_id}. Se retorna DataFrame vacío.")
            # Retorna DataFrame vacío con el esquema de la tabla 'eventos'
            return pd.DataFrame(columns=[
                'id', 'partido_id', 'equipo_id', 'persona_id', 'tipo_evento', 
                'minuto', 'segundo', 'periodo'
            ])

        event_rows = []
        for event in raw_events:
            # Identificadores base y FKs
            # Si el evento ya trae un id lo usamos, caso contrario generamos uno.
            evento_id = event.get('id', self._generate_uuid())
            
            # La estructura exacta del JSON inyectado determina dónde están los IDs
            # Asumimos unas claves probables (teamId, playerId, type, subType). 
            # Esto debe ajustarse si el JSON difiere.
            equipo_id = event.get('teamId')  
            # Algunos eventos históricos usan playerId, pero no siempre
            # son jugadores: también puede ser una persona del CT.
            persona_id = event.get('personId') or event.get('playerId')
            
            # El JSON usa 'scoreTypeName' para el tipo de evento
            tipo_evento = event.get('scoreTypeName', 'DESCONOCIDO')
            periodo = event.get('period', '1T') # Asumimos 1T si falta

            # Lógica Crucial de Tiempo Futsal (cuenta regresiva en segundos)
            # minute suele venir en segundos restantes. Ej: 1066.
            raw_seconds_left = event.get('minute')
            
            minuto = 0
            segundo = 0

            if raw_seconds_left is not None:
                try:
                    raw_seconds_left = int(raw_seconds_left)
                    is_first_period = str(periodo).upper() in ['1', '1T', 'FIRST_HALF', 'FIRSTHALF']
                    
                    if is_first_period:
                        # 1200 segundos = 20 minutos
                        segundo_transcurrido = 1200 - raw_seconds_left
                    else:
                        # Si es segundo periodo, arranca desde los 1200 en adelante
                        segundo_transcurrido = 2400 - raw_seconds_left
                    
                    # Prevenir números negativos
                    segundo_transcurrido = max(0, segundo_transcurrido)

                    minuto = segundo_transcurrido // 60
                    segundo = segundo_transcurrido % 60
                except (ValueError, TypeError):
                    logger.warning(f"Error procesando campo minuto ({raw_seconds_left}) en evento {evento_id}.")

            # Coordenadas (asumiendo que puedan venir en un objeto o planas)
            coord_x = event.get('x')
            coord_y = event.get('y')

            event_rows.append({
                'id': str(evento_id),
                'partido_id': str(match_id),
                'equipo_id': str(equipo_id) if equipo_id else None,
                'persona_id': str(persona_id) if persona_id else None,
                'tipo_evento': str(tipo_evento),
                'minuto': int(minuto),
                'segundo': int(segundo),
                'periodo': str(periodo)
            })

        df_eventos = pd.DataFrame(event_rows)
        if not df_eventos.empty:
            df_eventos["_row_order"] = range(len(df_eventos))
            df_eventos["_completeness"] = df_eventos[["equipo_id", "persona_id"]].notna().sum(axis=1)
            df_eventos = (
                df_eventos
                .sort_values(["id", "_completeness", "_row_order"])
                .drop_duplicates(subset=["id"], keep="last")
                .sort_values("_row_order")
                .drop(columns=["_row_order", "_completeness"])
                .reset_index(drop=True)
            )

        logger.info(f"Procesados {len(df_eventos)} eventos únicos para el partido {match_id}.")
        return df_eventos

    def process_players(self, raw_players: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extrae la lista de jugadores de las plantillas (convocadas) 
        y normaliza sus nombres.
        """
        if not raw_players:
            logger.warning("No hay lista de convocadas. Se retorna DataFrame de jugadores vacío.")
            return pd.DataFrame(columns=[
                'id', 'equipo_id', 'nombre'
            ])

        player_rows = []
        people_entries = self._extract_people_entries(raw_players)
        
        for player in people_entries:
            # Skip Technical Staff (Cuerpo Técnico)
            is_ct = player.get('isCT', False)
            ct_role = player.get('ctRole')
            
            if is_ct or ct_role is not None:
                continue

            # IDs
            jugador_id = player.get('id', self._generate_uuid())
            equipo_id = player.get('teamId')

            # Normalización del Nombre
            # Puede venir en 'name', 'firstName' + 'lastName', etc.
            raw_name = player.get('name', '')
            if not raw_name:
                fall_first = player.get('firstName', '')
                fall_last = player.get('lastName', '')
                raw_name = f"{fall_first} {fall_last}".strip()
            
            if not raw_name:
                raw_name = "Desconocido"

            # Capitalizar cada palabra (Title Case) para normalizar
            nombre_normalizado = raw_name.title()

            player_rows.append({
                'id': str(jugador_id),
                'equipo_id': str(equipo_id) if equipo_id else None,
                'nombre': nombre_normalizado
            })

        df_jugadores = pd.DataFrame(player_rows)
        # Eliminar duplicados en caso de que un jugador venga listado varias veces
        df_jugadores.drop_duplicates(subset=['id'], inplace=True)
        
        logger.info(f"Procesados {len(df_jugadores)} jugadores.")
        return df_jugadores

    def process_staff(self, raw_players: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extrae la lista del cuerpo técnico de las plantillas (convocadas).
        """
        if not raw_players:
            return pd.DataFrame(columns=[
                'id', 'equipo_id', 'nombre', 'rol'
            ])

        staff_rows = []
        people_entries = self._extract_people_entries(raw_players)

        for player in people_entries:
            is_ct = player.get('isCT', False)
            ct_role = player.get('ctRole')
            
            # Solo procesar si es parte del cuerpo técnico
            if not is_ct and ct_role is None:
                continue

            staff_id = player.get('id', self._generate_uuid())
            equipo_id = player.get('teamId')

            raw_name = player.get('name', '')
            if not raw_name:
                fall_first = player.get('firstName', '')
                fall_last = player.get('lastName', '')
                raw_name = f"{fall_first} {fall_last}".strip()
            
            if not raw_name:
                raw_name = "Desconocido"

            nombre_normalizado = raw_name.title()

            staff_rows.append({
                'id': str(staff_id),
                'equipo_id': str(equipo_id) if equipo_id else None,
                'nombre': nombre_normalizado,
                'rol': str(ct_role) if ct_role else "CT"
            })

        df_staff = pd.DataFrame(staff_rows)
        df_staff.drop_duplicates(subset=['id'], inplace=True)
        
        logger.info(f"Procesados {len(df_staff)} miembros del cuerpo técnico.")
        return df_staff

    def process_metadata(self, match_metadata: Dict[str, Any], match_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extrae y separa los datos para las tablas 'torneos' y 'partidos' desde el metadato del partido.
        Retorna una tupla de (df_torneos, df_partidos).
        """
        if not match_metadata:
            logger.warning(f"No hay metadata para el partido {match_id}. Se retornan DataFrames vacíos.")
            return (
                pd.DataFrame(columns=['id', 'nombre', 'temporada', 'pais']),
                pd.DataFrame(columns=[
                    'id', 'torneo_id', 'equipo_local_id', 'equipo_visitante_id', 
                    'fecha', 'jornada', 'goles_local', 'goles_visitante'
                ])
            )
            
        torneo_id = match_metadata.get('torneo_id', 'DESCONOCIDO')
        torneo_nombre = match_metadata.get('torneo_nombre', 'Torneo Desconocido')
        temporada = match_metadata.get('temporada', 'Desconocida')

        fecha_raw = match_metadata.get('fecha')
        equipo_local_id = match_metadata.get('equipo_local_id')
        equipo_visitante_id = match_metadata.get('equipo_visitante_id')

        if not fecha_raw or not equipo_local_id or not equipo_visitante_id:
            logger.warning(
                f"Metadata incompleta para el partido {match_id}. "
                "Se omite la carga del partido para evitar datos corruptos."
            )
            return (
                pd.DataFrame(columns=['id', 'nombre', 'temporada', 'pais']),
                pd.DataFrame(columns=[
                    'id', 'torneo_id', 'equipo_local_id', 'equipo_visitante_id',
                    'fecha', 'jornada', 'goles_local', 'goles_visitante'
                ])
            )
        
        df_torneos = pd.DataFrame([{
            'id': str(torneo_id),
            'nombre': str(torneo_nombre),
            'temporada': temporada,
            'pais': 'Argentina' # Defaulting as this scraper is for Mendoza
        }])
        
        # Convertimos la fecha JS ($D2024-...) a algo parseable por pandas/mysql
        fecha_str = str(fecha_raw).replace('$D', '').replace('T', ' ')[:19]
            
        df_partidos = pd.DataFrame([{
            'id': str(match_id),
            'torneo_id': str(torneo_id),
            'equipo_local_id': str(equipo_local_id),
            'equipo_visitante_id': str(equipo_visitante_id),
            'fecha': fecha_str,
            'jornada': match_metadata.get('jornada'),
            'goles_local': match_metadata.get('goles_local', 0),
            'goles_visitante': match_metadata.get('goles_visitante', 0)
        }])
        
        logger.info(f"Metadata procesada correctamente para el partido {match_id}.")
        return df_torneos, df_partidos
