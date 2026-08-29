#!/usr/bin/env python3
"""Static integration checks for the DOESTE visit counter."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORPORA = ("ted", "tek", "tej")
MARKER = "<!-- DOESTE_VISIT_COUNTER -->"


def main() -> None:
    helper = (ROOT / "shared/Sources/visit-counter.php").read_text(encoding="utf-8")
    for required in ("flock", "LOCK_EX", "number_format", "$_SESSION", "HTTP_USER_AGENT"):
        assert required in helper, f"missing counter safeguard: {required}"

    css = (ROOT / "shared/Resources/doeste.css").read_text(encoding="utf-8")
    assert ".corpus-visit-counter" in css

    for corpus in CORPORA:
        home = (ROOT / corpus / "Pages/home.html").read_text(encoding="utf-8")
        assert home.count(MARKER) == 1, f"counter marker missing or duplicated: {corpus}"
        onload = (ROOT / corpus / "Sources/onload.php").read_text(encoding="utf-8")
        assert "shared/Sources/visit-counter.php" in onload
        assert f"'{corpus.upper()}'" in onload
        template = (ROOT / corpus / "templates/main.tpl").read_text(encoding="utf-8")
        assert "/shared/Resources/doeste.css?v=5" in template

    print("visit-counter-integration=valid")


if __name__ == "__main__":
    main()
