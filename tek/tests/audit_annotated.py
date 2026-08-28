#!/usr/bin/env python3
"""Corpus-wide structural and linguistic audit of derived TEK XML."""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}
CONTRACTIONS = {"da", "do", "das", "dos", "na", "no", "nas", "nos", "pela", "pelo", "à", "às"}


def canonical(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n")


def local_id(element: etree._Element) -> str:
    return element.get("id") or element.get(f"{{{XML}}}id")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--annotated", type=Path, required=True)
    args = parser.parse_args()

    source_files = sorted(args.source.glob("TEK_*.xml"))
    annotated_files = sorted(args.annotated.glob("TEK_*.xml"))
    assert len(source_files) == len(annotated_files) == 128
    assert [p.name for p in source_files] == [p.name for p in annotated_files]

    totals: Counter[str] = Counter()
    attribute_counts: Counter[str] = Counter()
    missing_required: defaultdict[str, list[str]] = defaultdict(list)
    contraction_examples: defaultdict[str, list[tuple[str, str, list[str]]]] = defaultdict(list)
    document_ids: set[str] = set()

    for source_path, annotated_path in zip(source_files, annotated_files):
        source = etree.parse(str(source_path))
        annotated = etree.parse(str(annotated_path))
        doc_id = annotated.getroot().get(f"{{{XML}}}id")
        assert doc_id == source.getroot().get(f"{{{XML}}}id") == annotated_path.stem
        assert doc_id not in document_ids
        document_ids.add(doc_id)

        source_header = copy.deepcopy(source.xpath("/tei:TEI/tei:teiHeader", namespaces=NS)[0])
        annotated_header = copy.deepcopy(annotated.xpath("/tei:TEI/tei:teiHeader", namespaces=NS)[0])
        changes = annotated_header.xpath(".//tei:revisionDesc/tei:change[@who='DOESTE_UDPIPE_PIPELINE']", namespaces=NS)
        assert len(changes) == 1
        changes[0].getparent().remove(changes[0])
        assert canonical(source_header) == canonical(annotated_header), f"header changed: {doc_id}"

        source_paragraphs = source.xpath("//tei:body/tei:p", namespaces=NS)
        paragraphs = annotated.xpath("//tei:body/tei:p", namespaces=NS)
        assert len(source_paragraphs) == len(paragraphs) and paragraphs
        assert [local_id(p) for p in source_paragraphs] == [local_id(p) for p in paragraphs]
        paragraph_ids = [local_id(p) for p in paragraphs]
        assert len(paragraph_ids) == len(set(paragraph_ids))

        sentences = annotated.xpath("//tei:body//tei:s", namespaces=NS)
        orthographic = annotated.xpath("//tei:body//tei:tok", namespaces=NS)
        dtoks = annotated.xpath("//tei:body//tei:dtok", namespaces=NS)
        assert sentences and orthographic
        structural_nodes = [*paragraphs, *sentences, *orthographic, *dtoks]
        assert all(node.get("id") for node in structural_nodes)
        assert all(node.get(f"{{{XML}}}id") is None for node in structural_nodes)
        sentence_ids = [local_id(s) for s in sentences]
        token_ids = [local_id(t) for t in orthographic]
        dtok_ids = [local_id(d) for d in dtoks]
        assert len(sentence_ids) == len(set(sentence_ids))
        assert len(token_ids) == len(set(token_ids))
        assert len(dtok_ids) == len(set(dtok_ids))
        assert sentence_ids == [f"s-{number}" for number in range(1, len(sentences) + 1)]
        assert token_ids == [f"w-{number}" for number in range(1, len(orthographic) + 1)]
        assert all(identifier and identifier.startswith("d-") for identifier in dtok_ids)

        totals.update(documents=1, paragraphs=len(paragraphs), sentences=len(sentences), tok=len(orthographic), dtok=len(dtoks))
        multiwords = [tok for tok in orthographic if tok.xpath("./tei:dtok", namespaces=NS)]
        totals["multiword_tokens"] += len(multiwords)

        for tok in multiwords:
            form = (tok.text or "")
            if form.casefold() in CONTRACTIONS and len(contraction_examples[form.casefold()]) < 2:
                contraction_examples[form.casefold()].append(
                    (doc_id, form, [d.get("form") for d in tok.xpath("./tei:dtok", namespaces=NS)])
                )

        for sentence in sentences:
            analysis_nodes = sentence.xpath("./tei:tok[not(tei:dtok)] | ./tei:tok/tei:dtok", namespaces=NS)
            ids = {local_id(node) for node in analysis_nodes}
            roots = 0
            heads: dict[str, str] = {}
            for node in analysis_nodes:
                node_id = local_id(node)
                for attribute in ("lemma", "upos", "feats", "head", "deprel"):
                    if node.get(attribute) is not None:
                        attribute_counts[attribute] += 1
                for required in ("lemma", "upos", "head", "deprel"):
                    if node.get(required) is None:
                        missing_required[required].append(f"{doc_id}:{node_id}")
                head = node.get("head")
                if head == "0":
                    roots += 1
                else:
                    assert head in ids, f"invalid head {doc_id}:{node_id}->{head}"
                heads[node_id] = head
            assert roots == 1, f"expected one root in {doc_id}:{local_id(sentence)}"
            for node_id in heads:
                seen: set[str] = set()
                cursor = node_id
                while heads[cursor] != "0":
                    assert cursor not in seen, f"dependency cycle in {doc_id}:{local_id(sentence)}"
                    seen.add(cursor)
                    cursor = heads[cursor]

    analysis_total = totals["tok"] - totals["multiword_tokens"] + totals["dtok"]
    print(f"documents={totals['documents']}")
    print(f"paragraphs={totals['paragraphs']}")
    print(f"sentences={totals['sentences']}")
    print(f"tok={totals['tok']}")
    print(f"dtok={totals['dtok']}")
    print(f"multiword_tokens={totals['multiword_tokens']}")
    print(f"analysis_nodes={analysis_total}")
    for attribute in ("lemma", "upos", "feats", "head", "deprel"):
        count = attribute_counts[attribute]
        print(f"{attribute}={count}/{analysis_total} ({count / analysis_total:.2%})")
    for attribute in ("lemma", "upos", "head", "deprel"):
        print(f"missing_{attribute}={len(missing_required[attribute])}")
    print("contraction_examples:")
    for form in sorted(contraction_examples):
        for doc_id, surface, components in contraction_examples[form]:
            print(f"  {doc_id}: {surface} -> {' + '.join(components)}")
    print("Structural validation passed for all 128 documents.")


if __name__ == "__main__":
    main()
