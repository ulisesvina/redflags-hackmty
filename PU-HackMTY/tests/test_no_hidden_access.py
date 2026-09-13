"""tests/test_no_hidden_access.py (#28): mechanically enforce AGENTS.md rule 2.

Rule 2 says ``agent/`` must never read ``hidden/``. Today that is checked by eye; this
module makes it a test that fails the PR. It must catch two traps (and more):

  1. a string path to ``hidden/ground_truth.json``;
  2. the sneaky one: ``from data_estate.validate import load`` or
     ``from data_estate.score import score``. Both read ``hidden/ground_truth.json``
     internally, so an agent module importing them would see the ground truth without
     ever spelling ``hidden``.

The **static** part below has no dependencies and always runs. It parses every ``*.py``
under ``agent/`` (recursive) plus ``scripts/check_llm.py`` and fails on:
  * any ``Import`` / ``ImportFrom`` of a module starting with ``data_estate``
    (the agent package must not touch the generator/validator/scorer at all);
  * any string constant containing ``hidden`` or ``ground_truth``, EXCEPT docstrings
    (``agent/__init__.py``'s docstring mentions ``hidden/`` on purpose);
  * any ``open``/``Path``/``read_text``/``read_bytes``/``read_csv``/``read_json``/
    ``json.load`` call whose string-literal argument contains ``hidden``.

The **runtime** part is guarded with ``pytest.importorskip("agent.data")`` so it skips
until #2 lands. An audit hook proves ``agent.data.load`` (on the real company_42) and
every detector never open anything under ``hidden/``.
"""
from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
SCRIPTS_DIR = ROOT / "scripts"
CHECK_LLM = ROOT / "scripts" / "check_llm.py"
COMPANY_42 = ROOT / "data_estate" / "out" / "company_42"

CSV_STEMS = (
    "suppliers",
    "customers",
    "employees",
    "invoices",
    "goods_receipts",
    "bank_transactions",
    "counterparty_bank",
    "ledger",
    "efos_69b",
)

_FORBIDDEN_MODULE_PREFIX = "data_estate"
_FORBIDDEN_STRINGS = ("hidden", "ground_truth")
_OPEN_CALL_LEAVES = {"open", "Path", "read_text", "read_bytes", "read_csv", "read_json"}
_JSON_LOAD = "json.load"


# --------------------------------------------------------------------------- helpers
def _source_files() -> list[Path]:
    """agent/ (recursive) plus scripts/check_llm.py."""
    files = sorted(AGENT_DIR.rglob("*.py"))
    files.append(CHECK_LLM)
    return files


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """ids of the Constant nodes that are Module/Class/Function docstrings."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def _call_leaf(call: ast.Call) -> str | None:
    """Canonical name of a file-opening call, or None if it is not one we track."""
    f = call.func
    if isinstance(f, ast.Name):
        return f.id if f.id in _OPEN_CALL_LEAVES else None
    if isinstance(f, ast.Attribute):
        if f.attr in _OPEN_CALL_LEAVES:
            return f.attr
        # json.load(...) strictly; not json.loads.
        if f.attr == "load" and isinstance(f.value, ast.Name) and f.value.id == "json":
            return _JSON_LOAD
    return None


def _scan_file(path: Path, want: str) -> list[str]:
    """Return violations of rule ``want`` (one of 'import', 'string', 'open') in ``path``."""
    violations: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    doc_ids = _docstring_node_ids(tree)

    for node in ast.walk(tree):
        if want == "import":
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == _FORBIDDEN_MODULE_PREFIX:
                        violations.append(
                            f"{path}:{node.lineno}: forbidden import of data-side module {alias.name!r}"
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".")[0] == _FORBIDDEN_MODULE_PREFIX:
                    violations.append(
                        f"{path}:{node.lineno}: forbidden from-import of data-side module {mod!r}"
                    )
        elif want == "string":
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in doc_ids
            ):
                if any(bad in node.value for bad in _FORBIDDEN_STRINGS):
                    violations.append(
                        f"{path}:{node.lineno}: string constant mentions forbidden path {node.value!r}"
                    )
        elif want == "open":
            if isinstance(node, ast.Call):
                leaf = _call_leaf(node)
                if leaf is not None:
                    for arg in node.args:
                        if (
                            isinstance(arg, ast.Constant)
                            and isinstance(arg.value, str)
                            and "hidden" in arg.value
                        ):
                            violations.append(
                                f"{path}:{node.lineno}: {leaf} call opens hidden path {arg.value!r}"
                            )
    return violations


# --------------------------------------------------------------- static, no deps
def test_agent_and_check_llm_never_import_data_estate():
    """Agent modules and check_llm.py must never import the data side (generator/validator/scorer)."""
    violations: list[str] = []
    for path in _source_files():
        violations.extend(_scan_file(path, "import"))
    assert violations == [], "\n".join(violations)


def test_agent_and_check_llm_never_mention_hidden_or_ground_truth():
    """No string constant outside docstrings may mention `hidden` or `ground_truth`."""
    violations: list[str] = []
    for path in _source_files():
        violations.extend(_scan_file(path, "string"))
    assert violations == [], "\n".join(violations)


def test_agent_and_check_llm_never_open_a_hidden_path():
    """No file-opening call may pass a string literal pointing at `hidden/`."""
    violations: list[str] = []
    for path in _source_files():
        violations.extend(_scan_file(path, "open"))
    assert violations == [], "\n".join(violations)


# ------------------------------------------------------- (95) ground_truth grep
# The judges grep the source tree for `ground_truth` and it caps the score at 2,
# so no file under agent/ or scripts/ may contain the string at all. The only
# exceptions are the vendored judge harness (scripts/judges/, #88) and
# scripts/eval_batch.py (#86), which legitimately name the judges' ground truth.
_HARNESS_EXCLUDES = ("scripts/eval_batch.py",)


def _is_harness(rel: Path) -> bool:
    """Return whether a path under ROOT is a vendored judge/harness file."""
    posix = rel.as_posix()
    if posix in _HARNESS_EXCLUDES:
        return True
    # everything under scripts/judges/ is judges' own code
    return len(rel.parts) >= 3 and rel.parts[0] == "scripts" and rel.parts[1] == "judges"


def _scan_for_ground_truth() -> list[str]:
    """Every text file under agent/ and scripts/ (minus the harness) containing 'ground_truth'."""
    offenders: list[str] = []
    for root in (AGENT_DIR, SCRIPTS_DIR):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT)
            if _is_harness(rel):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # binary (compiled .pyc etc.); not greppable source
            if "ground_truth" in text.lower():
                offenders.append(rel.as_posix())
    return offenders


def test_no_file_under_agent_or_scripts_mentions_ground_truth():
    """`ground_truth` may appear nowhere under agent/ or scripts/ except the judge harness."""
    offenders = _scan_for_ground_truth()
    assert offenders == [], "files mentioning 'ground_truth':\n" + "\n".join(offenders)


# ------------------------------------------------------------------- runtime part
# The audit hook cannot be removed, so it must only record and return fast. It appends
# to a module-level list; each test clears it first so cross-test contamination from an
# earlier `open` of hidden/ground_truth.json (e.g. via the conftest `truth` fixture)
# cannot cause a spurious failure.
_OPENED_HIDDEN: list[str] = []


def _audit_hook(event: str, args: tuple) -> None:
    if event == "open" and "hidden" in str(args[0]):
        _OPENED_HIDDEN.append(str(args[0]))


def test_agent_load_and_detectors_never_open_hidden():
    """Load company_42 and run every detector under an audit hook; neither may open hidden/."""
    pytest.importorskip("agent.data")
    import agent.data  # noqa: PLC0415
    import agent.detectors  # noqa: PLC0415

    _OPENED_HIDDEN.clear()
    sys.addaudithook(_audit_hook)
    ds = agent.data.load(COMPANY_42)
    if agent.detectors.DETECTORS:
        agent.detectors.run_all(ds)
    assert _OPENED_HIDDEN == [], f"agent opened hidden/ during load/run_all: {_OPENED_HIDDEN}"


def test_load_without_hidden_invoice_count(tmp_path):
    """A copy of company_42 with hidden/ removed still loads to exactly 597 invoices.

    tests/test_loader.py::test_load_without_hidden already checks that a hidden-free copy
    loads to the same row counts as the session `ds`; the absolute 597 here pins the count
    so a schema change that silently shifts it cannot slip through.
    """
    pytest.importorskip("agent.data")
    from agent.data import load  # noqa: PLC0415

    for stem in CSV_STEMS:
        shutil.copy(COMPANY_42 / f"{stem}.csv", tmp_path / f"{stem}.csv")
    shutil.copy(COMPANY_42 / "company.json", tmp_path / "company.json")
    assert not (tmp_path / "hidden").exists()
    ds = load(tmp_path)
    assert len(ds.invoices) == 597
