import subprocess
import sys
from pathlib import Path

from data_estate.validate import check

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_gen(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "data_estate.generate", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_batch_two_seeds_write_company_dirs(tmp_path: Path):
    b = tmp_path / "b"
    proc = run_gen("--seed", "500", "--n", "2", "--out", str(b))
    assert proc.returncode == 0, proc.stderr
    for seed in (500, 501):
        out = b / f"company_{seed}"
        assert (out / "invoices.csv").exists(), f"missing {out}"
        assert check(out) == [], f"seed {seed} invalid: {check(out)[:3]}"


def test_n_one_writes_to_out_directly(tmp_path: Path):
    single = tmp_path / "single"
    proc = run_gen("--seed", "7", "--n", "1", "--out", str(single))
    assert proc.returncode == 0, proc.stderr
    assert (single / "invoices.csv").exists()
    assert not (single / "company_7").exists()


def test_n_zero_or_negative_exits_nonzero(tmp_path: Path):
    for n in ("0", "-1"):
        proc = run_gen("--seed", "7", "--n", n, "--out", str(tmp_path / "x"))
        assert proc.returncode != 0, f"--n {n} should exit non-zero"
