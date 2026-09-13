import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_requirements_declares_runtime_and_test_dependencies():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements == ["pandas", "pytest", "ruff", "openai>=1.40"]


def test_make_test_uses_available_project_python():
    result = subprocess.run(
        ["make", "--no-print-directory", "-n", "test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    expected_python = ".venv/bin/python" if (ROOT / ".venv/bin/python").exists() else "python"
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"{expected_python} -m pytest -q"]


def test_make_gen_defaults_to_seed_7():
    result = subprocess.run(
        ["make", "--no-print-directory", "gen", "PYTHON=/bin/echo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == (
        "-m data_estate.generate --seed 7 --out data_estate/out/company_7"
    )


def test_make_gen_refuses_frozen_seed_42():
    result = subprocess.run(
        ["make", "--no-print-directory", "gen", "SEED=42", "PYTHON=/bin/true"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "company_42 is frozen" in result.stderr


def test_make_gen_rejects_seed_with_injected_output_argument():
    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            "gen",
            "SEED=7 --out data_estate/out/company_42",
            "PYTHON=/bin/true",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SEED must be a non-negative integer" in result.stderr


def test_make_score_uses_frozen_dataset_and_example_case_file():
    result = subprocess.run(
        ["make", "--no-print-directory", "-n", "score", "PYTHON=.venv/bin/python"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        ".venv/bin/python -m data_estate.score data_estate/out/company_42 "
        "data_estate/out/example_case_file_for_seed42.json"
    ]
