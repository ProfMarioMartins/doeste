#!/usr/bin/env python3
"""Lossless, sentence-controlled UDPipe annotation for canonical TEK XML.

Orthographic tokens remain as ``tok`` text. CoNLL-U multiword-token analyses
are represented as TEITOK ``dtok`` children, preserving contractions such as
``da`` while retaining the UD analyses of ``de`` and ``a``. Sentence
segmentation is performed deterministically by DOESTE-PT between UDPipe's
tokenization and its final tagging/dependency-parsing stages.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
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


@dataclass
class ConlluRow:
    """One mutable ten-column CoNLL-U row from tokenization-only output."""

    columns: list[str]


@dataclass
class OrthographicToken:
    """A surface token and its one or more underlying UD word rows."""

    form: str
    start: int
    end: int
    token_row: ConlluRow | None
    word_rows: list[ConlluRow]


SENTENCE_SEGMENTER = "doeste-pt-v1"
TERMINAL_CHARS = frozenset(".!?…")
CLOSING_MARKS = frozenset({'"', "'", "”", "’", "»", ")", "]", "}"})
CONTINUATION_MARKS = frozenset({",", ";", ":"})
DASHES = frozenset({"-", "–", "—"})

# General Portuguese abbreviations whose final period does not by itself end
# a sentence. This linguistic list is independent of corpus/document IDs.
ABBREVIATIONS = frozenset(
    {
        "art", "arts", "av", "cap", "caps", "cf", "cia", "dr", "dra",
        "ed", "eds", "etc", "ex", "fig", "figs", "inc", "jr", "ltda",
        "n", "no", "núm", "p", "pág", "págs", "prof", "profa", "s",
        "sr", "sra", "srta", "tel", "v", "vol", "vols",
    }
)


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


def call_udpipe(data_fields: dict[str, str]) -> tuple[str, str]:
    """Call the fixed UDPipe model with explicitly selected pipeline stages."""

    data = urlencode({"model": MODEL, **data_fields}).encode()
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


def tokenize_paragraph(text: str) -> tuple[str, str]:
    """Tokenize a whole paragraph losslessly, without tagging or parsing."""

    return call_udpipe({"tokenizer": "ranges", "data": text})


def analyse_presegmented(conllu: str) -> tuple[str, str]:
    """Tag and parse sentence blocks whose tokens are already fixed."""

    return call_udpipe({"input": "conllu", "tagger": "", "parser": "", "data": conllu})


def parse_tokenized_conllu(conllu: str) -> list[OrthographicToken]:
    """Flatten UDPipe sentence guesses into one ordered orthographic stream."""

    rows: list[ConlluRow] = []
    for line in conllu.splitlines():
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 10:
            raise ValueError(f"Invalid tokenization-only CoNLL-U line: {line}")
        if "." not in columns[0]:
            rows.append(ConlluRow(columns))

    tokens: list[OrthographicToken] = []
    index = 0
    while index < len(rows):
        row = rows[index]
        identifier = row.columns[0]
        if "-" in identifier:
            first, last = (int(value) for value in identifier.split("-", 1))
            component_count = last - first + 1
            components = rows[index + 1:index + 1 + component_count]
            if len(components) != component_count or any("-" in item.columns[0] for item in components):
                raise ValueError(f"Malformed multiword token at CoNLL-U id {identifier}")
            start, end = token_range(row.columns[9])
            tokens.append(OrthographicToken(row.columns[1], start, end, row, components))
            index += component_count + 1
        else:
            start, end = token_range(row.columns[9])
            tokens.append(OrthographicToken(row.columns[1], start, end, None, [row]))
            index += 1
    if not tokens:
        raise ValueError("UDPipe tokenization produced no orthographic tokens")
    return tokens


def replace_token_range(misc: str, start: int, end: int, force_no_space: bool = False) -> str:
    """Replace TokenRange while retaining other lossless MISC information."""

    values = [item for item in misc.split("|") if item and item != "_" and not item.startswith("TokenRange=")]
    if force_no_space and "SpaceAfter=No" not in values:
        values.append("SpaceAfter=No")
    values.append(f"TokenRange={start}:{end}")
    return "|".join(values)


def embedded_terminal_offsets(form: str) -> list[int]:
    """Find high-confidence missing token boundaries inside one surface form.

    Full stops require a plausible new sentence beginning (upper-case letter,
    optionally after an opening quote). Question and exclamation marks are
    intrinsically terminal candidates when followed by another lexical unit.
    URLs, e-mail addresses, decimals, abbreviations and initials are excluded.
    Returned offsets identify punctuation characters that become standalone
    orthographic tokens.
    """

    if "://" in form or "@" in form or form.casefold().startswith("www."):
        return []
    offsets: list[int] = []
    for index, char in enumerate(form):
        if char not in ".!?" or index == 0 or index + 1 >= len(form):
            continue
        left = form[:index]
        right = form[index + 1:]
        left_char = left[-1]
        right_lexical = right.lstrip('"\'“‘«([{')
        if not left_char.isalnum() or not right_lexical or not right_lexical[0].isalnum():
            continue
        if char == ".":
            if left_char.isdigit() and right_lexical[0].isdigit():
                continue
            left_word = re.split(r"[^\wÀ-ÖØ-öø-ÿ]+", left)[-1].casefold()
            if left_word in ABBREVIATIONS or (len(left_word) == 1 and left_word.isalpha()):
                continue
            if not right_lexical[0].isupper():
                continue
        offsets.append(index)
    return offsets


def repair_embedded_terminal_tokens(text: str, tokens: list[OrthographicToken]) -> list[OrthographicToken]:
    """Split terminal punctuation fused between lexical units losslessly."""

    repaired: list[OrthographicToken] = []
    for token in tokens:
        offsets = embedded_terminal_offsets(token.form)
        if not offsets or token.token_row is not None:
            repaired.append(token)
            continue

        split_points: list[tuple[int, int]] = []
        start = 0
        for offset in offsets:
            if offset > start:
                split_points.append((start, offset))
            split_points.append((offset, offset + 1))
            start = offset + 1
        if start < len(token.form):
            split_points.append((start, len(token.form)))

        original = token.word_rows[0].columns
        for part_index, (local_start, local_end) in enumerate(split_points):
            absolute_start = token.start + local_start
            absolute_end = token.start + local_end
            form = text[absolute_start:absolute_end]
            if form != token.form[local_start:local_end]:
                raise ValueError("Embedded-token repair diverged from source surface")
            columns = original.copy()
            columns[0] = "0"  # Renumbered when presegmented CoNLL-U is built.
            columns[1] = form
            columns[2:9] = ["_"] * 7
            columns[9] = replace_token_range(
                original[9], absolute_start, absolute_end,
                force_no_space=part_index < len(split_points) - 1,
            )
            row = ConlluRow(columns)
            repaired.append(OrthographicToken(form, absolute_start, absolute_end, None, [row]))
    return repaired


def is_terminal(token: OrthographicToken) -> bool:
    return bool(token.form) and any(char in TERMINAL_CHARS for char in token.form) and all(
        char in TERMINAL_CHARS for char in token.form
    )


def is_abbreviation_period(text: str, tokens: list[OrthographicToken], index: int) -> bool:
    """Disambiguate periods internal to abbreviations, numbers and URLs."""

    token = tokens[index]
    if token.form != "." or index == 0:
        return False
    previous = tokens[index - 1]
    following = tokens[index + 1] if index + 1 < len(tokens) else None
    attached_left = previous.end == token.start
    attached_right = following is not None and token.end == following.start
    if not attached_left:
        return False

    previous_form = previous.form.casefold()
    if previous_form in ABBREVIATIONS:
        return True
    if previous.form.isalpha() and len(previous.form) == 1 and previous.form.isupper():
        return True
    if following and previous.form.isdigit() and following.form.isdigit() and attached_right:
        return True

    # Covers dotted domains/e-mail fragments without treating a final URL
    # punctuation mark as internal to the address.
    left = text[max(0, previous.start - 64):token.start]
    right = text[token.end:min(len(text), token.end + 64)]
    if attached_right and re.search(r"(?:https?://|www\.|\S+@)\S*$", left, re.IGNORECASE):
        return bool(re.match(r"[\w%-]", right))
    return False


def segment_tokens(text: str, tokens: list[OrthographicToken]) -> list[list[OrthographicToken]]:
    """Apply deterministic DOESTE-PT sentence-boundary disambiguation.

    UDPipe's raw sentence blocks are deliberately ignored. Boundaries are
    inferred from terminal punctuation plus Portuguese abbreviation, quote,
    title, numeric, URL and dash context. Paragraph end is always a boundary.
    """

    boundaries: list[int] = []
    index = 0
    while index < len(tokens):
        if not is_terminal(tokens[index]) or is_abbreviation_period(text, tokens, index):
            index += 1
            continue

        boundary = index
        while boundary + 1 < len(tokens) and tokens[boundary + 1].form in CLOSING_MARKS:
            boundary += 1
        following = boundary + 1

        # Punctuation inside a title/quotation followed by comma, semicolon or
        # colon is not the end of the containing sentence.
        if following < len(tokens) and tokens[following].form in CONTINUATION_MARKS:
            index = boundary + 1
            continue

        # A closing quote followed directly by a lower-case continuation is
        # normally a quoted title or embedded citation, not a sentence break.
        if boundary > index and following < len(tokens) and tokens[following].form[:1].islower():
            index = boundary + 1
            continue

        # Quoted speech followed by a reporting clause introduced by a dash
        # remains one sentence (e.g. “...?” — afirmou o autor).
        if boundary > index and following < len(tokens) and tokens[following].form in DASHES:
            after_dash = following + 1
            if after_dash < len(tokens) and tokens[after_dash].form[:1].islower():
                index = following + 1
                continue

        boundaries.append(boundary + 1)
        index = boundary + 1

    if not boundaries or boundaries[-1] != len(tokens):
        boundaries.append(len(tokens))

    sentences: list[list[OrthographicToken]] = []
    start = 0
    for end in boundaries:
        if end > start:
            sentences.append(tokens[start:end])
        start = end
    if start != len(tokens):
        raise ValueError("Sentence segmentation did not cover every token")
    return sentences


def presegmented_conllu(sentences: list[list[OrthographicToken]]) -> str:
    """Serialize fixed tokens/sentences for UDPipe tagging and parsing."""

    blocks: list[str] = []
    for sentence_number, sentence in enumerate(sentences, 1):
        lines = [f"# sent_id = {sentence_number}"]
        next_word_id = 1
        for token in sentence:
            if token.token_row is not None:
                first = next_word_id
                last = first + len(token.word_rows) - 1
                columns = token.token_row.columns.copy()
                columns[0] = f"{first}-{last}"
                columns[2:9] = ["_"] * 7
                lines.append("\t".join(columns))
                for component in token.word_rows:
                    columns = component.columns.copy()
                    columns[0] = str(next_word_id)
                    columns[2:9] = ["_"] * 7
                    lines.append("\t".join(columns))
                    next_word_id += 1
            else:
                columns = token.word_rows[0].columns.copy()
                columns[0] = str(next_word_id)
                columns[2:9] = ["_"] * 7
                lines.append("\t".join(columns))
                next_word_id += 1
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def annotate_text(text: str) -> tuple[str, set[str]]:
    """Run tokenization, DOESTE-PT segmentation, then UD analysis."""

    tokenized, tokenizer_model = tokenize_paragraph(text)
    tokens = parse_tokenized_conllu(tokenized)
    tokens = repair_embedded_terminal_tokens(text, tokens)
    sentences = segment_tokens(text, tokens)
    conllu = presegmented_conllu(sentences)
    analysed, analysis_model = analyse_presegmented(conllu)
    return analysed, {tokenizer_model, analysis_model}


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
        conllu, paragraph_models = annotate_text(text)
        resolved_models.update(paragraph_models)
        new, sentence_number, token_number = annotate_paragraph(text, conllu, old.get(f"{{{XML}}}id"), sentence_number, token_number)
        old.getparent().replace(old, new)
    if len(resolved_models) != 1:
        raise ValueError(f"Inconsistent UDPipe model versions in one document: {sorted(resolved_models)}")
    resolved_model = next(iter(resolved_models))
    revision = result.xpath("//tei:revisionDesc", namespaces=NS)[0]
    change = etree.SubElement(revision, f"{{{TEI}}}change", who="DOESTE_UDPIPE_PIPELINE")
    change.set("when", datetime.now(timezone.utc).isoformat())
    change.text = (
        f"Automatic lossless tokenization, DOESTE-controlled sentence segmentation, and UD annotation "
        f"(requested_model={MODEL}; resolved_model={resolved_model}; tokenizer=ranges; "
        f"sentence_segmenter={SENTENCE_SEGMENTER}; analysis_input=conllu); "
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
