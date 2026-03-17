import unittest

import pandas as pd

from dashboard import analytics


class TestDashboardAnalytics(unittest.TestCase):
    def setUp(self):
        self.partidos = pd.DataFrame(
            [
                {
                    "id": "m1",
                    "equipo_local": "A",
                    "equipo_visitante": "B",
                    "goles_local": 2,
                    "goles_visitante": 1,
                    "fecha": "2026-03-01 20:00:00",
                    "jornada": 1,
                },
                {
                    "id": "m2",
                    "equipo_local": "B",
                    "equipo_visitante": "C",
                    "goles_local": 1,
                    "goles_visitante": 2,
                    "fecha": "2026-03-08 20:00:00",
                    "jornada": 2,
                },
                {
                    "id": "m3",
                    "equipo_local": "A",
                    "equipo_visitante": "C",
                    "goles_local": 0,
                    "goles_visitante": 1,
                    "fecha": "2026-03-15 20:00:00",
                    "jornada": 3,
                },
            ]
        )
        self.eventos = pd.DataFrame(
            [
                {"id": "e1", "partido_id": "m1", "equipo": "A", "jugador": "P1", "persona_id": "p1", "tipo_evento": "Gol", "minuto": 0, "segundo": 0, "periodo": "1"},
                {"id": "e2", "partido_id": "m1", "equipo": "A", "jugador": "P1", "persona_id": "p1", "tipo_evento": "Falta", "minuto": 5, "segundo": 0, "periodo": "1"},
                {"id": "e3", "partido_id": "m1", "equipo": "A", "jugador": "P1", "persona_id": "p1", "tipo_evento": "Amarilla", "minuto": 5, "segundo": 10, "periodo": "1"},
                {"id": "e4", "partido_id": "m1", "equipo": "A", "jugador": "P2", "persona_id": "p2", "tipo_evento": "Falta", "minuto": 20, "segundo": 0, "periodo": "2"},
                {"id": "e5", "partido_id": "m1", "equipo": "B", "jugador": "P3", "persona_id": "p3", "tipo_evento": "Gol", "minuto": 35, "segundo": 0, "periodo": "2"},
                {"id": "e6", "partido_id": "m1", "equipo": "B", "jugador": "P3", "persona_id": "p3", "tipo_evento": "Falta", "minuto": 40, "segundo": 0, "periodo": "2"},
                {"id": "e7", "partido_id": "m2", "equipo": "B", "jugador": "P3", "persona_id": "p3", "tipo_evento": "Gol", "minuto": 10, "segundo": 0, "periodo": "1"},
                {"id": "e8", "partido_id": "m2", "equipo": "C", "jugador": "P4", "persona_id": "p4", "tipo_evento": "Gol", "minuto": 15, "segundo": 0, "periodo": "1"},
                {"id": "e9", "partido_id": "m2", "equipo": "C", "jugador": "P4", "persona_id": "p4", "tipo_evento": "Gol", "minuto": 25, "segundo": 0, "periodo": "2"},
                {"id": "e10", "partido_id": "m2", "equipo": "B", "jugador": "P3", "persona_id": "p3", "tipo_evento": "Roja", "minuto": 30, "segundo": 0, "periodo": "2"},
                {"id": "e11", "partido_id": "m3", "equipo": "C", "jugador": "P4", "persona_id": "p4", "tipo_evento": "Gol", "minuto": 39, "segundo": 0, "periodo": "2"},
                {"id": "e12", "partido_id": "m3", "equipo": "A", "jugador": "P1", "persona_id": "p1", "tipo_evento": "Falta", "minuto": 20, "segundo": 0, "periodo": "2"},
                {"id": "e13", "partido_id": "m1", "equipo": "A", "jugador": "P2", "persona_id": "p2", "tipo_evento": "Penal Gol", "minuto": 18, "segundo": 0, "periodo": "1"},
                {"id": "e14", "partido_id": "m1", "equipo": "A", "jugador": "P2", "persona_id": "p2", "tipo_evento": "Penal Gol", "minuto": 40, "segundo": 0, "periodo": "5"},
            ]
        )
        self.eventos["jornada"] = self.eventos["partido_id"].map({"m1": 1, "m2": 2, "m3": 3})

    def test_minute_to_bucket_boundaries(self):
        self.assertEqual(analytics.minute_to_bucket(0), "0-5'")
        self.assertEqual(analytics.minute_to_bucket(5), "5-10'")
        self.assertEqual(analytics.minute_to_bucket(20), "20-25'")
        self.assertEqual(analytics.minute_to_bucket(40), "35-40'")

    def test_build_egr_table_orders_best_team_first(self):
        egr = analytics.build_egr_table(self.partidos)
        self.assertEqual(egr.iloc[0]["Equipo"], "C")
        self.assertAlmostEqual(float(egr.iloc[0]["EGR"]), 128.6, places=1)

    def test_build_team_discipline_applies_ipd_weights(self):
        team_disc = analytics.build_team_discipline(self.eventos, self.partidos)
        row_b = team_disc[team_disc["Equipo"] == "B"].iloc[0]
        self.assertAlmostEqual(float(row_b["IPD"]), 1.6, places=2)
        self.assertEqual(row_b["Riesgo"], "Medio")

    def test_build_team_profile_returns_summary_and_momentum(self):
        profile = analytics.build_team_profile(self.eventos, self.partidos, "A")
        self.assertEqual(profile["summary"]["pts"], 3)
        self.assertEqual(profile["summary"]["gf"], 2)
        self.assertNotIn("splits", profile)
        self.assertEqual(profile["per_match"]["Indicador"].tolist(), ["GF por partido", "GC por partido", "PTS por partido", "Diferencia por partido"])
        self.assertFalse(profile["momentum"].empty)

    def test_build_match_selector_orders_latest_match_first(self):
        selector = analytics.build_match_selector(self.partidos)
        self.assertEqual(selector.iloc[0]["id"], "m3")
        self.assertIn("A 0-1 C", selector.iloc[0]["label"])

    def test_build_match_dataset_splits_goals_by_period(self):
        dataset = analytics.build_match_dataset(self.eventos, self.partidos, "m1")
        periods = dataset["period_summary"]
        first_half = periods[(periods["Periodo"] == "1T") & (periods["Equipo"] == "A")]
        second_half_b = periods[(periods["Periodo"] == "2T") & (periods["Equipo"] == "B")]
        self.assertEqual(int(first_half.iloc[0]["Goles"]), 2)
        self.assertEqual(int(second_half_b.iloc[0]["Goles"]), 1)
        self.assertEqual(int(periods["Goles"].sum()), 3)
        self.assertEqual(int(dataset["non_regular_goal_events"]), 1)

    def test_goal_events_excludes_shootout_penalties_by_default(self):
        regular_goals = analytics.goal_events(self.eventos)
        all_goals = analytics.goal_events(self.eventos, include_non_regular_periods=True)
        self.assertEqual(len(all_goals) - len(regular_goals), 1)
        self.assertFalse((regular_goals["periodo"].astype(str) == "5").any())

    def test_build_player_comparison_returns_table_and_radar(self):
        comparison = analytics.build_player_comparison(self.eventos, "p1", "p4")
        self.assertIn("P1", comparison["label_a"])
        self.assertIn("P4", comparison["label_b"])
        self.assertEqual(set(comparison["radar"]["Metrica"]), {"Goles", "Partidos", "Gol/Partido", "IPD", "Faltas"})
        self.assertEqual(len(comparison["table"]), 5)


if __name__ == "__main__":
    unittest.main()
