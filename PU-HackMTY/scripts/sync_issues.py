#!/usr/bin/env python3
"""Regenerate docs/ISSUES.md, the offline mirror of the GitHub issue queue. Stdlib only.

  python scripts/sync_issues.py                       # rewrite docs/ISSUES.md
  python scripts/sync_issues.py --check               # exit 1 if docs/ISSUES.md is stale
  python scripts/sync_issues.py --repo o/r --out f.md

Needs an authenticated `gh`. GitHub stays the source of truth: `gh issue view <n>`.
Exit 0 on success, 1 when --check finds drift, 2 when `gh` is missing or fails.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "filip-rs/PU-HackMTY"
DEFAULT_OUT = ROOT / "docs" / "ISSUES.md"

ISSUE_FIELDS = "number,title,state,labels,body,url"
PR_FIELDS = "number,title,state,headRefName,url"


def _gh(args: list[str]) -> list[dict]:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def fetch(repo: str) -> tuple[list[dict], list[dict]]:
    """(issues, prs) as `gh` returns them. Raises on any gh failure; never writes."""
    issues = _gh(["issue", "list", "-R", repo, "--state", "all", "--limit", "200", "--json", ISSUE_FIELDS])
    prs = _gh(["pr", "list", "-R", repo, "--state", "all", "--limit", "200", "--json", PR_FIELDS])
    return issues, prs


def _prs_for(number: int, prs: list[dict]) -> list[dict]:
    hits = [
        pr
        for pr in prs
        if str(pr.get("headRefName", "")).endswith(f"/{number}")
        or str(pr.get("title", "")).startswith(f"#{number} ")
    ]
    return sorted(hits, key=lambda pr: pr["number"])


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def build_markdown(issues: list[dict], prs: list[dict], today: str) -> str:
    issues = sorted(issues, key=lambda i: i["number"])
    lines = [
        f"# Issue queue — snapshot of the GitHub issues (regenerated {today}). "
        "GitHub is the source of truth: `gh issue view <n>`.",
        "",
        "| # | State | Label | Title | PR |",
        "|---|---|---|---|---|",
    ]
    for issue in issues:
        n = issue["number"]
        labels = ", ".join(f"`{lb['name']}`" for lb in issue.get("labels", []))
        pr_cell = ", ".join(f"#{pr['number']} ({str(pr['state']).lower()})" for pr in _prs_for(n, prs))
        lines.append(f"| #{n} | {issue['state']} | {labels} | {_cell(issue['title'])} | {pr_cell} |")
    lines += ["", "---"]
    for issue in issues:
        n = issue["number"]
        labels = " ".join(f"`{lb['name']}`" for lb in issue.get("labels", []))
        heading = f"## #{n} {issue['title'].strip()}  {labels}  {issue['state']}".rstrip()
        body = "\n".join(line.rstrip() for line in str(issue.get("body") or "").strip().splitlines())
        lines += ["", heading, ""]
        if body:
            lines += [body]
    text = "\n".join(lines).rstrip() + "\n"
    # collapse runs of blank lines so sections are separated by exactly one
    out: list[str] = []
    for line in text.splitlines():
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--check", action="store_true", help="exit 1 if the file differs from a fresh build")
    args = parser.parse_args(argv)

    try:
        issues, prs = fetch(args.repo)
    except FileNotFoundError:
        print("gh not found: install GitHub CLI and run `gh auth login`", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or f"gh exited {exc.returncode}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"gh returned invalid JSON: {exc}", file=sys.stderr)
        return 2

    text = build_markdown(issues, prs, today=date.today().isoformat())
    out = Path(args.out)
    if args.check:
        current = out.read_text(encoding="utf-8") if out.exists() else ""
        # the header carries today's date; compare everything after the first line
        if current.split("\n", 1)[1:] != text.split("\n", 1)[1:]:
            print(f"{out}: stale, run python scripts/sync_issues.py", file=sys.stderr)
            return 1
        print(f"{out}: up to date")
        return 0
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}: {len(issues)} issues, {len(prs)} pull requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
