import os
import logging
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class MySQLManager:
    """
    Clase encargada de manejar la conexión a la base de datos MySQL,
    las transacciones y las inserciones por lotes (Batch Processing) con UPSERT.
    """

    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '3306')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', 'secret')
        self.database = os.getenv('DB_NAME', 'futsal_analytics')
        self.connection = None

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                logger.info("Conexión a MySQL establecida exitosamente.")
        except Error as e:
            logger.error(f"Error al conectar a MySQL: {e}")
            raise

    def close(self):
        """Cierra la conexión con la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión a MySQL cerrada.")

    def upsert_equipos(self, df_equipos: pd.DataFrame):
        """
        Inserta equipos y actualiza si ya existen (UPSERT).
        """
        if df_equipos.empty:
            return

        self.connect()
        cursor = self.connection.cursor()
        
        query = """
            INSERT INTO equipos (id, nombre)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                nombre = VALUES(nombre)
        """
        
        # Filtramos columnas que existen y reemplazamos NaNs por None (NULL en base de datos)
        # Asume que si no traemos ciudad/estadio todavía, no los rompemos
        cols = ['id', 'nombre']
        records = df_equipos[cols].where(pd.notnull(df_equipos[cols]), None).values.tolist()

        try:
            cursor.executemany(query, records)
            self.connection.commit()
            logger.info(f"UPSERT exitoso para {len(records)} equipos.")
        except Error as e:
            logger.error(f"Error al hacer UPSERT en equipos: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def upsert_torneos(self, df_torneos: pd.DataFrame):
        """
        Inserta o actualiza Torneos en la BD.
        """
        if df_torneos.empty: return

        self.connect()
        cursor = self.connection.cursor()
        query = """
            INSERT INTO torneos (id, nombre, temporada, pais)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nombre = VALUES(nombre),
                temporada = VALUES(temporada),
                pais = VALUES(pais)
        """
        cols = ['id', 'nombre', 'temporada', 'pais']
        records = df_torneos[cols].where(pd.notnull(df_torneos[cols]), None).values.tolist()

        try:
            cursor.executemany(query, records)
            self.connection.commit()
            logger.info(f"UPSERT exitoso para {len(records)} torneos.")
        except Error as e:
            logger.error(f"Error al hacer UPSERT en torneos: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def upsert_partidos(self, df_partidos: pd.DataFrame):
        """
        Inserta o actualiza Partidos en la BD.
        """
        if df_partidos.empty: return

        self.connect()
        cursor = self.connection.cursor()
        query = """
            INSERT INTO partidos (id, torneo_id, equipo_local_id, equipo_visitante_id, 
                                fecha, jornada, goles_local, goles_visitante)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                torneo_id = VALUES(torneo_id),
                equipo_local_id = VALUES(equipo_local_id),
                equipo_visitante_id = VALUES(equipo_visitante_id),
                fecha = VALUES(fecha),
                jornada = VALUES(jornada),
                goles_local = VALUES(goles_local),
                goles_visitante = VALUES(goles_visitante)
        """
        cols = ['id', 'torneo_id', 'equipo_local_id', 'equipo_visitante_id', 
                'fecha', 'jornada', 'goles_local', 'goles_visitante']
        records = df_partidos[cols].where(pd.notnull(df_partidos[cols]), None).values.tolist()

        try:
            cursor.executemany(query, records)
            self.connection.commit()
            logger.info(f"UPSERT exitoso para {len(records)} partidos.")
        except Error as e:
            logger.error(f"Error al hacer UPSERT en partidos: {e}")
            self.connection.rollback()
        finally:
            cursor.close()


    def upsert_personas(self, df_personas: pd.DataFrame):
        """
        Inserta o actualiza personas unificadas (jugadores y cuerpo técnico).
        """
        if df_personas.empty:
            return

        self.connect()
        cursor = self.connection.cursor()

        query = """
            INSERT INTO personas (id, equipo_id, nombre, tipo_persona, rol_ct)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                equipo_id = VALUES(equipo_id),
                nombre = VALUES(nombre),
                tipo_persona = VALUES(tipo_persona),
                rol_ct = VALUES(rol_ct)
        """

        cols = ['id', 'equipo_id', 'nombre', 'tipo_persona', 'rol_ct']
        records = df_personas[cols].where(pd.notnull(df_personas[cols]), None).values.tolist()

        try:
            cursor.executemany(query, records)
            self.connection.commit()
            logger.info(f"UPSERT exitoso para {len(records)} personas.")
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error haciendo UPSERT en personas: {e}")
            raise
        finally:
            cursor.close()

    def upsert_jugadores(self, df_jugadores: pd.DataFrame):
        """
        Compatibilidad: mapea jugadores al modelo unificado de personas.
        """
        if df_jugadores.empty:
            return

        df_personas = df_jugadores.copy()
        df_personas['tipo_persona'] = 'JUGADOR'
        df_personas['rol_ct'] = None
        self.upsert_personas(df_personas[['id', 'equipo_id', 'nombre', 'tipo_persona', 'rol_ct']])


    def upsert_staff(self, df_staff: pd.DataFrame):
        """
        Compatibilidad: mapea cuerpo técnico al modelo unificado de personas.
        """
        if df_staff.empty:
            return

        df_personas = df_staff.rename(columns={'rol': 'rol_ct'}).copy()
        df_personas['tipo_persona'] = 'CT'
        self.upsert_personas(df_personas[['id', 'equipo_id', 'nombre', 'tipo_persona', 'rol_ct']])


    def insert_events(self, df_eventos: pd.DataFrame, batch_size: int = 500):
        """
        Inserta eventos usando Batch Processing para evitar errores de 
        'max_allowed_packet' de MySQL, garantizando transacciones atómicas.
        """
        if df_eventos.empty:
            return

        self.connect()
        cursor = self.connection.cursor()

        query = """
            INSERT INTO eventos (id, partido_id, equipo_id, persona_id, tipo_evento, 
                                minuto, segundo, periodo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                partido_id = VALUES(partido_id),
                equipo_id = VALUES(equipo_id),
                persona_id = VALUES(persona_id),
                tipo_evento = VALUES(tipo_evento),
                minuto = VALUES(minuto),
                segundo = VALUES(segundo),
                periodo = VALUES(periodo)
        """
        
        cols = ['id', 'partido_id', 'equipo_id', 'persona_id', 'tipo_evento', 
                'minuto', 'segundo', 'periodo']
        
        # Convertimos NaNs de Pandas a Nones nativos (NULL SQL)
        records = df_eventos[cols].where(pd.notnull(df_eventos[cols]), None).values.tolist()
        total_records = len(records)
        inserted = 0

        # Transacción Atómica para garantizar la consistencia relacional de un partido
        try:
            # Procesamiento por Lotes (Batches)
            for i in range(0, total_records, batch_size):
                batch = records[i:i + batch_size]
                cursor.executemany(query, batch)
                inserted += len(batch)
                logger.debug(f"Insertado lote de {len(batch)} eventos... Progreso: {inserted}/{total_records}")

            # Solo hacemos commit si TODOS los lotes se insertaron correctamente
            self.connection.commit()
            logger.info(f"Se insertaron/actualizaron {total_records} eventos en total en lotes de {batch_size}.")

        except Error as e:
            # Rollback Atómico deshace todo el progreso para mantener consistencia de este partido completo
            self.connection.rollback()
            logger.error(f"Error fatal ingresando eventos. Falló en lote index={i}. Se aplicó ROLLBACK absoluto: {e}")
            raise
        finally:
            cursor.close()
