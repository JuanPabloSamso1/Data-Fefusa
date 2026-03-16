import unittest
from unittest.mock import MagicMock

import pandas as pd

from src.processor import DataProcessor
from src.db_manager import MySQLManager


class TestEventosConPersonas(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()

    def test_evento_con_persona_ct(self):
        raw_events = [{
            "id": "ev-ct-1",
            "teamId": "team-1",
            "personId": "ct-1",
            "scoreTypeName": "Tarjeta Azul",
            "minute": 1190,
            "period": "1T",
        }]

        df = self.processor.process_events(raw_events, match_id="match-1")

        self.assertEqual(df.iloc[0]["persona_id"], "ct-1")
        self.assertEqual(df.iloc[0]["tipo_evento"], "Tarjeta Azul")

    def test_evento_con_persona_jugador(self):
        raw_events = [{
            "id": "ev-j-1",
            "teamId": "team-1",
            "playerId": "jug-1",
            "scoreTypeName": "Gol",
            "minute": 1180,
            "period": "1T",
        }]

        df = self.processor.process_events(raw_events, match_id="match-1")

        self.assertEqual(df.iloc[0]["persona_id"], "jug-1")
        self.assertEqual(df.iloc[0]["tipo_evento"], "Gol")


class TestPersistenciaEventosPersonas(unittest.TestCase):
    def test_insert_events_con_persona_id(self):
        manager = MySQLManager()

        cursor = MagicMock()
        connection = MagicMock()
        connection.cursor.return_value = cursor

        manager.connect = MagicMock()
        manager.connection = connection

        df_eventos = pd.DataFrame([
            {
                "id": "ev-1",
                "partido_id": "m-1",
                "equipo_id": "t-1",
                "persona_id": "ct-1",
                "tipo_evento": "Tarjeta Roja",
                "minuto": 5,
                "segundo": 0,
                "periodo": "1T",
            },
            {
                "id": "ev-2",
                "partido_id": "m-1",
                "equipo_id": "t-1",
                "persona_id": "jug-1",
                "tipo_evento": "Gol",
                "minuto": 8,
                "segundo": 30,
                "periodo": "1T",
            },
        ])

        manager.insert_events(df_eventos, batch_size=100)

        executed_query = cursor.executemany.call_args[0][0]
        records = cursor.executemany.call_args[0][1]

        self.assertIn("persona_id", executed_query)
        self.assertEqual(records[0][3], "ct-1")
        self.assertEqual(records[1][3], "jug-1")
        connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
