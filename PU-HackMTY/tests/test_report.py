"""tests/test_report.py (#23, rewritten for #90): the case file a judge reads.

`case_file_structure.md` fixes five sections in order, seven elements per finding, and is
explicit that the money trail must be **a rendered diagram, not prose** — prose-only caps
Clarity at 3. It also says the file must be producible **with no network call**, because
judges may ask for that with the Wi-Fi off. Every one of those is asserted here.

The reference case file `data_estate/out/example_case_file_for_seed42.json` stays the
contract for `exposure()` and `money_trail()`, which survive from #23 as the bonus
tax-exposure estimate.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from agent.data import load
from agent.investigate import run
from agent.report import exposure, mermaid, money_trail, render, render_html, svg

ROOT = Path(__file__).resolve().parents[1]
COMPANY_42 = ROOT / "data_estate" / "out" / "company_42"
EXAMPLE_FILE = ROOT / "data_estate" / "out" / "example_case_file_for_seed42.json"

SECTIONS = ["## Header", "## Executive summary", "## Findings", "## Leads not pursued", "## Method and limits"]
ELEMENTS = [
    "**Rule broken**",
    "**Amount and confidence**",
    "**What happened**",
    "**Money trail**",
    "**Exhibits**",
    "**Reconciliation**",
    "**Challenge**",
]


@pytest.fixture(scope="module")
def ds():
    return load(COMPANY_42)


@pytest.fixture(scope="module")
def example_case() -> dict:
    return json.loads(EXAMPLE_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    """A real no-LLM run on company_42, rendered both ways from its own submission."""
    tmp = tmp_path_factory.mktemp("report")
    case = run(
        COMPANY_42,
        out=str(tmp / "case.json"),
        log=str(tmp / "run.jsonl"),
        no_llm=True,
        submission=str(tmp / "submission.json"),
    )
    submission = json.loads((tmp / "submission.json").read_text(encoding="utf-8"))
    dataset = load(COMPANY_42)
    return {
        "case": case,
        "submission": submission,
        "ds": dataset,
        "md": render(case, dataset, submission=submission),
        "html": render_html(case, dataset, submission=submission),
    }


def _finding(case: dict, scheme_type: str) -> dict:
    for f in case["findings"]:
        if f["scheme_type"] == scheme_type:
            return f
    raise AssertionError(f"no finding {scheme_type}")


def _sections(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.startswith("## ")]


# --- the five required sections ----------------------------------------------
def test_the_five_sections_appear_once_each_in_order(rendered):
    assert _sections(rendered["md"]) == SECTIONS


def test_the_header_carries_the_run_numbers_a_judge_asks_for(rendered):
    header = rendered["md"].split("## Executive summary")[0]
    assert "Talleres Industriales del Norte SA de CV" in header
    assert "TIN091214KL3" in header
    assert "| Estate seed | 42 |" in header
    assert "| LLM calls | 0 |" in header
    assert "| Cost | MXN 0.00 |" in header
    assert re.search(r"\| Wall-clock \| \d+\.\d+ s \|", header)
    assert "| Deterministic | yes — no model was called" in header


def test_the_executive_summary_stands_alone(rendered):
    summary = rendered["md"].split("## Executive summary")[1].split("## Findings")[0]
    total = sum(float(f["peso_amount"]) for f in rendered["submission"]["findings"])
    assert "| Findings |" in summary and "proven" in summary
    assert f"| Total exposure | MXN {total:,.2f} |" in summary
    assert "| Leads investigated and closed |" in summary
    # The tax estimate stays, but never as the claimed amount.
    assert "Tax exposure (bonus estimate)" in summary
    assert "not part of any finding's claimed amount" in summary


def test_every_finding_section_has_the_seven_elements_in_order(rendered):
    body = rendered["md"].split("## Findings")[1].split("## Leads not pursued")[0]
    sections = body.split("\n### ")[1:]
    assert len(sections) == len(rendered["submission"]["findings"])
    for section in sections:
        positions = [section.find(element) for element in ELEMENTS]
        assert all(p >= 0 for p in positions), section[:200]
        assert positions == sorted(positions), "elements are out of order"


def test_finding_headings_name_the_entity_its_id_and_the_scheme_type(rendered):
    body = rendered["md"].split("## Findings")[1]
    for finding in rendered["submission"]["findings"]:
        heading = next(line for line in body.splitlines() if line.startswith("### ") and finding["scheme_type"] in line)
        for entity in finding["entities"]:
            assert entity in heading


# --- the money trail is a diagram --------------------------------------------
def test_each_finding_draws_its_money_trail_as_a_mermaid_graph(rendered):
    body = rendered["md"].split("## Findings")[1].split("## Leads not pursued")[0]
    blocks = re.findall(r"```mermaid\n(.*?)```", body, re.DOTALL)
    assert len(blocks) == len(rendered["submission"]["findings"])
    for block, finding in zip(blocks, rendered["submission"]["findings"]):
        assert block.startswith("flowchart LR")
        edges = [line for line in block.splitlines() if "-->" in line]
        assert len(edges) == len(finding["money_trail"])
        for step in finding["money_trail"]:
            assert step["exhibit_id"] in block


def test_the_money_trail_subsection_holds_the_diagram_and_nothing_else(rendered):
    body = rendered["md"].split("## Findings")[1].split("## Leads not pursued")[0]
    for chunk in body.split("**Money trail**")[1:]:
        between = chunk.split("**Exhibits**")[0].strip()
        assert between.startswith("```mermaid")
        assert between.endswith("```")


def test_mermaid_labels_cannot_be_broken_by_a_quote_in_a_name():
    trail = [{"from": 'O"Neil | SA', "to": "the company", "amount": 1.0, "date": "2025-01-01", "exhibit_id": "EX-01"}]
    block = mermaid(trail)
    assert '"' not in block.split("flowchart LR")[1].replace('["', "").replace('"]', "").replace('|"', "").replace('"|', "")


def test_svg_draws_one_column_per_party_and_one_arrow_per_step():
    trail = [
        {"from": "A", "to": "B", "amount": 10.0, "date": "2025-01-01", "exhibit_id": "EX-01"},
        {"from": "B", "to": "C", "amount": 9.0, "date": "2025-01-02", "exhibit_id": "EX-02"},
    ]
    drawing = svg(trail)
    assert drawing.count("<rect") == 3          # A, B, C
    assert drawing.count("marker-end") == 2     # one arrow per step
    assert "EX-01" in drawing and "EX-02" in drawing
    assert "xmlns" not in drawing               # an xmlns is a URL; the file must have none


def test_svg_survives_an_empty_trail():
    assert "<svg" in svg([])


# --- exhibits and reconciliation ----------------------------------------------
def test_the_exhibits_table_lists_every_exhibit_with_what_it_proves(rendered):
    body = rendered["md"].split("## Findings")[1]
    for finding in rendered["submission"]["findings"]:
        for exhibit in finding["exhibits"]:
            assert f"| {exhibit['exhibit_id']} | `{exhibit['source_table']}` | `{exhibit['record_id']}` |" in body
            assert exhibit["note"] in body


def test_the_reconciliation_arithmetic_adds_up_to_the_claim(rendered):
    """The line is the proof the amount is not asserted: it must actually sum."""
    body = rendered["md"].split("## Findings")[1].split("## Leads not pursued")[0]
    lines = [
        chunk.split("**Challenge**")[0].strip()
        for chunk in body.split("**Reconciliation**")[1:]
    ]
    assert len(lines) == len(rendered["submission"]["findings"])
    for line, finding in zip(lines, rendered["submission"]["findings"]):
        terms = [float(t.replace(",", "")) for t in re.findall(r"EX-\d+ ([\d,]+\.\d{2})", line)]
        stated = float(re.search(r"= \*\*MXN ([\d,]+\.\d{2})\*\*", line).group(1).replace(",", ""))
        assert abs(sum(terms) - stated) <= 0.01
        assert abs(stated - finding["peso_amount"]) <= 0.01
        assert line.endswith("= claimed.")


# --- leads not pursued --------------------------------------------------------
def test_every_declined_lead_prints_signal_reason_tools_and_closer(rendered):
    body = rendered["md"].split("## Leads not pursued")[1].split("## Method and limits")[0]
    leads = rendered["submission"]["leads_not_pursued"]
    assert leads
    assert body.count("- **Signal:**") == len(leads)
    assert body.count("- **Closed by:**") == len(leads)
    for lead in leads:
        assert lead["entity"] in body
        assert lead["reason"] in body
        assert lead["signal"] in body


def test_declined_leads_are_in_the_body_not_an_appendix(rendered):
    """The judges' spec is explicit: this section comes before Method and limits."""
    md = rendered["md"]
    assert md.index("## Leads not pursued") < md.index("## Method and limits")


# --- method and limits --------------------------------------------------------
def test_method_states_architecture_scope_limits_and_how_to_reproduce(rendered):
    section = rendered["md"].split("## Method and limits")[1]
    assert "**Architecture**" in section
    assert "**Out of scope for this run**" in section
    assert "**What this system cannot detect**" in section
    assert "**Reproducibility**" in section
    assert "python -m agent.investigate" in section
    assert "collusion that never moves money through the books" in section


# --- HTML ---------------------------------------------------------------------
def test_html_is_self_contained_and_opens_with_the_network_off(rendered):
    html = rendered["html"]
    assert html.startswith("<!DOCTYPE html>")
    assert html.count("<svg") == len(rendered["submission"]["findings"])
    assert "<script" not in html
    assert "http" not in html, "a URL of any kind would break the offline requirement"
    assert len(html.encode("utf-8")) < 2_000_000
    assert [line for line in html.splitlines() if line.startswith("<h2>")] == [
        f"<h2>{s[3:]}</h2>" for s in SECTIONS
    ]


def test_html_escapes_names_that_contain_markup(ds):
    case = {
        "findings": [],
        "not_pursued": [{"entity": "S00005", "reason": "a <script>alert(1)</script> reason"}],
    }
    html = render_html(case, ds, submission={"seed": 0, "findings": [], "leads_not_pursued": [
        {"entity": "S00005", "signal": "detect_no_receipt", "reason": "a <script>alert(1)</script> reason",
         "tool_calls_made": [], "closed_by": "investigator"}], "run_metadata": {
        "llm_calls": 0, "mxn_cost": 0.0, "wall_clock_seconds": 0.0}})
    assert "<script" not in html
    assert "&lt;script&gt;" in html


def test_rendering_makes_no_network_call(rendered, monkeypatch):
    """Judges may ask for the case file with connectivity disabled; prove it needs none."""
    import socket

    def refuse(*args, **kwargs):
        raise AssertionError("the report tried to open a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    markdown = render(rendered["case"], rendered["ds"], submission=rendered["submission"])
    html = render_html(rendered["case"], rendered["ds"], submission=rendered["submission"])
    assert _sections(markdown) == SECTIONS
    assert "<svg" in html


def test_a_report_can_be_rendered_without_a_submission(rendered):
    """The submission is rebuilt from the case file, so one artifact is never stale."""
    markdown = render(rendered["case"], rendered["ds"])
    assert _sections(markdown) == SECTIONS
    assert "```mermaid" in markdown


# --- exposure and money_trail (kept from #23) ---------------------------------
def test_exposure_efos(ds, example_case):
    expo = exposure(_finding(example_case, "efos_fake_supplier"), ds)
    assert abs(expo["isr_deduction_at_risk"] - 535500.00) <= 0.01
    assert abs(expo["iva_credit_at_risk"] - 285600.00) <= 0.01


def test_exposure_kickback(ds, example_case):
    expo = exposure(_finding(example_case, "kickback_shell"), ds)
    assert expo["paid_to_employee"] > 0
    assert expo["isr_deduction_at_risk"] > 0


def test_exposure_round_trip(ds, example_case):
    expo = exposure(_finding(example_case, "round_trip_sales"), ds)
    assert expo["revenue_overstated"] > 0


def test_exposure_duplicate(ds, example_case):
    expo = exposure(_finding(example_case, "duplicate_invoice_payment"), ds)
    assert expo["cash_loss"] > 0


def test_money_trail_round_trip(ds, example_case):
    trail = money_trail(_finding(example_case, "round_trip_sales"), ds)
    assert trail
    dates = [row["fecha"] for row in trail]
    assert dates == sorted(dates)


# --- CLI ----------------------------------------------------------------------
def _run_cli(args):
    return subprocess.run([sys.executable, "-m", "agent.report", *args], cwd=ROOT, capture_output=True, text=True)


def test_cli_writes_markdown_and_html(tmp_path):
    out, html = tmp_path / "c42.md", tmp_path / "c42.html"
    res = _run_cli([str(COMPANY_42), str(EXAMPLE_FILE), "--out", str(out), "--html", str(html)])
    assert res.returncode == 0, res.stderr
    assert _sections(out.read_text(encoding="utf-8")) == SECTIONS
    assert "<svg" in html.read_text(encoding="utf-8")


def test_cli_rejects_invalid_evidence(example_case, tmp_path):
    import copy

    case = copy.deepcopy(example_case)
    case["findings"][0]["evidence"].append("TX99999")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(case), encoding="utf-8")
    out = tmp_path / "bad.md"
    res = _run_cli([str(COMPANY_42), str(bad), "--out", str(out)])
    assert res.returncode == 1
    assert "TX99999" in res.stderr
    assert not out.exists()
