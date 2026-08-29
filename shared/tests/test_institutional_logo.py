#!/usr/bin/env python3
"""Integration checks for the shared UFERSA institutional logo."""

from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGO_URL = "/shared/Resources/logo_ufersa_doeste.png"
EXPECTED_SHA256 = "2111b801bb8c5a6b74ac6c376244f59236c4c83847282858839af85fdac48e0b"


def main() -> None:
    logo = ROOT / "shared/Resources/logo_ufersa_doeste.png"
    assert logo.is_file()
    assert sha256(logo.read_bytes()).hexdigest() == EXPECTED_SHA256

    for corpus in ("ted", "tek", "tej"):
        template = (ROOT / corpus / "templates/main.tpl").read_text(encoding="utf-8")
        assert template.count(LOGO_URL) == 1
        assert template.index("institution-logo") < template.index("brand-title")
        assert "/shared/Resources/doeste.css?v=5" in template
        personal_path_prefix = "/" + "Users/" + "mariomartins2/"
        assert personal_path_prefix not in template

    css = (ROOT / "shared/Resources/doeste.css").read_text(encoding="utf-8")
    rule = css[css.index(".layout .sidebar .institution-logo") :]
    for declaration in ("width: 100%", "max-width: 210px", "height: auto", "margin: 0 auto 18px"):
        assert declaration in rule

    print("institutional-logo=valid")


if __name__ == "__main__":
    main()
