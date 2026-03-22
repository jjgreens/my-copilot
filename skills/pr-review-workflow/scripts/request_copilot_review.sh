#!/usr/bin/env bash
# request_copilot_review.sh <owner/repo> <pr>
#
# Requests a Copilot review on a PR — but only if one is not already pending
# or in progress for the current HEAD commit. Repos with automatic review
# settings will have already queued a review on push; re-requesting is a no-op
# at best and creates duplicate review noise at worst.
#
# Exit codes:
#   0 — completed (review requested, or already pending/in-progress for HEAD)
#   1 — error (missing arguments, missing required tool, or API failure)

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: 'gh' CLI is required but not found. Install it from https://cli.github.com/" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: 'jq' is required but not found. Install it via your package manager (e.g. apt install jq, brew install jq)." >&2
  exit 1
fi

REPO="${1:-}"
PR="${2:-}"

if [[ -z "$REPO" || -z "$PR" ]]; then
  echo "Usage: $0 <owner/repo> <pr>" >&2
  exit 1
fi

# Get the current HEAD SHA for this PR
HEAD_SHA=$(gh pr view "$PR" --repo "$REPO" --json headRefOid -q .headRefOid)

# Check if any Copilot review check run is currently queued or in progress
# Use --paginate to handle repos with many check runs exceeding the default page size
COPILOT_ACTIVE=$(gh api "repos/${REPO}/commits/${HEAD_SHA}/check-runs?per_page=100" \
  --paginate \
  --jq '[.check_runs[] | select(.name | test("Copilot"; "i")) | select(.status == "queued" or .status == "in_progress")] | length' \
  | jq -s 'add // 0')

if [[ "$COPILOT_ACTIVE" -gt 0 ]]; then
  echo "ℹ️  Copilot review already in progress for ${HEAD_SHA:0:7} — skipping request."
  exit 0
fi

echo "Requesting Copilot review for PR #${PR} (HEAD: ${HEAD_SHA:0:7})..."
gh api "repos/${REPO}/pulls/${PR}/requested_reviewers" \
  -X POST \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]" \
  --silent

echo "✅ Copilot review requested."
