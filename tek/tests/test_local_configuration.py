#!/usr/bin/env python3
"""Local homologation checks that do not require the external TEITOK PHP runtime."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from lxml import etree, html

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI}
EXPECTED_PATTRS = {"word", "lemma", "upos", "feats", "head", "deprel"}
EXPECTED_FILTERS = {"year", "theme", "author", "score", "language", "domain", "purpose", "corpus", "source"}


def cqp_size(registry: Path, expression: str) -> int:
    commands = f'TEK;\nA = {expression};\nsize A;\n'
    result = subprocess.run(
        ["cqp", "-r", str(registry), "-c"], input=commands, text=True,
        capture_output=True, check=True,
    )
    values = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
    if len(values) != 1:
        raise AssertionError(f"Unexpected CQP output for {expression!r}: {result.stdout}{result.stderr}")
    return int(values[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tek", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.tek.resolve()

    settings = etree.parse(str(root / "Resources" / "settings.xml"))
    pattrs = set(settings.xpath("//cqp/pattributes/item/@key"))
    filters = set(settings.xpath("//cqp/sattributes/item[@level='text']/item/@key"))
    filter_nodes = settings.xpath("//cqp/sattributes/item[@level='text']/item")
    assert EXPECTED_PATTRS <= pattrs
    assert EXPECTED_FILTERS <= filters
    assert settings.xpath("string(//cqp/@tokxpath)") == "//*[local-name()='tok']"
    assert settings.xpath("string(//cqp/@wordpath)") == "text()"

    pages = sorted((root / "Pages").glob("*.html"))
    assert {p.name for p in pages} == {"home.html", "metodo-pt.html", "fontes-pt.html", "cqptext.html", "querybuilderhelp.html"}
    for page in pages:
        fragment = html.fragment_fromstring(page.read_text(encoding="utf-8"), create_parent="main")
        assert fragment.text_content().strip(), f"empty page: {page.name}"
        for href in fragment.xpath(".//a/@href"):
            assert not href.startswith("https://doeste.ufersa.edu.br"), f"production-only link in {page.name}: {href}"

    xml_files = sorted((root / "xmlfiles").glob("TEK_*.xml"))
    assert len(xml_files) == 128
    counts: Counter[str] = Counter()
    for path in xml_files:
        tree = etree.parse(str(path))
        counts["documents"] += 1
        counts["paragraphs"] += len(tree.xpath("//tei:body/tei:p", namespaces=NS))
        counts["sentences"] += len(tree.xpath("//tei:body//tei:s", namespaces=NS))
        counts["tokens"] += len(tree.xpath("//tei:body//tei:tok", namespaces=NS))
        for xpath in (
            "//tei:titleStmt/tei:author",
            "//tei:setting/tei:date[@type='exam']/@when",
            "//tei:keywords[@type='official_prompt']/tei:term",
            "//tei:keywords[@type='score']/tei:term",
        ):
            assert len(tree.xpath(xpath, namespaces=NS)) == 1, f"bad metadata {path.name}: {xpath}"
        for filter_node in filter_nodes:
            xpath = filter_node.get("xpath")
            result = tree.xpath(xpath)
            assert len(result) == 1, f"filter {filter_node.get('key')} failed for {path.name}: {xpath}"

    registry = root / "cqp"
    assert (registry / "tek").is_file(), "TEITOK registry must be available at tek/cqp/tek"
    assert (registry / "word.corpus").is_file(), "CWB binaries must be available directly in tek/cqp"
    tt_encoder_available = shutil.which("tt-cwb-encode") is not None
    if tt_encoder_available:
        assert (registry / "xidx.rng").is_file(), "tt-cwb-encode build must produce tek/cqp/xidx.rng"
    assert not (registry / "data" / "word.corpus").exists(), "obsolete cqp/data architecture detected"
    assert not (registry / "registry" / "tek").exists(), "obsolete nested registry detected"
    registry_text = (registry / "tek").read_text(encoding="utf-8")
    expected_home = f"HOME {registry.resolve()}"
    expected_info = f"INFO {registry.resolve() / '.info'}"
    assert expected_home in registry_text, f"registry HOME must be {registry.resolve()}"
    assert expected_info in registry_text, f"registry INFO must be {registry.resolve() / '.info'}"
    queries = {
        'word="sociedade"': cqp_size(registry, '[word="sociedade"]'),
        'word="da"': cqp_size(registry, '[word="da"]'),
        'lemma="sociedade"': cqp_size(registry, '[lemma="sociedade"]'),
        'lemma="valorizar"': cqp_size(registry, '[lemma="valorizar"]'),
        'upos="VERB"': cqp_size(registry, '[upos="VERB"]'),
        'year=2024': cqp_size(registry, '[] :: match.text_year = "2024"'),
        'theme=2024': cqp_size(registry, '[] :: match.text_theme = "Desafios para a valorização da herança africana no Brasil"'),
        'author=Sabrina': cqp_size(registry, '[] :: match.text_author = "Sabrina Ayumi Alves Shimizu"'),
    }
    assert all(value > 0 for value in queries.values())
    assert counts["tokens"] == 60620
    assert counts["sentences"] == 1891
    assert queries['word="da"'] == 897
    assert queries['lemma="sociedade"'] == 228
    assert queries['upos="VERB"'] == 5565
    assert queries["year=2024"] == 4720
    assert queries["year=2024"] == queries["theme=2024"]
    print("configuration=valid")
    print("pages=5 valid HTML fragments; no absolute production links")
    print("corpus=" + ", ".join(f"{key}={value}" for key, value in counts.items()))
    if tt_encoder_available:
        print("xidx=validated (tt-cwb-encode available)")
    else:
        print("xidx=not validated locally (tt-cwb-encode unavailable)")
    for query, result in queries.items():
        print(f"query {query}: {result}")


if __name__ == "__main__":
    main()
