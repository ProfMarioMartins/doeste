#!/usr/bin/env python3
"""Linguistic and corpus regressions for DOESTE-PT sentence segmentation."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parents[1] / "pipeline"))
from annotate_tek import (  # noqa: E402
    ConlluRow,
    OrthographicToken,
    repair_embedded_terminal_tokens,
    segment_tokens,
    surface_text,
)

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI}


def tokens_from_forms(text: str, forms: list[str]) -> list[OrthographicToken]:
    """Create aligned surface tokens without invoking the remote UDPipe API."""

    tokens: list[OrthographicToken] = []
    cursor = 0
    for identifier, form in enumerate(forms, 1):
        start = text.index(form, cursor)
        end = start + len(form)
        row = ConlluRow([str(identifier), form, "_", "_", "_", "_", "_", "_", "_", f"TokenRange={start}:{end}"])
        tokens.append(OrthographicToken(form, start, end, None, [row]))
        cursor = end
    return tokens


def segmented_surface(text: str, forms: list[str]) -> list[str]:
    groups = segment_tokens(text, tokens_from_forms(text, forms))
    return [text[group[0].start:group[-1].end] for group in groups]


class PortugueseSegmentationTests(unittest.TestCase):
    def assert_embedded_repair(self, form: str, expected: list[str]) -> None:
        tokens = tokens_from_forms(form, [form])
        repaired = repair_embedded_terminal_tokens(form, tokens)
        self.assertEqual([token.form for token in repaired], expected)
        self.assertEqual("".join(token.form for token in repaired), form)
        self.assertEqual([(token.start, token.end) for token in repaired], [
            (sum(len(part) for part in expected[:index]), sum(len(part) for part in expected[:index + 1]))
            for index in range(len(expected))
        ])

    def test_repairs_embedded_full_stop(self) -> None:
        self.assert_embedded_repair("palavra.Palavra", ["palavra", ".", "Palavra"])

    def test_repairs_embedded_exclamation(self) -> None:
        self.assert_embedded_repair("palavra!Palavra", ["palavra", "!", "Palavra"])

    def test_repairs_embedded_question(self) -> None:
        self.assert_embedded_repair("palavra?Palavra", ["palavra", "?", "Palavra"])

    def test_does_not_split_decimal(self) -> None:
        self.assert_embedded_repair("3.14", ["3.14"])

    def test_does_not_split_url(self) -> None:
        self.assert_embedded_repair("https://exemplo.com/Arquivo", ["https://exemplo.com/Arquivo"])

    def test_does_not_split_email(self) -> None:
        self.assert_embedded_repair("nome.sobrenome@exemplo.com", ["nome.sobrenome@exemplo.com"])

    def test_does_not_split_abbreviation(self) -> None:
        self.assert_embedded_repair("prof.Silva", ["prof.Silva"])

    def test_does_not_split_initial(self) -> None:
        self.assert_embedded_repair("A.Silva", ["A.Silva"])

    def test_does_not_split_nonterminal_period(self) -> None:
        for form in ("arquivo.txt", "versão2.0", "palavra.seguinte"):
            with self.subTest(form=form):
                self.assert_embedded_repair(form, [form])

    def test_quoted_title_with_question_mark_is_embedded(self) -> None:
        text = "O filme “Que horas ela volta?” retrata o Brasil. Depois, conclui."
        forms = ["O", "filme", "“", "Que", "horas", "ela", "volta", "?", "”", "retrata", "o", "Brasil", ".", "Depois", ",", "conclui", "."]
        self.assertEqual(segmented_surface(text, forms), ["O filme “Que horas ela volta?” retrata o Brasil.", "Depois, conclui."])

    def test_quoted_title_with_exclamation_and_comma_is_embedded(self) -> None:
        text = "A obra “Pare!” , segundo a crítica, é relevante."
        forms = ["A", "obra", "“", "Pare", "!", "”", ",", "segundo", "a", "crítica", ",", "é", "relevante", "."]
        self.assertEqual(len(segmented_surface(text, forms)), 1)

    def test_direct_quote_after_colon_is_not_split_at_colon(self) -> None:
        text = "A autora afirmou: “A educação transforma”. A tese permanece."
        forms = ["A", "autora", "afirmou", ":", "“", "A", "educação", "transforma", "”", ".", "A", "tese", "permanece", "."]
        self.assertEqual(segmented_surface(text, forms), ["A autora afirmou: “A educação transforma”.", "A tese permanece."])

    def test_abbreviation_does_not_split(self) -> None:
        text = "O prof. Silva apresentou a proposta. Depois, saiu."
        forms = ["O", "prof", ".", "Silva", "apresentou", "a", "proposta", ".", "Depois", ",", "saiu", "."]
        self.assertEqual(segmented_surface(text, forms), ["O prof. Silva apresentou a proposta.", "Depois, saiu."])

    def test_period_without_space_still_splits(self) -> None:
        text = "A democracia.Em uma análise, isso importa."
        forms = ["A", "democracia", ".", "Em", "uma", "análise", ",", "isso", "importa", "."]
        self.assertEqual(segmented_surface(text, forms), ["A democracia.", "Em uma análise, isso importa."])

    def test_closing_quote_is_kept_with_finished_sentence(self) -> None:
        text = "Ela disse “Isso basta.” Depois, partiu."
        forms = ["Ela", "disse", "“", "Isso", "basta", ".", "”", "Depois", ",", "partiu", "."]
        self.assertEqual(segmented_surface(text, forms), ["Ela disse “Isso basta.”", "Depois, partiu."])

    def test_reporting_clause_after_dash_is_not_split(self) -> None:
        text = "“Isso basta!” — afirmou a autora. Depois, partiu."
        forms = ["“", "Isso", "basta", "!", "”", "—", "afirmou", "a", "autora", ".", "Depois", ",", "partiu", "."]
        self.assertEqual(segmented_surface(text, forms), ["“Isso basta!” — afirmou a autora.", "Depois, partiu."])

    def test_unquoted_dash_does_not_cancel_sentence_boundary(self) -> None:
        text = "A medida protege os surdos. - uma ação adicional será proposta."
        forms = ["A", "medida", "protege", "os", "surdos", ".", "-", "uma", "ação", "adicional", "será", "proposta", "."]
        self.assertEqual(segmented_surface(text, forms), ["A medida protege os surdos.", "- uma ação adicional será proposta."])

    def test_lowercase_one_letter_word_is_not_an_initial(self) -> None:
        text = "O problema não é. Crianças ainda aprendem."
        forms = ["O", "problema", "não", "é", ".", "Crianças", "ainda", "aprendem", "."]
        self.assertEqual(segmented_surface(text, forms), ["O problema não é.", "Crianças ainda aprendem."])

    def test_decimal_period_is_not_a_boundary(self) -> None:
        text = "O índice foi 3.14 no teste. Depois, mudou."
        forms = ["O", "índice", "foi", "3", ".", "14", "no", "teste", ".", "Depois", ",", "mudou", "."]
        self.assertEqual(segmented_surface(text, forms), ["O índice foi 3.14 no teste.", "Depois, mudou."])

    def test_url_internal_period_is_not_a_boundary(self) -> None:
        text = "Consulte https://exemplo.com hoje. Depois, retorne."
        forms = ["Consulte", "https://exemplo", ".", "com", "hoje", ".", "Depois", ",", "retorne", "."]
        self.assertEqual(segmented_surface(text, forms), ["Consulte https://exemplo.com hoje.", "Depois, retorne."])


def sentence_surfaces(path: Path) -> list[str]:
    tree = etree.parse(str(path))
    return [surface_text(sentence).strip() for sentence in tree.xpath("//tei:body/tei:p/tei:s", namespaces=NS)]


def assert_same_sentence(sentences: list[str], phrase: str, document: str) -> None:
    if not any(phrase in sentence for sentence in sentences):
        raise AssertionError(f"Expected one sentence containing {phrase!r} in {document}")


def verify_corpus_regressions(annotated: Path) -> None:
    regressions = {
        "TEK_0659.xml": "o protagonista Neo é confrontado",
        "TEK_3567.xml": "Ministério das Comunicações",
        "TEK_5119.xml": "O livro “Quarto de despejo”",
        "TEK_8939.xml": "“Nise: O Coração da Loucura”",
    }
    for filename, phrase in regressions.items():
        assert_same_sentence(sentence_surfaces(annotated / filename), phrase, filename)

    sentences = sentence_surfaces(annotated / "TEK_2030.xml")
    democracy = next((index for index, sentence in enumerate(sentences) if sentence.endswith("democracia.")), None)
    if democracy is None or democracy + 1 >= len(sentences) or not sentences[democracy + 1].startswith("Em uma análise"):
        raise AssertionError("TEK_2030 must split after 'democracia.' and before 'Em uma análise'")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotated", type=Path)
    args, _ = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PortugueseSegmentationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.annotated:
        verify_corpus_regressions(args.annotated)
        print("Corpus sentence-boundary regressions passed.")


if __name__ == "__main__":
    main()
