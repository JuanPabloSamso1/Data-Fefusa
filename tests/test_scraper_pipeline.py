import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pandas as pd

import main
from src.processor import DataProcessor
from src.scraper import ScorefyScraper


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class TestScraperPipeline(unittest.TestCase):
    def test_get_fixture_urls_extracts_structured_matches_from_results_html(self):
        html = Path(__file__).with_name("test_html.txt").read_text(encoding="utf-8")
        scraper = ScorefyScraper()
        scraper.session.get = Mock(return_value=FakeResponse(html))

        fixture = scraper.get_fixture_urls("https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results")

        self.assertTrue(fixture)
        self.assertEqual(len({match["id"] for match in fixture}), len(fixture))

        regatas_match = next(match for match in fixture if match["id"] == "cmlmgwve10012p4zcskrr7o5j")
        self.assertEqual(regatas_match["data"]["round"], 1)
        self.assertEqual(regatas_match["data"]["tour_id"], "FFM-P-M-FSP-A-2026")
        self.assertEqual(regatas_match["data"]["teams"][0]["name"], "Regatas")
        self.assertEqual(regatas_match["data"]["teams"][1]["name"], "Independiente Rivadavia")
        self.assertEqual(regatas_match["data"]["dateOriginal"], "$D2026-02-28T00:30:00.000Z")

    def test_get_match_data_parses_nested_payloads_without_truncation(self):
        html = r"""
        <html>
        <head><title>FEFUSA Mendoza Primera Apertura 2026 Scoreboard - Futsal Mendoza - Scorefy</title></head>
        <body>
        <script>
        self.__next_f.push([1,"{\"initialFanLog\":[{\"id\":\"e1\",\"teamId\":\"home\",\"personId\":\"p1\",\"scoreTypeName\":\"Gol\",\"period\":\"1T\",\"minute\":1180}],\"convocadas\":[{\"id\":\"home\",\"players\":[{\"id\":\"p1\",\"teamId\":\"home\",\"name\":\"jugador uno\"}],\"staff\":[{\"id\":\"s1\",\"teamId\":\"home\",\"name\":\"dt local\",\"ctRole\":\"DT\"}]}],\"match\":{\"id\":\"m1\",\"round\":1,\"dateOriginal\":\"$D2026-02-28T00:30:00.000Z\",\"categoryName\":\"Primera\",\"divisionName\":\"FSP\",\"teams\":[{\"id\":\"home\",\"name\":\"Regatas\",\"goals\":3},{\"id\":\"away\",\"name\":\"Independiente Rivadavia\",\"goals\":3}]}}"])
        </script>
        </body>
        </html>
        """
        scraper = ScorefyScraper()
        scraper.session.get = Mock(return_value=FakeResponse(html))

        match_data = scraper.get_match_data("https://scorefy.app/cast/scoreboard/m1")

        self.assertEqual(len(match_data["initialFanLog"]), 1)
        self.assertEqual(match_data["initialFanLog"][0]["id"], "e1")
        self.assertEqual(len(match_data["convocadas"]), 1)
        self.assertEqual(match_data["convocadas"][0]["players"][0]["id"], "p1")
        self.assertEqual(match_data["matchFull"]["fecha"], "$D2026-02-28T00:30:00.000Z")
        self.assertEqual(match_data["matchFull"]["equipo_local_nombre"], "Regatas")
        self.assertEqual(match_data["matchFull"]["equipo_visitante_nombre"], "Independiente Rivadavia")

    def test_get_match_data_reads_convocadas_inside_matchfull_and_local_visitor_teams(self):
        html = r"""
        <html>
        <head><title>FEFUSA Mendoza Primera Apertura 2026 Scoreboard - Futsal Mendoza - Scorefy</title></head>
        <body>
        <script>
        self.__next_f.push([1,"{\"noise\":{\"initialFanLog\":\"skip\"},\"payload\":{\"initialFanLog\":[{\"id\":198105,\"playerId\":\"p1\",\"teamId\":\"home\",\"scoreTypeName\":\"Gol\",\"period\":1,\"minute\":1089}],\"matchFull\":{\"id\":\"m1\",\"tournamentId\":\"FFM-P-M-FSP-A-2026\",\"round\":1,\"categoryName\":\"Primera\",\"divisionName\":\"FSP\",\"date\":\"27/02\",\"startTime\":\"21:30\",\"localTeam\":{\"id\":\"home\",\"name\":\"Regatas\",\"goals\":3},\"visitorTeam\":{\"id\":\"away\",\"name\":\"Independiente Rivadavia\",\"goals\":3},\"convocadas\":[{\"id\":\"p1\",\"teamId\":\"home\",\"name\":\"Jugador Uno\",\"isCT\":false},{\"id\":\"s1\",\"teamId\":\"away\",\"name\":\"DT Visitante\",\"isCT\":true,\"ctRole\":\"DT\"}]}}}"])
        </script>
        </body>
        </html>
        """
        scraper = ScorefyScraper()
        scraper.session.get = Mock(return_value=FakeResponse(html))

        match_data = scraper.get_match_data("https://scorefy.app/cast/scoreboard/m1")

        self.assertEqual(len(match_data["initialFanLog"]), 1)
        self.assertEqual(len(match_data["convocadas"]), 2)
        self.assertEqual(match_data["matchFull"]["equipo_local_id"], "home")
        self.assertEqual(match_data["matchFull"]["equipo_visitante_id"], "away")
        self.assertEqual(match_data["matchFull"]["fecha"], "2026-02-27 21:30:00")

    def test_build_match_full_prefers_fixture_metadata_when_scoreboard_is_incomplete(self):
        scraper = ScorefyScraper()

        match_full = scraper._build_match_full(
            html="<title>FEFUSA Mendoza Primera Apertura 2026 Scoreboard</title>",
            url_partido="https://scorefy.app/cast/scoreboard/m1",
            match_payload={
                "categoryName": "Primera",
                "divisionName": "FSP",
                "dateOriginal": "",
                "teams": "$undefined",
            },
            fallback_data={
                "tour_id": "FFM-P-M-FSP-A-2026",
                "round": 1,
                "dateOriginal": "$D2026-02-28T00:30:00.000Z",
                "categoryName": "Primera",
                "divisionName": "FSP",
                "teams": [
                    {"id": "home", "name": "Regatas", "goals": 3},
                    {"id": "away", "name": "Independiente Rivadavia", "goals": 3},
                ],
            },
        )

        self.assertEqual(match_full["torneo_id"], "FFM-P-M-FSP-A-2026")
        self.assertEqual(match_full["fecha"], "$D2026-02-28T00:30:00.000Z")
        self.assertEqual(match_full["equipo_local_id"], "home")
        self.assertEqual(match_full["equipo_visitante_id"], "away")

    def test_get_fixture_urls_falls_back_to_regex_when_structured_match_is_incomplete(self):
        html = r"""
        <html>
        <body>
        <script>
        self.__next_f.push([1,"{\"match\":{\"id\":\"abc123\",\"teams\":[{\"id\":\"home\",\"name\":\"Regatas\"},{\"id\":\"away\",\"name\":\"Independiente Rivadavia\"}]},\"cards\":[{\"id\":\"abc123\",\"date\":\"28/2\",\"statusId\":57,\"hasPlayerScores\":true}]}"])
        </script>
        \"id\":\"abc123\",\"date\":\"28/2\",\"statusId\":57,\"hasPlayerScores\":true
        </body>
        </html>
        """
        scraper = ScorefyScraper()
        scraper.session.get = Mock(return_value=FakeResponse(html))

        fixture = scraper.get_fixture_urls("https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-P-M-FSP-A-2026/results")

        self.assertEqual(len(fixture), 1)
        self.assertEqual(fixture[0]["id"], "abc123")
        self.assertEqual(fixture[0]["data"]["teams"][0]["name"], "Regatas")

    def test_process_events_deduplicates_same_event_id_keeping_complete_row(self):
        processor = DataProcessor()
        raw_events = [
            {
                "id": "e1",
                "teamId": "home",
                "scoreTypeName": "Gol",
                "period": "1T",
                "minute": 1180,
            },
            {
                "id": "e1",
                "teamId": "home",
                "personId": "p1",
                "scoreTypeName": "Gol",
                "period": "1T",
                "minute": 1180,
            },
            {
                "id": "e2",
                "teamId": "away",
                "scoreTypeName": "Falta",
                "period": "2T",
                "minute": 300,
            },
        ]

        df = processor.process_events(raw_events, "m1")

        self.assertEqual(len(df), 2)
        event = df.loc[df["id"] == "e1"].iloc[0]
        self.assertEqual(event["persona_id"], "p1")
        self.assertEqual(event["equipo_id"], "home")

    def test_process_metadata_skips_incomplete_matches(self):
        processor = DataProcessor()

        df_torneos, df_partidos = processor.process_metadata(
            {
                "torneo_id": "FFM-P-M-FSP-A-2026",
                "torneo_nombre": "Primera FSP",
                "temporada": "Primera FSP - Apertura 2026",
            },
            "m1",
        )

        self.assertTrue(df_torneos.empty)
        self.assertTrue(df_partidos.empty)

    def test_append_deduped_csv_deduplicates_first_write_with_mixed_id_types(self):
        df = pd.DataFrame(
            [
                {"id": "1", "nombre": "Primero"},
                {"id": 1, "nombre": "Segundo"},
            ]
        )

        with TemporaryDirectory() as tmp_dir:
            with patch.object(main, "CSV_DIR", Path(tmp_dir)):
                main.append_deduped_csv(df, "eventos.csv", "id")
                stored = pd.read_csv(Path(tmp_dir) / "eventos.csv", dtype={"id": str})

        self.assertEqual(len(stored), 1)
        self.assertEqual(stored.iloc[0]["id"], "1")
        self.assertEqual(stored.iloc[0]["nombre"], "Segundo")


if __name__ == "__main__":
    unittest.main()
