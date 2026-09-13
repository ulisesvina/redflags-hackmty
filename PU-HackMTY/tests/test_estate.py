import json
from pathlib import Path

from data_estate.generate import Generator, write_estate
from data_estate.validate import check


def test_seeds_validate(tmp_path: Path):
    for seed in (1, 2, 3):
        e = Generator(seed).build(["efos", "kickback", "roundtrip", "duplicate"])
        write_estate(e, tmp_path / f"c{seed}")
        assert check(tmp_path / f"c{seed}") == []


def test_clean_books(tmp_path: Path):
    e = Generator(9).build([])
    write_estate(e, tmp_path / "clean")
    assert check(tmp_path / "clean") == []
    assert e.truth["schemes"] == []


def test_deterministic():
    a = Generator(11).build(["efos"])
    b = Generator(11).build(["efos"])
    assert [i.uuid for i in a.invoices] == [i.uuid for i in b.invoices]


def test_sparse_category_seeds(tmp_path: Path):
    """Seeds with no drawn `logistica`/`consumibles` supplier must not crash (issue #24)."""
    for seed in (13, 34, 74):
        e = Generator(seed).build(["efos", "kickback", "roundtrip", "duplicate"])
        out = tmp_path / f"c{seed}"
        write_estate(e, out)
        assert check(out) == []
        ground_truth = json.loads((out / "hidden" / "ground_truth.json").read_text())
        assert len(ground_truth["decoys"]) == 5


def test_seed_42_unchanged(tmp_path: Path):
    """Company_42 stays byte-identical; the new fallback branches never alter a working seed."""
    from tests.test_frozen_dataset import EXPECTED, digest

    e = Generator(42).build(["efos", "kickback", "roundtrip", "duplicate"])
    out = tmp_path / "c42"
    write_estate(e, out)
    assert digest(out) == EXPECTED
