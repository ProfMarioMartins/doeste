#!/usr/bin/env python3
"""Integrity tests for canonical and annotated TEK XML."""

from __future__ import annotations

import argparse
import sys
import unicodedata
import unittest
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parents[1] / "pipeline"))
from annotate_tek import annotate_paragraph, surface_text  # noqa: E402

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI}


CONTRACTION_FIXTURE = """# sent_id = 1
# text = Da escola, ela saiu.
1-2\tDa\t_\t_\t_\t_\t_\t_\t_\tTokenRange=0:2
1\tDe\tde\tADP\t_\t_\t3\tcase\t_\t_
2\ta\to\tDET\t_\tDefinite=Def|Gender=Fem|Number=Sing|PronType=Art\t3\tdet\t_\t_
3\tescola\tescola\tNOUN\t_\tGender=Fem|Number=Sing\t6\tobl\t_\tTokenRange=3:9
4\t,\t,\tPUNCT\t_\t_\t3\tpunct\t_\tSpaceAfter=No|TokenRange=9:10
5\tela\tela\tPRON\t_\tGender=Fem|Number=Sing|Person=3|PronType=Prs\t6\tnsubj\t_\tTokenRange=11:14
6\tsaiu\tsair\tVERB\t_\tMood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin\t0\troot\t_\tSpaceAfter=No|TokenRange=15:19
7\t.\t.\tPUNCT\t_\t_\t6\tpunct\t_\tSpaceAfter=No|TokenRange=19:20
"""


class PipelineUnitTests(unittest.TestCase):
    def test_contraction_punctuation_and_spaces_are_lossless(self) -> None:
        original = "Da escola, ela saiu."
        paragraph, _, _ = annotate_paragraph(original, CONTRACTION_FIXTURE, "p-1")
        self.assertEqual(surface_text(paragraph), original)
        token = paragraph.xpath(".//tei:tok[1]", namespaces=NS)[0]
        self.assertEqual(token.text, "Da")
        self.assertEqual(token.get("form"), "Da")
        self.assertEqual([d.get("form") for d in token.xpath("./tei:dtok", namespaces=NS)], ["De", "a"])


def document_text(path: Path) -> list[str]:
    tree = etree.parse(str(path))
    return [unicodedata.normalize("NFC", surface_text(p)) for p in tree.xpath("//tei:body/tei:p", namespaces=NS)]


def verify_corpus(source: Path, annotated: Path | None = None) -> None:
    files = sorted(source.glob("TEK_*.xml"))
    if len(files) != 128:
        raise AssertionError(f"Expected 128 source files, found {len(files)}")
    ids: set[str] = set()
    for path in files:
        tree = etree.parse(str(path))
        root_id = tree.getroot().get("{http://www.w3.org/XML/1998/namespace}id")
        if root_id in ids:
            raise AssertionError(f"Duplicate ID: {root_id}")
        ids.add(root_id)
        if annotated:
            target = annotated / path.name
            if not target.exists():
                raise AssertionError(f"Missing annotated document: {path.name}")
            if document_text(path) != document_text(target):
                raise AssertionError(f"Surface divergence: {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--annotated", type=Path)
    args, remaining = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PipelineUnitTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.source:
        verify_corpus(args.source, args.annotated)
        print(f"Verified 128 canonical source documents{'; annotated equality passed' if args.annotated else ''}.")


if __name__ == "__main__":
    main()
