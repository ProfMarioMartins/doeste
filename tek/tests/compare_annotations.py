#!/usr/bin/env python3
"""Compare current and candidate TEK annotations without rebuilding CQP."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI}
ATTRS = ("form", "lemma", "upos", "feats", "head", "deprel")


@dataclass(frozen=True)
class TokenRecord:
    paragraph: str
    start: int
    end: int
    form: str
    element: etree._Element


def surface(element: etree._Element) -> str:
    result = element.text or ""
    for child in element:
        if etree.QName(child).localname != "dtok":
            result += surface(child)
        result += child.tail or ""
    return result


def records(paragraph: etree._Element) -> list[TokenRecord]:
    text = surface(paragraph)
    cursor = 0
    result: list[TokenRecord] = []
    paragraph_id = paragraph.get("id")
    for token in paragraph.xpath("./tei:s/tei:tok", namespaces=NS):
        form = token.text or ""
        start = text.index(form, cursor)
        end = start + len(form)
        result.append(TokenRecord(paragraph_id, start, end, form, token))
        cursor = end
    return result


def paragraph_map(tree: etree._ElementTree) -> dict[str, etree._Element]:
    return {paragraph.get("id"): paragraph for paragraph in tree.xpath("//tei:body/tei:p", namespaces=NS)}


def boundary_positions(paragraph: etree._Element, token_records: list[TokenRecord]) -> set[int]:
    by_element = {id(record.element): record for record in token_records}
    result: set[int] = set()
    sentences = paragraph.xpath("./tei:s", namespaces=NS)
    for sentence in sentences[:-1]:
        last = sentence.xpath("./tei:tok[last()]", namespaces=NS)[0]
        result.add(by_element[id(last)].end)
    return result


def context(text: str, position: int, width: int = 42) -> str:
    return text[max(0, position - width):position] + " | " + text[position:min(len(text), position + width)]


def normalized_analysis(token_records: list[TokenRecord]) -> dict[tuple[str, int, int, int], dict[str, str]]:
    nodes: list[tuple[tuple[str, int, int, int], etree._Element]] = []
    id_to_key: dict[str, tuple[str, int, int, int]] = {}
    for record in token_records:
        dtoks = record.element.xpath("./tei:dtok", namespaces=NS)
        if dtoks:
            for component, node in enumerate(dtoks, 1):
                key = (record.paragraph, record.start, record.end, component)
                nodes.append((key, node))
                id_to_key[node.get("id")] = key
        else:
            key = (record.paragraph, record.start, record.end, 0)
            nodes.append((key, record.element))
            id_to_key[record.element.get("id")] = key
    result: dict[tuple[str, int, int, int], dict[str, str]] = {}
    for key, node in nodes:
        values = {attribute: node.get(attribute) or "_" for attribute in ATTRS}
        head = node.get("head")
        values["head"] = "ROOT" if head == "0" else repr(id_to_key.get(head, ("UNRESOLVED", head)))
        result[key] = values
    return result


def cqp_value(token: etree._Element, attribute: str) -> str:
    dtoks = token.xpath("./tei:dtok", namespaces=NS)
    if dtoks:
        return "+".join(dtok.get(attribute) or "__UNDEF__" for dtok in dtoks)
    return token.get(attribute) or "__UNDEF__"


def projected_metrics(directory: Path) -> dict[str, int]:
    metrics: Counter[str] = Counter()
    word_types: set[str] = set()
    for path in sorted(directory.glob("TEK_*.xml")):
        tree = etree.parse(str(path))
        tokens = tree.xpath("//tei:body//tei:tok", namespaces=NS)
        metrics["documents"] += 1
        metrics["paragraphs"] += len(tree.xpath("//tei:body/tei:p", namespaces=NS))
        metrics["sentences"] += len(tree.xpath("//tei:body//tei:s", namespaces=NS))
        metrics["tok"] += len(tokens)
        metrics["dtok"] += len(tree.xpath("//tei:body//tei:dtok", namespaces=NS))
        year = tree.xpath("string(//tei:setting/tei:date[@type='exam']/@when)", namespaces=NS)
        theme = tree.xpath("string(//tei:keywords[@type='official_prompt']/tei:term)", namespaces=NS)
        author = tree.xpath("string(//tei:titleStmt/tei:author)", namespaces=NS)
        for token in tokens:
            word = token.text or ""
            word_types.add(word)
            metrics['word="da"'] += word == "da"
            metrics['word="sociedade"'] += word == "sociedade"
            metrics['lemma="sociedade"'] += cqp_value(token, "lemma") == "sociedade"
            metrics['lemma="valorizar"'] += cqp_value(token, "lemma") == "valorizar"
            metrics['upos="VERB"'] += cqp_value(token, "upos") == "VERB"
        metrics["year=2024"] += len(tokens) if year == "2024" else 0
        metrics["theme=2024"] += len(tokens) if theme == "Desafios para a valorização da herança africana no Brasil" else 0
        metrics["Sabrina"] += len(tokens) if author == "Sabrina Ayumi Alves Shimizu" else 0
    metrics["word_types"] = len(word_types)
    return dict(metrics)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.report.mkdir(parents=True, exist_ok=True)

    boundary_rows: list[dict[str, str | int]] = []
    token_rows: list[dict[str, str | int]] = []
    analysis_rows: list[dict[str, str | int]] = []
    analysis_counts: Counter[str] = Counter()
    affected_documents: set[str] = set()

    for old_path in sorted(args.old.glob("TEK_*.xml")):
        new_path = args.new / old_path.name
        old_tree, new_tree = etree.parse(str(old_path)), etree.parse(str(new_path))
        old_paragraphs, new_paragraphs = paragraph_map(old_tree), paragraph_map(new_tree)
        assert old_paragraphs.keys() == new_paragraphs.keys()
        for paragraph_id in old_paragraphs:
            old_p, new_p = old_paragraphs[paragraph_id], new_paragraphs[paragraph_id]
            text = surface(old_p)
            assert text == surface(new_p)
            old_records, new_records = records(old_p), records(new_p)

            old_boundaries = boundary_positions(old_p, old_records)
            new_boundaries = boundary_positions(new_p, new_records)
            removed, added = sorted(old_boundaries - new_boundaries), sorted(new_boundaries - old_boundaries)
            paired_removed: set[int] = set()
            paired_added: set[int] = set()
            for old_position in removed:
                candidates = [position for position in added if position not in paired_added and abs(position - old_position) <= 5]
                if candidates:
                    new_position = min(candidates, key=lambda position: abs(position - old_position))
                    paired_removed.add(old_position)
                    paired_added.add(new_position)
                    boundary_rows.append({"document": old_path.stem, "paragraph": paragraph_id, "kind": "repositioned", "old": old_position, "new": new_position, "context": context(text, new_position)})
            for position in removed:
                if position not in paired_removed:
                    boundary_rows.append({"document": old_path.stem, "paragraph": paragraph_id, "kind": "removed", "old": position, "new": "", "context": context(text, position)})
            for position in added:
                if position not in paired_added:
                    boundary_rows.append({"document": old_path.stem, "paragraph": paragraph_id, "kind": "added", "old": "", "new": position, "context": context(text, position)})
            if removed or added:
                affected_documents.add(old_path.stem)

            matcher = SequenceMatcher(a=[record.form for record in old_records], b=[record.form for record in new_records], autojunk=False)
            for operation, i1, i2, j1, j2 in matcher.get_opcodes():
                if operation != "equal":
                    token_rows.append({
                        "document": old_path.stem, "paragraph": paragraph_id, "operation": operation,
                        "old_forms": " + ".join(record.form for record in old_records[i1:i2]),
                        "new_forms": " + ".join(record.form for record in new_records[j1:j2]),
                        "old_ranges": ";".join(f"{record.start}:{record.end}" for record in old_records[i1:i2]),
                        "new_ranges": ";".join(f"{record.start}:{record.end}" for record in new_records[j1:j2]),
                    })
                    affected_documents.add(old_path.stem)

            old_analysis, new_analysis = normalized_analysis(old_records), normalized_analysis(new_records)
            for key in sorted(old_analysis.keys() & new_analysis.keys()):
                for attribute in ATTRS:
                    if old_analysis[key][attribute] != new_analysis[key][attribute]:
                        analysis_counts[attribute] += 1
                        analysis_rows.append({
                            "document": old_path.stem, "paragraph": paragraph_id,
                            "range": f"{key[1]}:{key[2]}", "component": key[3],
                            "attribute": attribute, "old": old_analysis[key][attribute],
                            "new": new_analysis[key][attribute],
                        })
                        affected_documents.add(old_path.stem)

    for filename, rows in (("boundaries.tsv", boundary_rows), ("tokenization.tsv", token_rows), ("analysis.tsv", analysis_rows)):
        with (args.report / filename).open("w", encoding="utf-8", newline="") as output:
            if rows:
                writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)

    summary = {
        "old_metrics": projected_metrics(args.old),
        "new_metrics": projected_metrics(args.new),
        "boundary_counts": dict(Counter(str(row["kind"]) for row in boundary_rows)),
        "tokenization_changes": len(token_rows),
        "analysis_changes": dict(analysis_counts),
        "analysis_change_rows": len(analysis_rows),
        "affected_documents": sorted(affected_documents),
    }
    (args.report / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
