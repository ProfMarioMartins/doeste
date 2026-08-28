#!/usr/bin/env python3
"""Verify fidelity and essential metadata of the stabilized TEK source set."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_source import PROMPTS, docx_records  # noqa: E402

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}


def values(tree: etree._ElementTree, xpath: str) -> list[str]:
    return [str(value).strip() for value in tree.xpath(xpath, namespaces=NS)]


def paragraphs(tree: etree._ElementTree) -> list[str]:
    return ["".join(p.itertext()) for p in tree.xpath("//tei:body/tei:p", namespaces=NS)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.source.glob("TEK_*.xml"))
    assert len(files) == 128, f"expected 128 source files, found {len(files)}"
    ids: set[str] = set()
    years: Counter[str] = Counter()
    imported_2024: dict[str, tuple[str, list[str]]] = {}

    for path in files:
        tree = etree.parse(str(path))
        root = tree.getroot()
        document_id = root.get(f"{{{XML}}}id")
        assert document_id == path.stem and document_id not in ids
        ids.add(document_id)
        assert values(tree, "//tei:language/@ident") == ["pt-BR"]
        assert values(tree, "//tei:keywords[@type='corpus']/tei:term/text()") == ["TEK"]
        assert values(tree, "//tei:keywords[@type='domain']/tei:term/text()") == ["Escolar"]
        assert values(tree, "//tei:textDesc/tei:purpose/text()") == ["Argumentar"]
        assert values(tree, "//tei:keywords[@type='score']/tei:term/text()") == ["1000"]
        assert len(values(tree, "//tei:titleStmt/tei:author/text()")) == 1
        year = values(tree, "//tei:setting/tei:date[@type='exam']/@when")[0]
        years[year] += 1
        assert values(tree, "//tei:keywords[@type='official_prompt']/tei:term/text()") == [PROMPTS[year][0]]
        assert not values(tree, "//tei:date[@type='publication']/@when")
        if year == "2024":
            author = values(tree, "//tei:titleStmt/tei:author/text()")[0]
            imported_2024[author] = (document_id, paragraphs(tree))

    for original_path in sorted(args.original.glob("TEK_*.xml")):
        original = etree.parse(str(original_path))
        document_id = original.getroot().get(f"{{{XML}}}id")
        stabilized = etree.parse(str(args.source / f"{document_id}.xml"))
        assert paragraphs(original) == paragraphs(stabilized), f"text changed: {document_id}"

    expected_2024 = [record for record in docx_records(args.docx) if record["year"] == "2024"]
    assert len(expected_2024) == 10
    for record in expected_2024:
        author = str(record["author"])
        assert author in imported_2024, f"missing 2024 author: {author}"
        assert list(record["paragraphs"]) == imported_2024[author][1], f"2024 text changed: {author}"

    print("Verified exact paragraph text for 118 original XML and 10 DOCX records.")
    print("Verified 128 unique IDs and required canonical metadata.")
    print("Documents by exam year:", ", ".join(f"{year}={years[year]}" for year in sorted(years)))


if __name__ == "__main__":
    main()
