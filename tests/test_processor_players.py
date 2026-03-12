import unittest

from src.processor import DataProcessor


class TestDataProcessorPlayers(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()

    def test_process_players_extracts_all_players_from_nested_convocadas(self):
        raw_players = [
            {
                "teamId": "home",
                "starters": [
                    {"id": "p1", "teamId": "home", "name": "jugador uno", "isCT": False},
                    {"id": "p2", "teamId": "home", "name": "jugador dos", "isCT": False},
                ],
                "substitutes": [
                    {"id": "p3", "teamId": "home", "name": "jugador tres", "isCT": False}
                ],
                "staff": [
                    {"id": "s1", "teamId": "home", "name": "dt local", "isCT": True, "ctRole": "DT"}
                ],
            },
            {
                "teamId": "away",
                "players": [
                    {"id": "p4", "teamId": "away", "firstName": "jugador", "lastName": "cuatro"},
                    {"id": "p5", "teamId": "away", "name": "jugador cinco"},
                ],
                "staff": [
                    {"id": "s2", "teamId": "away", "name": "ayudante", "ctRole": "AT"}
                ],
            },
        ]

        df = self.processor.process_players(raw_players)

        ids = set(df["id"].tolist())
        self.assertEqual(ids, {"p1", "p2", "p3", "p4", "p5"})
        self.assertNotIn("s1", ids)
        self.assertNotIn("s2", ids)

    def test_process_staff_extracts_only_staff_from_nested_convocadas(self):
        raw_players = [
            {
                "players": [
                    {"id": "p1", "teamId": "home", "name": "jugador uno", "isCT": False},
                ],
                "staff": [
                    {"id": "s1", "teamId": "home", "name": "dt local", "isCT": True, "ctRole": "DT"}
                ],
            }
        ]

        df = self.processor.process_staff(raw_players)
        ids = set(df["id"].tolist())

        self.assertEqual(ids, {"s1"})
        self.assertNotIn("p1", ids)


if __name__ == "__main__":
    unittest.main()
