#!/usr/bin/env python3
"""
show_ci_annotations.py <owner/repo> <pr>

For CI check runs on the HEAD commit of a PR that have actionable findings
(conclusion other than success, neutral, or skipped; or warning/failure-level
annotations), reports:
  1. The check run output summary (tool-level report, e.g. MegaLinter analysis)
  2. File/line annotations at warning or failure level

Check runs with success, neutral, or skipped conclusions and no annotations
are silently skipped.
These are two distinct GitHub surfaces — both must be checked each round.
The output summary is the canonical per-run report tied to the current HEAD;
it is never stale, unlike PR issue comments which accumulate across runs.

Exit codes:
  0 — completed (findings may or may not be present)
  1 — error (invalid usage, missing `gh` CLI, or GitHub API failure)
"""

import json
import shutil
import subprocess
import sys


def gh(*args):
    if not shutil.which("gh"):
        print("Error: 'gh' CLI is required but not found. Install it from https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    try:
        result = subprocess.run(
            ["gh", "api", "--paginate"] + list(args),
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: gh API call failed:\n{e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    pages = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            pages.append(json.loads(line))
    if len(pages) == 1:
        return pages[0]
    # --paginate emits one JSON object per page; merge arrays
    merged = []
    for page in pages:
        if isinstance(page, list):
            merged.extend(page)
        elif isinstance(page, dict):
            for v in page.values():
                if isinstance(v, list):
                    merged.extend(v)
    return merged


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <owner/repo> <pr>", file=sys.stderr)
        sys.exit(1)

    repo = sys.argv[1]
    pr_num = sys.argv[2]

    # Get HEAD SHA
    pr_data = gh(f"repos/{repo}/pulls/{pr_num}")
    head_sha = pr_data["head"]["sha"]
    short_sha = head_sha[:7]

    # Get all check runs for HEAD
    data = gh(f"repos/{repo}/commits/{head_sha}/check-runs?per_page=100")
    if isinstance(data, dict):
        check_runs = data.get("check_runs", [])
    else:
        check_runs = data

    total_annotations = 0
    total_summaries = 0
    incomplete_runs = 0
    for run in check_runs:
        run_id = run["id"]
        run_name = run["name"]
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion") or status

        if status != "completed":
            incomplete_runs += 1
            continue

        # Use output data already present in the list response (avoids an extra API call per run)
        output = run.get("output", {}) if isinstance(run, dict) else {}
        summary = (output.get("summary") or "").strip()
        ann_count = output.get("annotations_count", 0)
        actionable = conclusion not in ("success", "neutral", "skipped")

        # Always report non-success runs; show summary when present
        if actionable:
            total_summaries += 1
            print(f"\n[{run_name}] ({conclusion}) on {short_sha}:")
            if summary:
                # Truncate very long summaries to keep output readable
                if len(summary) > 2000:
                    print(summary[:2000])
                    print(f"  ... ({len(summary) - 2000} chars truncated — see check run for full output)")
                else:
                    print(summary)
            else:
                print("  (no output summary)")
        elif summary and ann_count > 0:
            # Success/neutral run with annotations — still worth showing the summary
            total_summaries += 1
            print(f"\n[{run_name}] ({conclusion}) — output summary on {short_sha}:")
            if len(summary) > 2000:
                print(summary[:2000])
                print(f"  ... ({len(summary) - 2000} chars truncated — see check run for full output)")
            else:
                print(summary)

        # Fetch annotations only when the check run reports there are some
        if not ann_count:
            continue
        annotations = gh(f"repos/{repo}/check-runs/{run_id}/annotations?per_page=100")
        if not annotations:
            continue

        warnings = [a for a in annotations if a.get("annotation_level") in ("warning", "failure")]
        if not warnings:
            continue

        total_annotations += len(warnings)
        print(f"\n[{run_name}] ({conclusion}) — {len(warnings)} annotation(s) on {short_sha}")
        for ann in warnings:
            path = ann.get("path", "")
            line = ann.get("start_line", "")
            level = ann.get("annotation_level", "")
            msg = ann.get("message", "").replace("\n", " ")
            print(f"  {level.upper():7} {path}:{line}  {msg}")

    if incomplete_runs > 0:
        print(f"⚠️  {incomplete_runs} check run(s) still in progress — re-run after CI completes.")
    if total_summaries == 0 and total_annotations == 0 and incomplete_runs == 0:
        print(f"✅ No actionable CI findings for {short_sha} (all check runs clean).")
    elif total_annotations > 0:
        print(f"\n⚠️  {total_annotations} annotation(s) found — address before merging.")


if __name__ == "__main__":
    main()
