#!/usr/bin/env python3
"""Normaliza apenas referências numéricas de dependência no TEJ.

Os XML de ``tej/xmlfiles`` são tratados como fonte protegida. O conversor é
estrito e idempotente: não executa análise linguística e não altera qualquer
atributo além de ``head``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from lxml import etree


def normalize_file(path: Path, write: bool = True) -> tuple[bool, int]:
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(path), parser)
    if tree.xpath("//*[local-name()='dtok']"):
        raise ValueError(f"{path}: dtok inesperado; conversão recusada")

    document_ids = tree.xpath("//*[local-name()='tok']/@id")
    token_count = len(tree.xpath("//*[local-name()='tok']"))
    if len(document_ids) != token_count or len(document_ids) != len(set(document_ids)):
        raise ValueError(f"{path}: @id XML ausente ou duplicado")

    changed = False
    converted = 0
    for sentence in tree.xpath("//*[local-name()='s']"):
        nodes = sentence.xpath("./*[local-name()='tok']")
        ids = [node.get("id") for node in nodes]
        if any(not node_id for node_id in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"{path}: IDs inválidos na sentença {sentence.get('id')}")
        local_to_xml = {str(index): node_id for index, node_id in enumerate(ids, 1)}
        for node in nodes:
            head = node.get("head")
            if head is None or head == "0":
                continue
            if not head.isdigit():
                if head not in ids:
                    raise ValueError(
                        f"{path}: head XML {head!r} fora da sentença {sentence.get('id')}"
                    )
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
    parser.add_argument("root", type=Path, nargs="?", default=Path("tej/xmlfiles"))
    parser.add_argument("--check", action="store_true", help="valida sem gravar")
    args = parser.parse_args()
    files = sorted(args.root.rglob("*.xml"))
    changed = converted = 0
    for path in files:
        file_changed, file_converted = normalize_file(path, not args.check)
        changed += int(file_changed)
        converted += file_converted
    print(f"documents={len(files)} changed={changed} heads_converted={converted}")


if __name__ == "__main__":
    main()
