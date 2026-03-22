#!/bin/bash
# Usage: monitor_ci_pr.sh <owner/repo> <pr_number>
# Polls every 30s. Exits once all GitHub Actions workflow runs reach a terminal
# state AND a Copilot review has been submitted for the current PR HEAD commit.

REPO="${1:?Usage: monitor_ci_pr.sh <owner/repo> <pr_number>}"
PR="${2:?Usage: monitor_ci_pr.sh <owner/repo> <pr_number>}"

if ! command -v gh > /dev/null 2>&1; then
  echo "Error: gh CLI not found — install it from https://cli.github.com and authenticate with 'gh auth login'."
  exit 1
fi

echo "Monitoring $REPO PR #$PR — will exit when all checks and Copilot review complete"
echo ""

EMPTY_RUNS_POLLS=0

while true; do
  echo "=== $(date -u +%H:%M:%SZ) ==="

  HEAD_SHA=$(gh api "repos/${REPO}/pulls/${PR}" --jq '.head.sha' 2>/dev/null)
  if [ -z "$HEAD_SHA" ]; then
    echo "Error: could not retrieve HEAD SHA — check repo/PR and gh auth status."
    exit 1
  fi

  if ! RUNS=$(gh api --paginate "repos/${REPO}/actions/runs?head_sha=${HEAD_SHA}&per_page=100" \
    --jq '.workflow_runs | .[] | "\(.name): \(.status) / \(.conclusion // "running")"' 2>/dev/null); then
    echo "Error: could not retrieve workflow runs — check repo permissions and gh auth status."
    exit 1
  fi
  echo "$RUNS"

  # Filter: copilot bot (login starts with "copilot-pull-request-reviewer"),
  # submitted for the current HEAD commit, and submitted_at is not null.
  # --paginate + per_page=100 fetches all pages; tail -1 picks the most recent
  # matching review since the API returns reviews in chronological order.
  REVIEW=$(gh api --paginate "repos/${REPO}/pulls/${PR}/reviews?per_page=100" \
    --jq ".[] | select((.user.login | startswith(\"copilot-pull-request-reviewer\")) and .commit_id == \"${HEAD_SHA}\" and .submitted_at != null) | \"Copilot review: \(.state) (\(.submitted_at))\"" 2>/dev/null | tail -1)
  if [ -n "$REVIEW" ]; then echo "$REVIEW"; else echo "Copilot review: null (null)"; fi

  echo ""

  REVIEW_DONE=$([ -n "$REVIEW" ] && echo 1 || echo 0)

  if [ -z "$RUNS" ]; then
    EMPTY_RUNS_POLLS=$((EMPTY_RUNS_POLLS + 1))
    # Wait up to 3 consecutive empty polls (~90s) before treating as no CI configured.
    if [ "$EMPTY_RUNS_POLLS" -ge 3 ] && [ "$REVIEW_DONE" -gt 0 ]; then
      echo "✅ All checks and Copilot review complete."
      break
    fi
    echo "(no workflow runs found yet — waiting)"
    IN_PROGRESS=1
  else
    EMPTY_RUNS_POLLS=0
    IN_PROGRESS=$(echo "$RUNS" | grep -cE ": (in_progress|queued|waiting) /" || true)
  fi

  if [ "$IN_PROGRESS" -eq 0 ] && [ "$REVIEW_DONE" -gt 0 ]; then
    echo "✅ All checks and Copilot review complete."
    break
  fi

  sleep 30
done
