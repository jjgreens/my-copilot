---
description: 'MSR (Monthly Status Report) update workflow — required at end of every work session.'
applyTo: '**'
---

# MSR Update Workflow

At the end of every work session, update the active MSR in OneDrive.

## Location

MSR files are in OneDrive at:
`Documents/msr/<YEAR>/jjgreens/`

Naming convention: `CTO-Team_SSASP_APPL_SPL_James-Greensky_MSR_<MON>_<YEAR>.md`

Example: `CTO-Team_SSASP_APPL_SPL_James-Greensky_MSR_APR_2026.md`

Templates are in:
`Documents/msr/<YEAR>/jjgreens/template/`

## Which MSR to Update

The active MSR is determined by what exists in OneDrive:

1. Compute next month's `<MON>_<YEAR>` (e.g. March 2026 → `APR_2026`; December 2026 → `JAN_2027` in the `2027` folder)
2. Check if that next-month file exists in OneDrive
3. If it exists → update it
4. If it does not exist → update the current month's file

This reflects the practice of opening next month's report partway through the current month.

## What to Update

**Summary and Highlights** — add a one-line bullet per significant deliverable:
```
- [<Category>] <What was built/fixed/shipped>. <Key metric or outcome>.
```

Categories: `Advanced Pathfinding`, `Simics Infrastructure`, `Developer Productivity`, `Collaborations`.

**Relevant detail section** — add or update the subsection for the work area:
- Context: one sentence on why this work exists
- Progress this month: bullet list of what was done
- Next Steps: what remains

**Collaborations, Leadership & Cross-Intel Efforts** — add a brief bullet if the work involves cross-team coordination, tooling, or standards alignment.

## When to Update

- At the end of every session where meaningful progress was made
- Use the session checkpoint as the source of what was accomplished
- Keep entries factual and concise — the MSR audience is technical leadership

## File Format

Follow the existing `.md` format in the MSR file. Do not modify the `.docx` version directly — the `.md` is the editable source.

After editing, upload the updated `.md` back to the same OneDrive folder (overwrite in place using the canonical filename).
