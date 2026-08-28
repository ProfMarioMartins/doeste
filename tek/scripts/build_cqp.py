#!/usr/bin/env python3
"""Build the surface-faithful TEK CQP corpus for TEITOK."""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
from pathlib import Path

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}
PATTRS = ("lemma", "upos", "feats", "head", "deprel")
SATTRS = ("id", "year", "theme", "author", "score", "language", "domain", "purpose", "corpus", "source")


def scalar(tree: etree._ElementTree, xpath: str) -> str:
    return str(tree.xpath(f"string({xpath})", namespaces=NS)).strip()


def safe(value: str | None) -> str:
    if not value:
        return "__UNDEF__"
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ")


def xml_attribute(value: str) -> str:
    return html.escape(value, quote=True)


def local_id(element: etree._Element) -> str:
    return element.get("id") or element.get(f"{{{XML}}}id")


def token_value(token: etree._Element, attribute: str) -> str:
    dtoks = token.xpath("./tei:dtok", namespaces=NS)
    if not dtoks:
        return safe(token.get(attribute))
    return safe("+".join(safe(dtok.get(attribute)) for dtok in dtoks))


def metadata(tree: etree._ElementTree) -> dict[str, str]:
    return {
        "id": tree.getroot().get(f"{{{XML}}}id"),
        "year": scalar(tree, "//tei:setting/tei:date[@type='exam']/@when"),
        "theme": scalar(tree, "//tei:keywords[@type='official_prompt']/tei:term"),
        "author": scalar(tree, "//tei:titleStmt/tei:author"),
        "score": scalar(tree, "//tei:keywords[@type='score']/tei:term"),
        "language": scalar(tree, "//tei:language/@ident"),
        "domain": scalar(tree, "//tei:keywords[@type='domain']/tei:term"),
        "purpose": scalar(tree, "//tei:textDesc/tei:purpose"),
        "corpus": scalar(tree, "//tei:keywords[@type='corpus']/tei:term"),
        "source": scalar(tree, "//tei:sourceDesc/tei:bibl[1]/tei:publisher"),
    }


def write_vertical(xml_dir: Path, vertical: Path) -> tuple[int, int]:
    files = sorted(xml_dir.glob("TEK_*.xml"))
    if len(files) != 128:
        raise ValueError(f"Expected 128 annotated XML files, found {len(files)}")
    token_count = sentence_count = 0
    with vertical.open("w", encoding="utf-8", newline="\n") as output:
        for path in files:
            tree = etree.parse(str(path))
            meta = metadata(tree)
            if any(not value for value in meta.values()):
                raise ValueError(f"Missing required CQP metadata in {path.name}: {meta}")
            attrs = " ".join(f'{key}="{xml_attribute(meta[key])}"' for key in SATTRS)
            output.write(f"<text {attrs}>\n")
            for paragraph in tree.xpath("//tei:body/tei:p", namespaces=NS):
                paragraph_id = local_id(paragraph)
                output.write(f'<p id="{xml_attribute(paragraph_id)}">\n')
                for sentence in paragraph.xpath("./tei:s", namespaces=NS):
                    sentence_count += 1
                    sentence_id = local_id(sentence)
                    output.write(f'<s id="{xml_attribute(sentence_id)}">\n')
                    for token in sentence.xpath("./tei:tok", namespaces=NS):
                        word = safe(token.text)
                        columns = [word, *(token_value(token, attribute) for attribute in PATTRS)]
                        output.write("\t".join(columns) + "\n")
                        token_count += 1
                    output.write("</s>\n")
                output.write("</p>\n")
            output.write("</text>\n")
    return token_count, sentence_count


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd)


def validate_outputs(cqp_dir: Path, require_xidx: bool) -> None:
    required = [cqp_dir / "tek", cqp_dir / "word.corpus"]
    if require_xidx:
        required.append(cqp_dir / "xidx.rng")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("CQP build did not produce required files: " + ", ".join(missing))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, default=Path(__file__).resolve().parents[1] / "xmlfiles")
    parser.add_argument("--cqp", type=Path, default=Path(__file__).resolve().parents[1] / "cqp")
    parser.add_argument(
        "--local-validation", action="store_true",
        help="use plain cwb-encode for local CQP checks only; does not produce TEITOK XIDX",
    )
    parser.add_argument("--tt-encoder", default="tt-cwb-encode")
    args = parser.parse_args()

    cqp_dir = args.cqp.resolve()
    tek_root = Path(__file__).resolve().parents[1]
    if cqp_dir.parent != tek_root:
        raise ValueError(f"Refusing to rebuild outside the TEK root: {cqp_dir}")
    tt_encoder = None
    if not args.local_validation:
        tt_encoder = shutil.which(args.tt_encoder)
        if tt_encoder is None:
            raise RuntimeError(
                f"{args.tt_encoder} is required for a production TEITOK build because "
                "plain cwb-encode does not generate xidx.rng. Use --local-validation "
                "only for non-production CQP checks."
            )
    # The production TEITOK runtime expects both the registry and CWB binary
    # files directly in the configured registryfolder/cqpfolder (tek/cqp).
    # The whole directory is derived, so rebuild it atomically from the TEI.
    if cqp_dir.exists():
        shutil.rmtree(cqp_dir)
    cqp_dir.mkdir(parents=True)
    vertical_dir = cqp_dir / "vertical"
    vertical_dir.mkdir()
    vertical = vertical_dir / "tek.vrt"
    # TEITOK resolves registryfolder="cqp" relative to the corpus root and
    # therefore expects this file at tek/cqp/tek (not cqp/registry/tek).
    registry = cqp_dir / "tek"

    token_count, sentence_count = write_vertical(args.xml.resolve(), vertical)
    if args.local_validation:
        print(
            "LOCAL VALIDATION ONLY: plain cwb-encode does not generate xidx.rng "
            "and this output is not suitable for TEITOK production."
        )
        encode = [
            "cwb-encode", "-f", str(vertical), "-d", str(cqp_dir), "-R", str(registry),
            "-c", "utf8", "-x", "-s",
            "-P", "lemma", "-P", "upos", "-P", "feats", "-P", "head", "-P", "deprel",
            "-S", "text:0+id+year+theme+author+score+language+domain+purpose+corpus+source",
            "-S", "p:0+id", "-S", "s:0+id",
        ]
        run(encode)
    else:
        # tt-cwb-encode resolves Resources/settings.xml, xmlfiles/ and cqp/
        # relative to the corpus project, so it must run from the TEK root.
        run([tt_encoder], cwd=tek_root)

    run(["cwb-makeall", "-r", str(cqp_dir), "TEK"])
    validate_outputs(cqp_dir, require_xidx=not args.local_validation)
    mode = "local-validation" if args.local_validation else "teitok-production"
    print(
        f"Built TEK CQP corpus: mode={mode}, tokens={token_count}, "
        f"sentences={sentence_count}, registry={registry}"
    )


if __name__ == "__main__":
    main()
