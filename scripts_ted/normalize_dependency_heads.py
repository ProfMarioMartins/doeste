#!/usr/bin/env python3
"""Normaliza referências de dependência nos XML derivados do TED.

Não executa UDPipe nem recalcula relações: converte exclusivamente heads
CoNLL-U locais para os @id XML dos tokens da mesma sentença.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import unicodedata
from lxml import etree


COLLISION_FILE = Path("Terceiro_Médio/nslm_1_12_eeoa.xml")


def sentence_nodes(sentence):
    dtoks = sentence.xpath(".//*[local-name()='dtok']")
    if dtoks:
        raise ValueError("TED atual não admite dtok na normalização de heads")
    return sentence.xpath("./*[local-name()='tok']")


def repair_known_collision(path: Path, root: Path, tree) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    if unicodedata.normalize("NFC", str(relative)) != str(COLLISION_FILE):
        return False

    sentences = tree.xpath("//*[local-name()='s' and @id='s-2']")
    if len(sentences) != 1:
        raise ValueError(f"{relative}: sentença s-2 não encontrada unicamente")
    nodes = sentence_nodes(sentences[0])
    if len(nodes) < 21:
        raise ValueError(f"{relative}: s-2 menor que o esperado")
    perto, do, mar = nodes[18:21]
    observed = [(x.text or "", x.get("id")) for x in (perto, do, mar)]
    expected = [("perto", "w-65"), ("do", "w-148"), ("mar", "w-65")]
    if observed == [("perto", "w-65"), ("do", "w-148"), ("mar", "w-149")]:
        return False
    if observed != expected:
        raise ValueError(f"{relative}: colisão não corresponde ao caso auditado: {observed}")
    all_ids = set(tree.xpath("//@id"))
    if "w-149" in all_ids:
        raise ValueError(f"{relative}: w-149 já existe")
    mar.set("id", "w-149")
    return True


def normalize_file(path: Path, root: Path, write: bool = True) -> tuple[bool, int]:
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(path), parser)
    changed = repair_known_collision(path, root, tree)
    converted = 0

    document_nodes = tree.xpath("//*[local-name()='tok' or local-name()='dtok']")
    document_ids = [node.get("id") for node in document_nodes]
    if any(not node_id for node_id in document_ids) or len(document_ids) != len(set(document_ids)):
        raise ValueError(f"{path}: IDs XML ausentes ou duplicados")

    for sentence in tree.xpath("//*[local-name()='s']"):
        nodes = sentence_nodes(sentence)
        ids = [node.get("id") for node in nodes]
        if any(not node_id for node_id in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"{path}: IDs inválidos na sentença {sentence.get('id')}")
        local_to_xml = {str(index): node_id for index, node_id in enumerate(ids, 1)}
        for node in nodes:
            head = node.get("head")
            if head is None or head == "0" or not head.isdigit():
                continue
            if head not in local_to_xml:
                raise ValueError(
                    f"{path}: head {head} fora da sentença {sentence.get('id')}"
                )
            node.set("head", local_to_xml[head])
            converted += 1
            changed = True

    if changed and write:
        tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=False)
    return changed, converted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("ted/xmlfiles"))
    parser.add_argument("--check", action="store_true", help="valida sem gravar")
    args = parser.parse_args()
    changed = converted = 0
    files = sorted(args.root.rglob("*.xml"))
    for path in files:
        file_changed, file_converted = normalize_file(path, args.root, not args.check)
        changed += int(file_changed)
        converted += file_converted
    print(f"documents={len(files)} changed={changed} heads_converted={converted}")


if __name__ == "__main__":
    main()
