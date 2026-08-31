#!/usr/bin/env python3
"""Static integration checks for the DOESTE visit counter."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
CORPORA = ("ted", "tek", "tej")
MARKER = "<!-- DOESTE_VISIT_COUNTER -->"
TEMPLATES = (
    ROOT / "shared/templates/main.tpl",
    ROOT / "ted/templates/main.tpl",
    ROOT / "tek/templates/main.tpl",
    ROOT / "tej/templates/main.tpl",
)


def shared_css_version(template: str) -> str:
    matches = re.findall(r'href="/shared/Resources/doeste\.css\?v=([^"]+)"', template)
    assert len(matches) == 1, "template must load one versioned doeste.css"
    assert matches[0].strip(), "doeste.css cache version must not be empty"
    return matches[0]


def main() -> None:
    helper = (ROOT / "shared/Sources/visit-counter.php").read_text(encoding="utf-8")
    for required in ("flock", "LOCK_EX", "number_format", "$_SESSION", "HTTP_USER_AGENT"):
        assert required in helper, f"missing counter safeguard: {required}"

    versions = {
        shared_css_version(path.read_text(encoding="utf-8"))
        for path in TEMPLATES
    }
    assert len(versions) == 1, "all templates must use the same doeste.css version"

    css = (ROOT / "shared/Resources/doeste.css").read_text(encoding="utf-8")
    assert ".corpus-visit-counter" in css

    for corpus in CORPORA:
        home = (ROOT / corpus / "Pages/home.html").read_text(encoding="utf-8")
        assert home.count(MARKER) == 1, f"counter marker missing or duplicated: {corpus}"
        onload = (ROOT / corpus / "Sources/onload.php").read_text(encoding="utf-8")
        assert "shared/Sources/visit-counter.php" in onload
        assert f"'{corpus.upper()}'" in onload

    print("visit-counter-integration=valid")


if __name__ == "__main__":
    main()
