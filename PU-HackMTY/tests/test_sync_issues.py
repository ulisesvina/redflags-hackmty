"""scripts/sync_issues.py (#30): builds docs/ISSUES.md from canned gh output, no network."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_issues", ROOT / "scripts" / "sync_issues.py")
sync_issues = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_issues)

ISSUES = [
    {
        "number": 15,
        "title": "requirements.txt + Makefile",
        "state": "CLOSED",
        "labels": [{"name": "hermes-ok"}],
        "body": "## Goal\nPin the deps.\n\n- [x] done  \n",
        "url": "https://github.com/o/r/issues/15",
    },
    {
        "number": 2,
        "title": "Loader module agent/data.py",
        "state": "OPEN",
        "labels": [{"name": "cc"}],
        "body": "Load CSVs with dtype=str.",
        "url": "https://github.com/o/r/issues/2",
    },
]
PRS = [
    {
        "number": 19,
        "title": "#15 Add requirements and Makefile commands",
        "state": "OPEN",
        "headRefName": "hermes/15",
        "url": "https://github.com/o/r/pull/19",
    }
]


class FakeCompleted:
    def __init__(self, stdout: str):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0


def fake_run(cmd, **kwargs):
    assert cmd[0] == "gh"
    payload = ISSUES if cmd[1] == "issue" else PRS
    return FakeCompleted(json.dumps(payload))


def test_build_markdown_table_bodies_and_determinism():
    text = sync_issues.build_markdown(ISSUES, PRS, today="2026-09-12")
    lines = text.splitlines()
    assert lines[0].startswith("# Issue queue — snapshot of the GitHub issues (regenerated 2026-09-12).")
    rows = [line for line in lines if re.match(r"^\| #\d", line)]
    assert rows == [
        "| #2 | OPEN | `cc` | Loader module agent/data.py |  |",
        "| #15 | CLOSED | `hermes-ok` | requirements.txt + Makefile | #19 (open) |",
    ]
    assert "## #2 Loader module agent/data.py  `cc`  OPEN\n\nLoad CSVs with dtype=str." in text
    assert "## #15 requirements.txt + Makefile  `hermes-ok`  CLOSED\n\n## Goal\nPin the deps.\n\n- [x] done\n" in text
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert "\n\n\n" not in text
    assert sync_issues.build_markdown(ISSUES, PRS, today="2026-09-12") == text


def test_main_writes_and_check_detects_drift(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run)
    out = tmp_path / "ISSUES.md"

    assert sync_issues.main(["--out", str(out)]) == 0
    assert out.exists()
    assert sync_issues.main(["--out", str(out), "--check"]) == 0

    out.write_text(out.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    assert sync_issues.main(["--out", str(out), "--check"]) == 1


def test_main_via_sys_argv(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run)
    out = tmp_path / "ISSUES.md"
    monkeypatch.setattr(sys, "argv", ["sync_issues.py", "--out", str(out)])
    assert sync_issues.main() == 0
    assert "| #15 | CLOSED |" in out.read_text(encoding="utf-8")


def test_gh_failure_exits_2_without_writing(tmp_path: Path, monkeypatch):
    def failing_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, output="", stderr="gh: not logged in")

    monkeypatch.setattr(subprocess, "run", failing_run)
    out = tmp_path / "ISSUES.md"
    assert sync_issues.main(["--out", str(out)]) == 2
    assert not out.exists()


@pytest.mark.parametrize("state", ["MERGED", "CLOSED"])
def test_pr_state_is_lowercased(state):
    prs = [dict(PRS[0], state=state)]
    text = sync_issues.build_markdown(ISSUES, prs, today="2026-09-12")
    assert f"| #19 ({state.lower()}) |" in text
