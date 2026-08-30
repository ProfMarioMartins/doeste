#!/usr/bin/env python3
"""Integration checks for the shared UFERSA institutional logo."""

from hashlib import sha256
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
LOGO_URL = "/shared/Resources/logo_ufersa_doeste.png"
EXPECTED_SHA256 = "2111b801bb8c5a6b74ac6c376244f59236c4c83847282858839af85fdac48e0b"
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
    logo = ROOT / "shared/Resources/logo_ufersa_doeste.png"
    assert logo.is_file()
    assert sha256(logo.read_bytes()).hexdigest() == EXPECTED_SHA256

    versions = {
        shared_css_version(path.read_text(encoding="utf-8"))
        for path in TEMPLATES
    }
    assert len(versions) == 1, "all templates must use the same doeste.css version"

    for corpus in ("ted", "tek", "tej"):
        template = (ROOT / corpus / "templates/main.tpl").read_text(encoding="utf-8")
        assert template.count(LOGO_URL) == 1
        assert template.index("institution-logo") < template.index("brand-title")
        personal_path_prefix = "/" + "Users/" + "mariomartins2/"
        assert personal_path_prefix not in template

    css = (ROOT / "shared/Resources/doeste.css").read_text(encoding="utf-8")
    rule = css[css.index(".layout .sidebar .institution-logo") :]
    for declaration in ("width: 100%", "max-width: 210px", "height: auto", "margin: 0 auto 18px"):
        assert declaration in rule

    print("institutional-logo=valid")


if __name__ == "__main__":
    main()
