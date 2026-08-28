#!/usr/bin/env python3
"""Build the canonical TEK source XML set from the audited source material."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from docx import Document
from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}

PROMPTS = {
    "2012": ("O movimento imigratório para o Brasil no século XXI", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/relatorio_pedagogico_enem_2011_2012.pdf"),
    "2014": ("Publicidade infantil em questão no Brasil", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/textos_dissertativo_argumentativos.pdf"),
    "2015": ("A persistência da violência contra a mulher na sociedade brasileira", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/textos_dissertativo_argumentativos.pdf"),
    "2016": ("Caminhos para combater a intolerância religiosa no Brasil", "https://download.inep.gov.br/educacao_basica/enem/provas/2016/CAD_ENEM_2016_DIA_2_05_AMARELO.pdf"),
    "2017": ("Desafios para a formação educacional de surdos no Brasil", "https://download.inep.gov.br/educacao_basica/enem/downloads/2020/presskit/press_kit_enem_2020.pdf"),
    "2018": ("Manipulação do comportamento do usuário pelo controle de dados na internet", "https://download.inep.gov.br/educacao_basica/enem/downloads/2020/Situacoes_nota_zero.pdf"),
    "2019": ("Democratização do acesso ao cinema no Brasil", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/a_redacao_do_enem_2020_-_cartilha_do_participante.pdf"),
    "2020": ("O estigma associado às doenças mentais na sociedade brasileira", "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos/2020"),
    "2021": ("Invisibilidade e registro civil: garantia de acesso à cidadania no Brasil", "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos/2021"),
    "2022": ("Desafios para a valorização de comunidades e povos tradicionais no Brasil", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/a_redacao_no_enem_2023_cartilha_do_participante.pdf"),
    "2023": ("Desafios para o enfrentamento da invisibilidade do trabalho de cuidado realizado pela mulher no Brasil", "https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/a_redacao_no_enem_2024_cartilha_do_participante.pdf"),
    "2024": ("Desafios para a valorização da herança africana no Brasil", "https://download.inep.gov.br/enem/outros_documentos/balanco_aplicacao_enem_2024_03112024-2.pdf"),
}

G1_AGGREGATOR = "https://g1.globo.com/educacao/enem/2024/noticia/2024/10/26/redacao-do-enem-leia-100-textos-que-tiraram-nota-mil.ghtml"
INEP_2024_COLLECTION = "https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/enem/enem-2025-cartilha-da-redacao-esta-disponivel"


def q(tree: etree._ElementTree, xpath: str) -> str:
    return tree.xpath(f"string({xpath})", namespaces=NS).strip()


def add_keywords(parent: etree._Element, kind: str, value: str) -> None:
    keywords = etree.SubElement(parent, f"{{{TEI}}}keywords", type=kind)
    etree.SubElement(keywords, f"{{{TEI}}}term").text = value


def make_header(document_id: str, author: str, year: str, source_url: str, source_type: str) -> etree._Element:
    header = etree.Element(f"{{{TEI}}}teiHeader")
    file_desc = etree.SubElement(header, f"{{{TEI}}}fileDesc")
    title_stmt = etree.SubElement(file_desc, f"{{{TEI}}}titleStmt")
    etree.SubElement(title_stmt, f"{{{TEI}}}title", type="main").text = f"Redação ENEM — {year}"
    etree.SubElement(title_stmt, f"{{{TEI}}}author").text = author
    publication = etree.SubElement(file_desc, f"{{{TEI}}}publicationStmt")
    etree.SubElement(publication, f"{{{TEI}}}p").text = "Corpus TEK — Redações Nota Mil, DOESTE."
    source_desc = etree.SubElement(file_desc, f"{{{TEI}}}sourceDesc")
    bibl = etree.SubElement(source_desc, f"{{{TEI}}}bibl", type=source_type)
    etree.SubElement(bibl, f"{{{TEI}}}title").text = "Fonte pública consultada"
    etree.SubElement(bibl, f"{{{TEI}}}ref", type=source_type, target=source_url)
    if source_type == "aggregator_page":
        etree.SubElement(bibl, f"{{{TEI}}}publisher").text = "G1"
    else:
        etree.SubElement(bibl, f"{{{TEI}}}publisher").text = "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira"
    etree.SubElement(bibl, f"{{{TEI}}}idno", type="internal").text = document_id
    official = etree.SubElement(source_desc, f"{{{TEI}}}bibl", type="official_prompt_source")
    etree.SubElement(official, f"{{{TEI}}}title").text = f"Fonte oficial do tema do ENEM {year}"
    etree.SubElement(official, f"{{{TEI}}}ref", type="institutional_material", target=PROMPTS[year][1])
    etree.SubElement(official, f"{{{TEI}}}publisher").text = "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira"
    profile = etree.SubElement(header, f"{{{TEI}}}profileDesc")
    lang = etree.SubElement(profile, f"{{{TEI}}}langUsage")
    etree.SubElement(lang, f"{{{TEI}}}language", ident="pt-BR").text = "Português brasileiro"
    setting_desc = etree.SubElement(profile, f"{{{TEI}}}settingDesc")
    setting = etree.SubElement(setting_desc, f"{{{TEI}}}setting")
    etree.SubElement(setting, f"{{{TEI}}}name", type="exam").text = "ENEM"
    etree.SubElement(setting, f"{{{TEI}}}date", type="exam", when=year).text = year
    text_class = etree.SubElement(profile, f"{{{TEI}}}textClass")
    add_keywords(text_class, "domain", "Escolar")
    add_keywords(text_class, "corpus", "TEK")
    add_keywords(text_class, "official_prompt", PROMPTS[year][0])
    add_keywords(text_class, "score", "1000")
    text_desc = etree.SubElement(profile, f"{{{TEI}}}textDesc")
    etree.SubElement(text_desc, f"{{{TEI}}}purpose").text = "Argumentar"
    revision = etree.SubElement(header, f"{{{TEI}}}revisionDesc")
    etree.SubElement(revision, f"{{{TEI}}}change", who="DOESTE").text = "Canonical TEK source metadata stabilized."
    return header


def source_from_existing(path: Path) -> tuple[str, str, str, list[str]]:
    tree = etree.parse(str(path))
    document_id = tree.getroot().get(f"{{{XML}}}id")
    author = q(tree, "//tei:author")
    year = q(tree, "//tei:setting/tei:date/@when") or q(tree, "//tei:date[@type='publication']/@when")
    paragraphs = ["".join(p.itertext()) for p in tree.xpath("//tei:body/tei:p", namespaces=NS)]
    return document_id, author, year, paragraphs


def docx_records(path: Path) -> list[dict[str, object]]:
    values = [p.text.strip() for p in Document(path).paragraphs if p.text.strip()]
    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for value in values:
        if value.startswith("LINK:"):
            continue
        if value.startswith("[NOME]"):
            if current:
                records.append(current)
            current = {"author": value[6:].strip(), "year": "", "theme": "", "paragraphs": []}
        elif current and value.startswith("[TEMA]"):
            current["theme"] = value[6:].strip()
        elif current and value.startswith("[ANO]"):
            current["year"] = value[5:].strip()
        elif current and value.startswith("[TEXTO]"):
            current["paragraphs"].append(value[7:].strip())
        elif current:
            current["paragraphs"].append(value)
    if current:
        records.append(current)
    return records


def stable_id(record: dict[str, object], used: set[str]) -> str:
    seed = "\x1f".join([str(record["author"]), str(record["year"]), str(record["theme"]), "\n".join(record["paragraphs"])])
    attempt = 0
    while True:
        material = seed if attempt == 0 else f"{seed}\x1f{attempt}"
        candidate = f"TEK_{int(hashlib.sha256(material.encode()).hexdigest(), 16) % 10000:04d}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        attempt += 1


def write_document(output: Path, document_id: str, author: str, year: str, paragraphs: list[str], source_url: str, source_type: str) -> None:
    root = etree.Element(f"{{{TEI}}}TEI", nsmap={None: TEI})
    root.set(f"{{{XML}}}id", document_id)
    root.append(make_header(document_id, author, year, source_url, source_type))
    text = etree.SubElement(root, f"{{{TEI}}}text")
    text.set(f"{{{XML}}}space", "preserve")
    body = etree.SubElement(text, f"{{{TEI}}}body")
    for number, paragraph in enumerate(paragraphs, 1):
        p = etree.SubElement(body, f"{{{TEI}}}p")
        p.set(f"{{{XML}}}id", f"p-{number}")
        p.text = paragraph
    etree.ElementTree(root).write(str(output), encoding="UTF-8", xml_declaration=True, pretty_print=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    for path in sorted(args.existing.glob("TEK_*.xml")):
        document_id, author, year, paragraphs = source_from_existing(path)
        if document_id in used:
            raise ValueError(f"Duplicate ID: {document_id}")
        used.add(document_id)
        write_document(args.output / f"{document_id}.xml", document_id, author, year, paragraphs, G1_AGGREGATOR, "aggregator_page")
    for record in [r for r in docx_records(args.docx) if r["year"] == "2024"]:
        document_id = stable_id(record, used)
        write_document(args.output / f"{document_id}.xml", document_id, str(record["author"]), "2024", list(record["paragraphs"]), INEP_2024_COLLECTION, "institutional_material")
    if len(list(args.output.glob("TEK_*.xml"))) != 128:
        raise RuntimeError("Expected exactly 128 canonical source XML files")


if __name__ == "__main__":
    main()
