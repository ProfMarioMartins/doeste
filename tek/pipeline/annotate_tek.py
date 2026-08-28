#!/usr/bin/env python3
"""Lossless UDPipe annotation for canonical TEK source XML.

Orthographic tokens remain as ``tok`` text. CoNLL-U multiword-token analyses
are represented as TEITOK ``dtok`` children, preserving contractions such as
``da`` while retaining the UD analyses of ``de`` and ``a``.
"""

from __future__ import annotations

import argparse
import copy
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}
MODEL = "portuguese-bosque-ud-2.17-251125"
UDPIPE_API = "https://lindat.mff.cuni.cz/services/udpipe/api/process"


@dataclass
class Word:
    conllu_id: int
    form: str
    lemma: str
    upos: str
    feats: str
    head: int
    deprel: str
    start: int
    end: int


@dataclass
class Multiword:
    first: int
    last: int
    form: str
    start: int
    end: int


@dataclass
class Sentence:
    words: list[Word]
    multiwords: list[Multiword]


def misc_values(value: str) -> dict[str, str]:
    if value == "_":
        return {}
    result: dict[str, str] = {}
    for item in value.split("|"):
        key, _, val = item.partition("=")
        result[key] = val
    return result


def token_range(misc: str, required: bool = True) -> tuple[int, int]:
    value = misc_values(misc).get("TokenRange")
    if not value:
        if required:
            raise ValueError("UDPipe output lacks TokenRange; lossless alignment is impossible")
        return -1, -1
    start, end = value.split(":", 1)
    return int(start), int(end)


def parse_conllu(conllu: str) -> list[Sentence]:
    sentences: list[Sentence] = []
    words: list[Word] = []
    multiwords: list[Multiword] = []
    for raw in [*conllu.splitlines(), ""]:
        line = raw.strip("\n")
        if not line:
            if words:
                sentences.append(Sentence(words, multiwords))
                words, multiwords = [], []
            continue
        if line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 10:
            raise ValueError(f"Invalid CoNLL-U line: {line}")
        if "-" in cols[0]:
            first, last = (int(x) for x in cols[0].split("-", 1))
            start, end = token_range(cols[9])
            multiwords.append(Multiword(first, last, cols[1], start, end))
        elif "." not in cols[0]:
            # UDPipe omits TokenRange on grammatical components of a
            # multiword token; the enclosing 1-2 line carries its exact
            # orthographic interval.
            start, end = token_range(cols[9], required=False)
            words.append(Word(int(cols[0]), cols[1], cols[2], cols[3], cols[5], int(cols[6]), cols[7], start, end))
    return sentences


def call_udpipe(text: str) -> tuple[str, str]:
    data = urlencode({"model": MODEL, "tokenizer": "ranges", "tagger": "", "parser": "", "data": text}).encode()
    request = Request(UDPIPE_API, data=data, method="POST")
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(request, timeout=180) as response:
                payload = json.load(response)
            break
        except (HTTPError, URLError, ConnectionError) as error:
            last_error = error
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    else:  # pragma: no cover - defensive; the loop either breaks or raises.
        raise RuntimeError("UDPipe request failed") from last_error
    return payload["result"], payload["model"]


def set_analysis(element: etree._Element, word: Word) -> None:
    element.set("form", word.form)
    element.set("lemma", word.lemma)
    element.set("upos", word.upos)
    if word.feats != "_":
        element.set("feats", word.feats)
    element.set("deprel", word.deprel)


def annotate_paragraph(text: str, conllu: str, paragraph_id: str, sentence_offset: int = 0, token_offset: int = 0) -> tuple[etree._Element, int, int]:
    sentences = parse_conllu(conllu)
    paragraph = etree.Element(f"{{{TEI}}}p")
    paragraph.set("id", paragraph_id)
    cursor = 0
    previous_sentence: etree._Element | None = None
    sentence_number = sentence_offset
    token_number = token_offset
    for sentence in sentences:
        sentence_number += 1
        sentence_el = etree.SubElement(paragraph, f"{{{TEI}}}s")
        sentence_el.set("id", f"s-{sentence_number}")
        covered_ids = {i for m in sentence.multiwords for i in range(m.first, m.last + 1)}
        for word in sentence.words:
            if word.conllu_id not in covered_ids and word.start < 0:
                raise ValueError(f"UDPipe output lacks TokenRange for orthographic token {word.conllu_id}")
        first_start = min([w.start for w in sentence.words if w.start >= 0] + [m.start for m in sentence.multiwords])
        if previous_sentence is None:
            paragraph.text = text[:first_start]
        else:
            previous_sentence.tail = text[cursor:first_start]
        mwt_by_first = {m.first: m for m in sentence.multiwords}
        covered = covered_ids
        word_map = {w.conllu_id: w for w in sentence.words}
        head_targets: list[tuple[etree._Element, int]] = []
        emitted: list[tuple[etree._Element, int, int]] = []
        id_target: dict[int, str] = {}
        for word in sentence.words:
            if word.conllu_id in covered and word.conllu_id not in mwt_by_first:
                continue
            token_number += 1
            if word.conllu_id in mwt_by_first:
                mwt = mwt_by_first[word.conllu_id]
                token = etree.SubElement(sentence_el, f"{{{TEI}}}tok")
                token.set("id", f"w-{token_number}")
                token.set("form", text[mwt.start:mwt.end])
                token.text = text[mwt.start:mwt.end]
                emitted.append((token, mwt.start, mwt.end))
                for component_id in range(mwt.first, mwt.last + 1):
                    component = word_map[component_id]
                    dtok = etree.SubElement(token, f"{{{TEI}}}dtok")
                    dtok.set("id", f"d-{sentence_number}-{component_id}")
                    set_analysis(dtok, component)
                    id_target[component_id] = dtok.get("id")
                    head_targets.append((dtok, component.head))
            else:
                token = etree.SubElement(sentence_el, f"{{{TEI}}}tok")
                token.set("id", f"w-{token_number}")
                token.text = text[word.start:word.end]
                set_analysis(token, word)
                token.set("form", text[word.start:word.end])
                emitted.append((token, word.start, word.end))
                id_target[word.conllu_id] = token.get("id")
                head_targets.append((token, word.head))
        for element, head in head_targets:
            element.set("head", "0" if head == 0 else id_target.get(head, str(head)))
        for index, (element, start, end) in enumerate(emitted):
            next_start = emitted[index + 1][1] if index + 1 < len(emitted) else end
            element.tail = text[end:next_start]
        cursor = max(end for _, _, end in emitted)
        previous_sentence = sentence_el
    if previous_sentence is None:
        paragraph.text = text
    else:
        previous_sentence.tail = text[cursor:]
    if surface_text(paragraph) != text:
        raise ValueError(f"Surface preservation failed for {paragraph_id}")
    return paragraph, sentence_number, token_number


def surface_text(element: etree._Element) -> str:
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        if etree.QName(child).localname != "dtok":
            parts.append(surface_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def annotate_tree(tree: etree._ElementTree) -> etree._ElementTree:
    result = copy.deepcopy(tree)
    paragraphs = result.xpath("//tei:body/tei:p", namespaces=NS)
    sentence_number = token_number = 0
    resolved_models: set[str] = set()
    for old in paragraphs:
        text = surface_text(old)
        conllu, resolved_model = call_udpipe(text)
        resolved_models.add(resolved_model)
        new, sentence_number, token_number = annotate_paragraph(text, conllu, old.get(f"{{{XML}}}id"), sentence_number, token_number)
        old.getparent().replace(old, new)
    if len(resolved_models) != 1:
        raise ValueError(f"Inconsistent UDPipe model versions in one document: {sorted(resolved_models)}")
    resolved_model = next(iter(resolved_models))
    revision = result.xpath("//tei:revisionDesc", namespaces=NS)[0]
    change = etree.SubElement(revision, f"{{{TEI}}}change", who="DOESTE_UDPIPE_PIPELINE")
    change.set("when", datetime.now(timezone.utc).isoformat())
    change.text = (
        f"Automatic lossless tokenization and UD annotation "
        f"(requested_model={MODEL}; resolved_model={resolved_model}; tokenizer=ranges); "
        "contractions represented with TEITOK dtok."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tree = etree.parse(str(args.input))
    annotated = annotate_tree(tree)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    annotated.write(str(args.output), encoding="UTF-8", xml_declaration=True, pretty_print=True)


if __name__ == "__main__":
    main()
