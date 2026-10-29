# Definition of Done

Written before any code. Each line is ticked only with evidence beside it: a number, a commit
SHA, a file:line reference or pasted output. A tick without evidence counts as unticked.

## Floor (items 1-4)

- [ ] The endpoint returns per-label counts for the imported COCO task that match an independent
      count: a `psql` `COUNT(*) ... GROUP BY label_id` over the task's annotation jobs, and the
      per-category totals from the COCO json for the imported subset. — evidence: _pending_
- [ ] Labels with no annotations come back with count 0. — evidence: _pending_
- [ ] The count is computed in SQL (GROUP BY), not by loading annotations into Python; file:line
      of the query recorded. — evidence: _pending_
- [ ] A missing task returns 404 and a non-integer `task_id` returns 400 (raw curl output).
      — evidence: _pending_
- [ ] The task page opens from the task actions menu and renders a bar chart of the counts.
      — evidence: _pending_
- [ ] A task with no annotations shows an empty state, not an empty chart. — evidence: _pending_
- [ ] A failed request shows an error state with a retry button, and retry recovers.
      — evidence: _pending_

## Items 5-10

- [ ] No login returns 401 (raw curl output). — evidence: _pending_
- [ ] A logged-in user without access to the task gets 403 (raw curl output). — evidence: _pending_
- [ ] MO-1 measured: 5 runs, raw output pasted in OBJECTIVES.md, median and spread (min-max),
      commit SHA. — evidence: _pending_
- [ ] MO-1 target met, or missed with the reason written down. — evidence: _pending_
- [ ] The filter/grouping works on the endpoint and the page, and the choice is justified in the
      Plan. — evidence: _pending_
- [ ] Live update observed: saving an annotation in a job changes the chart without a page reload.
      — evidence: _pending_
- [ ] Reconnect observed: after restarting `cvat_server` the page shows the dropped state,
      reconnects on its own and re-fetches the counts. — evidence: _pending_
- [ ] Decision record written at the end of the Plan. — evidence: _pending_

## Presentation

- [ ] black, isort (line length 100) and eslint report nothing on the changed files (command
      output). — evidence: _pending_
- [ ] No dead code, commented-out blocks, debug prints or stray files in the diff
      (`git diff --stat` against the base SHA). — evidence: _pending_
- [ ] Commits are small and their messages say what changed and why; the first commit holds only
      these three docs (`git log --oneline`). — evidence: _pending_
- [ ] Everything not finished is listed below with the reason. — evidence: _pending_
- [ ] The three docs describe only what the repository contains. — evidence: _pending_

## Not finished

_To be filled at the end: each item not reached or not working, and why._

**Update (2026-10-30 01:27): with about 2 h left, items 8 and 9 are dropped up front (reason: time). Their lines above stay unticked and will be marked as not reached. Item 7 is a stretch.**
