"""The frozen datasets (AGENTS.md). Any byte change fails these tests.

company_42 is our legacy CSV layout; estate_42 is the same seed exported to the
judges' estate_schema.sql (#80). Both are committed so a demo, a score and a judge's
own validator run always see identical bytes, and so a change to the generator that would
silently move an answer is caught here rather than on stage.

If you believe one must change, open an issue labelled needs-human. Do not update EXPECTED.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data_estate" / "out"
FROZEN = ROOT / "company_42"
EXPECTED = "c44f08440288f7f39a442911f294d1dd91d31b7fc423057160950c5a8d1818f4"
FROZEN_JUDGES = ROOT / "estate_42"
EXPECTED_JUDGES = "a02375a71ee9bdfe0d08f4c3a961c591a057091a9c73828fe572089875c799be"


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def test_company_42_is_frozen():
    assert FROZEN.is_dir(), "frozen dataset missing"
    assert digest(FROZEN) == EXPECTED, "data_estate/out/company_42 changed. It is frozen; generate elsewhere."


def test_estate_42_is_frozen():
    """The judges'-schema export of seed 42, including its SQLite file, is byte-stable."""
    assert FROZEN_JUDGES.is_dir(), "frozen judges' estate missing"
    assert digest(FROZEN_JUDGES) == EXPECTED_JUDGES, (
        "data_estate/out/estate_42 changed. It is frozen; export elsewhere with "
        "--format judges --out data_estate/out/estate_<seed>."
    )
