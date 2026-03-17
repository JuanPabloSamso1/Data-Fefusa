import unittest

import pandas as pd

from dashboard.data_loader import _normalize_events_frame


class TestDataLoader(unittest.TestCase):
    def test_normalize_events_frame_deduplicates_same_event_id(self):
        eventos = pd.DataFrame(
            [
                {
                    "id": "e1",
                    "partido_id": "m1",
                    "equipo_id": "team-a",
                    "jugador_id": "p1",
                    "persona_id": None,
                    "tipo_evento": "Gol",
                    "minuto": 3,
                    "segundo": 12,
                    "periodo": "1",
                },
                {
                    "id": "e1",
                    "partido_id": "m1",
                    "equipo_id": "team-a",
                    "jugador_id": None,
                    "persona_id": "p1",
                    "tipo_evento": "Gol",
                    "minuto": 3,
                    "segundo": 12,
                    "periodo": "1",
                },
                {
                    "id": "e2",
                    "partido_id": "m1",
                    "equipo_id": "team-b",
                    "jugador_id": None,
                    "persona_id": "p2",
                    "tipo_evento": "Falta",
                    "minuto": 5,
                    "segundo": 0,
                    "periodo": "1",
                },
            ]
        )

        normalized = _normalize_events_frame(eventos)

        self.assertEqual(len(normalized), 2)
        goal_row = normalized[normalized["id"] == "e1"].iloc[0]
        self.assertEqual(goal_row["persona_id"], "p1")
        self.assertEqual(goal_row["jugador_id"], "p1")


if __name__ == "__main__":
    unittest.main()
