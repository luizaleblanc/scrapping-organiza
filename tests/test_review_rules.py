import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config
import review_redaction as redaction


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sentiment = load_script("filter_sentiment", "06_filter_sentiment.py")
# The public script imports step 7 for its brand pattern. Stub that module so
# importing the check cannot inspect any project data files.
sys.modules["07_build_ai_share"] = types.SimpleNamespace(BRANDS=None)
public = load_script("build_public_criticas", "08b_build_public_criticas.py")


class SentimentRulesTests(unittest.TestCase):
    def test_protocol_cutoff_keeps_negative_and_neutral_but_not_positive_boundary(self):
        cutoff = config.POSITIVE_COMPOUND
        compounds = [-1.0, 0.0, cutoff - 0.0001, cutoff, cutoff + 0.0001, 1.0]
        retained = [value for value in compounds if value < config.POSITIVE_COMPOUND]
        self.assertEqual(retained, [-1.0, 0.0, cutoff - 0.0001])

    def test_preprocess_removes_empty_short_and_exact_duplicates_keeping_oldest(self):
        import pandas as pd
        rows = pd.DataFrame([
            {"app_mask_id": "APP_001", "score": 1, "lang": "pt", "at": "2026-01-01", "content": ""},
            {"app_mask_id": "APP_001", "score": 1, "lang": "pt", "at": "2026-01-02", "content": "   "},
            {"app_mask_id": "APP_001", "score": 1, "lang": "pt", "at": "2026-01-03", "content": "app muito ruim"},
            {"app_mask_id": "APP_001", "score": 1, "lang": "pt", "at": "2026-01-05", "content": "App cobra   sem avisar antes"},
            {"app_mask_id": "APP_001", "score": 2, "lang": "pt", "at": "2026-01-04", "content": "app cobra sem avisar antes"},
            {"app_mask_id": "APP_001", "score": 1, "lang": "pt", "at": "2026-01-06", "content": "Não consigo cancelar a assinatura"},
        ])
        cleaned, steps = sentiment.preprocess(rows)
        self.assertEqual(steps, {
            "n0_collected": 6,
            "removed_empty": 2,
            "removed_short_le_3_words": 1,
            "removed_exact_duplicates": 1,
            "n1_after_preprocessing": 2,
        })
        self.assertEqual(cleaned["at"].tolist(), ["2026-01-04", "2026-01-06"])
        self.assertEqual(
            cleaned["content_clean"].tolist(),
            ["app cobra sem avisar antes", "não consigo cancelar a assinatura"],
        )

    def test_main_filters_score_sentiment_spanish_labels_and_preprocessing(self):
        import pandas as pd
        from unittest.mock import MagicMock
        rows = pd.DataFrame([
            {"score": 3, "lang": "en", "at": "2026-01-01", "content": "this app is very negative", "app_mask_id": "APP_001"},
            {"score": 3, "lang": "en", "at": "2026-01-02", "content": "this app is totally neutral", "app_mask_id": "APP_001"},
            {"score": 3, "lang": "en", "at": "2026-01-03", "content": "this app hits positive boundary", "app_mask_id": "APP_001"},
            {"score": 4, "lang": "en", "at": "2026-01-04", "content": "low sentiment but high score", "app_mask_id": "APP_001"},
            {"score": 5, "lang": "en", "at": "2026-01-05", "content": "high score and great app", "app_mask_id": "APP_001"},
            {"score": 2, "lang": "en", "at": "2026-01-06", "content": "", "app_mask_id": "APP_001"},
            {"score": 2, "lang": "en", "at": "2026-01-07", "content": "too short review", "app_mask_id": "APP_001"},
            {"score": 3, "lang": "es", "at": "2026-01-08", "content": "esta app es muy negativa", "app_mask_id": "APP_001"},
            {"score": 3, "lang": "es", "at": "2026-01-09", "content": "esta app es totalmente neutra", "app_mask_id": "APP_001"},
            {"score": 3, "lang": "es", "at": "2026-01-10", "content": "esta app es muy positiva", "app_mask_id": "APP_001"},
        ])
        fake_path = MagicMock()
        fake_path.exists.return_value = True
        missing_path = MagicMock()
        missing_path.exists.return_value = False
        analyzers = {
            "this app is very negative": -0.2,
            "this app is totally neutral": 0.0,
            "this app hits positive boundary": config.POSITIVE_COMPOUND,
            "low sentiment but high score": -0.5,
            "high score and great app": 0.8,
        }
        analyzer = MagicMock()
        analyzer.polarity_scores.side_effect = lambda text: {"compound": analyzers[text]}
        spanish = MagicMock()
        spanish.predict.return_value = [
            types.SimpleNamespace(output="NEG", probas={"POS": 0.1, "NEG": 0.8}),
            types.SimpleNamespace(output="NEU", probas={"POS": 0.2, "NEG": 0.2}),
            types.SimpleNamespace(output="POS", probas={"POS": 0.8, "NEG": 0.1}),
        ]
        leia = types.ModuleType("leia")
        leia.SentimentIntensityAnalyzer = MagicMock(return_value=analyzer)
        paths = {"reviews": fake_path, "critical": Path("critical.csv"),
                 "as_reviews": missing_path, "as_critical": Path("as_critical.csv")}
        saved = {}
        metrics = {}
        with patch.dict(sys.modules, {"leia": leia}), \
             patch.object(sentiment.C, "PATHS", paths), \
             patch.object(sentiment.pd, "read_csv", return_value=rows), \
             patch.object(sentiment, "SentimentIntensityAnalyzer", return_value=analyzer), \
             patch.object(sentiment, "spanish_analyzer", return_value=spanish), \
             patch.object(sentiment, "write_csv", side_effect=lambda df, path: saved.update({Path(path).name: df.copy()})), \
             patch.object(sentiment, "update_metrics", side_effect=lambda k, v: metrics.update({k: v})):
            sentiment.main()
        result = saved["critical.csv"]
        self.assertEqual(
            result.content.tolist(),
            [
                "this app is very negative",
                "this app is totally neutral",
                "esta app es muy negativa",
                "esta app es totalmente neutra",
            ],
        )
        self.assertEqual(
            spanish.predict.call_args.args[0],
            ["esta app es muy negativa", "esta app es totalmente neutra", "esta app es muy positiva"],
        )
        self.assertEqual(metrics["06_sentiment_google_play"]["preprocessing"]["n0_collected"], 10)
        self.assertEqual(metrics["06_sentiment_google_play"]["preprocessing"]["removed_empty"], 1)
        self.assertEqual(metrics["06_sentiment_google_play"]["preprocessing"]["removed_short_le_3_words"], 1)
        self.assertEqual(metrics["06_sentiment_google_play"]["preprocessing"]["n1_after_preprocessing"], 8)
        self.assertEqual(metrics["06_sentiment_google_play"]["stars_only_le_3"], 6)
        self.assertEqual(metrics["06_sentiment_google_play"]["critical_reviews"], 4)


class RedactionTests(unittest.TestCase):
    def test_redact_text_removes_identifiers_and_keeps_date_and_money(self):
        text = "Fale com ana@example.com, https://exemplo.com, CPF 123.456.789-00, telefone 11 98765-4321, @luiza; meu nome \u00e9 Fulano de Tal e meu nome e CPF."
        counters = {}
        result = redaction.redact_text(text, counters)
        for marker in ("[EMAIL]", "[URL]", "[CPF]", "[PHONE]", "[HANDLE]", "[NOME]"):
            self.assertIn(marker, result)
        self.assertIn("meu nome e CPF", result)
        self.assertNotIn("Fulano", result)
        self.assertEqual(counters["email"], 1)
        self.assertEqual(counters["url"], 1)
        self.assertEqual(counters["cpf"], 1)
        self.assertEqual(counters["phone"], 1)
        self.assertEqual(counters["handle"], 1)
        self.assertEqual(counters["name"], 1)

    def test_redact_text_handles_nulls_and_ambiguous_numbers(self):
        self.assertEqual(redaction.redact_text(None), "")
        self.assertIn("[POSSIBLE_PHONE_OR_NUMBER]", redaction.redact_text("meu número 123456789"))

    def test_redact_person_names_and_organizations_with_stub_ner(self):
        text = "Carlos gostou do Mobills"
        def fake_ner(_texts, batch_size=32):
            return [[
                {"start": 0, "end": 6, "entity_group": "PER", "score": 0.99},
                {"start": 19, "end": 26, "entity_group": "ORG", "score": 0.95},
            ]]
        redaction._ner = fake_ner
        self.addCleanup(setattr, redaction, "_ner", None)
        counters = {}
        result = redaction.redact_person_names([text], counters)
        self.assertEqual(result, ["[NOME] gostou do [MARCA]"])
        self.assertEqual(counters["person_name"], 1)
        self.assertEqual(counters["other_brand"], 1)

    def test_redact_brands_is_case_and_accent_insensitive_and_respects_word_boundaries(self):
        pattern = redaction.brand_regex({"Mobills", "Financas Ja"})
        counters = {}
        result = redaction.redact_brands(["MOBILLS ajuda; financas-ja tambem. mobillsx fica."], pattern, counters)
        self.assertEqual(result, ["[APP] ajuda; [APP] tambem. mobillsx fica."])
        self.assertEqual(counters["app_brand"], 2)

    def test_generic_brand_terms_are_not_redacted(self):
        pattern = redaction.brand_regex({"Mobills", "era", "wallet"})
        self.assertEqual(redaction.redact_brands(["Mobills era wallet"], pattern), ["[APP] era wallet"])
        self.assertTrue({"era", "wallet"}.issubset(redaction.GENERIC_BRANDS))

    def test_person_name_span_expansion_never_leaves_partial_word(self):
        text = "atendimento"
        redaction._ner = lambda _texts, batch_size=32: [[
            {"start": 0, "end": 5, "entity_group": "PER", "score": 0.99},
        ]]
        self.addCleanup(setattr, redaction, "_ner", None)
        self.assertEqual(redaction.redact_person_names([text]), ["[NOME]"])


class PublicCheckTests(unittest.TestCase):
    def setUp(self):
        self.brand_patch = patch.object(public, "BRANDS", None)
        self.brand_patch.start()
        self.addCleanup(self.brand_patch.stop)

    @staticmethod
    def frame(content="texto seguro", at="2024-01-02"):
        import pandas as pd
        return pd.DataFrame([{"content": content, "at": at}])

    def test_accepts_clean_redacted_row(self):
        public.check(self.frame(), "teste")

    def test_rejects_remaining_app_brand(self):
        with patch.object(public, "BRANDS", redaction.brand_regex({"Mobills"})):
            with self.assertRaisesRegex(SystemExit, "marca de app"):
                public.check(self.frame("Mobills é bom"), "teste")

    def test_rejects_personal_identifiers(self):
        for text, expected in (("contato ana@example.com", "email"), ("visite https://example.com", "url"),
                               ("fale com @luiza", "handle"),
                               ("meu numero 11 98765-4321", "cpf_ou_telefone"),
                               ("CPF 123.456.789-00", "cpf_ou_telefone")):
            with self.subTest(expected=expected), self.assertRaisesRegex(SystemExit, expected):
                public.check(self.frame(text), "teste")

    def test_rejects_datetime(self):
        with self.assertRaisesRegex(SystemExit, "data com hora"):
            public.check(self.frame(at="2024-01-02 10:30:00"), "teste")


if __name__ == "__main__":
    unittest.main()
