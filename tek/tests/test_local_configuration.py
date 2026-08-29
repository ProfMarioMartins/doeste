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
EXPECTED_FILTERS = {"id", "year", "theme", "author", "language", "domain", "purpose"}
HIDDEN_FILTERS = {"score", "corpus", "source", "name"}
EXPECTED_YEARS = {"2012", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"}


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
    assert filters == EXPECTED_FILTERS
    assert filters.isdisjoint(HIDDEN_FILTERS)
    assert settings.xpath("string(//cqp/@tokxpath)") == "//*[local-name()='tok']"
    assert settings.xpath("string(//cqp/@wordpath)") == "text()"
    assert settings.xpath("string(//cqp/@toktype)") == "t"
    assert settings.xpath("string(//cqp/sattributes/item[@level='text']/item[@key='id']/@display)") == "ID do Texto"
    assert settings.xpath("string(//cqp/sattributes/item[@level='text']/item[@key='year']/@type)") == "select"

    pages = sorted((root / "Pages").glob("*.html"))
    assert {p.name for p in pages} == {"home.html", "metodo-pt.html", "cqptext.html", "querybuilderhelp.html"}
    for page in pages:
        fragment = html.fragment_fromstring(page.read_text(encoding="utf-8"), create_parent="main")
        assert fragment.text_content().strip(), f"empty page: {page.name}"
        for href in fragment.xpath(".//a/@href"):
            assert not href.startswith("https://doeste.ufersa.edu.br"), f"production-only link in {page.name}: {href}"
            assert "action=fontes" not in href, f"obsolete sources link in {page.name}: {href}"

    search_help = html.fragment_fromstring(
        (root / "Pages" / "cqptext.html").read_text(encoding="utf-8"), create_parent="main"
    ).text_content()
    for label in ("Forma", "Lema", "Classe gramatical", "ID do Texto", "Ano do ENEM", "Tema oficial", "Autor(a)", "Língua", "Domínio", "Propósito"):
        assert label in search_help, f"missing public search guidance: {label}"
    for hidden_label in ("Fonte documentada", "Propósito comunicativo", "Forma ortográfica", "Classe gramatical (UPOS)"):
        assert hidden_label not in search_help, f"obsolete public search label: {hidden_label}"

    home = html.fragment_fromstring(
        (root / "Pages" / "home.html").read_text(encoding="utf-8"), create_parent="main"
    )
    home_text = " ".join(home.text_content().split())
    home_headings = [" ".join(value.split()) for value in home.xpath(".//h1/text() | .//h2/text()")]
    assert home_headings == [
        "Corpus TEK – Redações Nota Mil",
        "Composição",
        "Estrutura e anotação",
        "Consultar o corpus",
        "Metadados",
        "Aspectos éticos e acesso",
        "Atualização dos dados",
    ]
    for statement in ("128 redações", "2012 e 2024", "sem textos da edição de 2013", "português brasileiro", "nota 1000"):
        assert statement in home_text, f"missing public corpus statement: {statement}"
    expected_home_links = {
        "index.php?action=files",
        "index.php?action=stats",
        "index.php?action=cqp&act=distribute",
    }
    assert set(home.xpath(".//a/@href")) == expected_home_links
    assert "23 de agosto de 2026" not in home_text
    assert "Última atualização dos dados:" not in home_text, "do not publish a date before manifest integration"

    tek_css = (root / "Resources" / "tek.css").read_text(encoding="utf-8")
    for responsive_rule in ("min-width: 0", "max-width: 100%", "table-layout: fixed", "@media (max-width: 1200px)", "@media (max-width: 600px)"):
        assert responsive_rule in tek_css, f"missing responsive search rule: {responsive_rule}"

    xml_files = sorted((root / "xmlfiles").glob("TEK_*.xml"))
    assert len(xml_files) == 128
    counts: Counter[str] = Counter()
    years: set[str] = set()
    for path in xml_files:
        tree = etree.parse(str(path))
        counts["documents"] += 1
        counts["paragraphs"] += len(tree.xpath("//tei:body/tei:p", namespaces=NS))
        counts["sentences"] += len(tree.xpath("//tei:body//tei:s", namespaces=NS))
        counts["tokens"] += len(tree.xpath("//tei:body//tei:tok", namespaces=NS))
        years.update(tree.xpath("//tei:setting/tei:date[@type='exam']/@when", namespaces=NS))
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
    assert years == EXPECTED_YEARS

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
    print("pages=4 valid HTML fragments; no absolute production links")
    print("corpus=" + ", ".join(f"{key}={value}" for key, value in counts.items()))
    if tt_encoder_available:
        print("xidx=validated (tt-cwb-encode available)")
    else:
        print("xidx=not validated locally (tt-cwb-encode unavailable)")
    for query, result in queries.items():
        print(f"query {query}: {result}")


if __name__ == "__main__":
    main()
