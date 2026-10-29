# Definition of Done

Written before any code. Each line is ticked only with evidence beside it: a number, a commit
SHA, a file:line reference or pasted output. A tick without evidence counts as unticked.

## Floor (items 1-4)

- [ ] The endpoint returns per-label counts for the imported COCO task that match an independent
      count: a `psql` `COUNT(*) ... GROUP BY label_id` over the task's annotation jobs, and the
      per-category totals from the COCO json for the imported subset. — evidence: _pending_
  **Update (2026-10-30 02:10): partly met, not ticked. psql matches exactly: total 4012 = 4012, 0 per-label mismatches (Evidence section below). The COCO json does not match literally (3591 objects), because CVAT stores each part of a multi-part polygon as its own shape. The +421 is explained and reproduced per label with 0 mismatches — see Plan, "Changes to this plan".**
- [x] Labels with no annotations come back with count 0. — evidence: task 1, `toaster` and `hair drier` return total 0 (2 of 80 labels).
- [x] The count is computed in SQL (GROUP BY), not by loading annotations into Python; file:line
      of the query recorded. — evidence: `cvat/apps/test/counts.py:31-32` (`.values("label_id").annotate(count=Count("id"))`, query built at lines 29-35).
- [x] A missing task returns 404 and a non-integer `task_id` returns 400 (raw curl output).
      — evidence: see Evidence section below.
- [ ] The task page opens from the task actions menu and renders a bar chart of the counts.
      — evidence: _pending_
- [ ] A task with no annotations shows an empty state, not an empty chart. — evidence: _pending_
- [ ] A failed request shows an error state with a retry button, and retry recovers.
      — evidence: _pending_

## Items 5-10

- [x] No login returns 401 (raw curl output). — evidence: see Evidence section below.
- [x] A logged-in user without access to the task gets 403 (raw curl output). — evidence: see Evidence section below.
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

## Evidence

**Update (2026-10-30 02:10): raw output from the live stack, task 1 (status line and body; headers left out). Passwords are masked.**

```
$ curl -i 'http://localhost:8080/api/annotation_counts?task_id=1'
HTTP/1.1 401 Unauthorized
{"detail":"Authentication credentials were not provided."}

$ curl -i -u analytics_admin:*** 'http://localhost:8080/api/annotation_counts'
HTTP/1.1 400 Bad Request
["The 'task_id' query parameter must be an integer"]

$ curl -i -u analytics_admin:*** 'http://localhost:8080/api/annotation_counts?task_id=abc'
HTTP/1.1 400 Bad Request
["The 'task_id' query parameter must be an integer"]

$ curl -i -u analytics_admin:*** 'http://localhost:8080/api/annotation_counts?task_id=999999'
HTTP/1.1 404 Not Found
{"detail":"Task 999999 does not exist"}

$ curl -i -u analytics_viewer:*** 'http://localhost:8080/api/annotation_counts?task_id=1'
HTTP/1.1 403 Forbidden
{"detail":"You do not have permission to perform this action."}

$ curl -i -u analytics_admin:*** 'http://localhost:8080/api/annotation_counts?task_id=1'
HTTP/1.1 200 OK
{"task_id":1,"total":4012,"labels":[{"id":1,"name":"person","color":"#c06060","shapes":1232,"tracks":0,"tags":0,"total":1232},{"id":2,"name":"bicycle","color":"#004040","shapes":45,"tracks":0,"tags":0,"total":45}, ... (truncated)
```

psql cross-check (API per-label totals compared with this query, run directly in the database):

```
api total 4012 db total 4012 mismatches []
```

```sql
WITH j AS (SELECT jj.id FROM engine_job jj JOIN engine_segment s ON s.id=jj.segment_id WHERE s.task_id=1 AND jj.type='annotation'),
c AS (
 SELECT label_id, 'shape' k FROM engine_labeledshape WHERE job_id IN (SELECT id FROM j) AND parent_id IS NULL
 UNION ALL SELECT label_id, 'track' FROM engine_labeledtrack WHERE job_id IN (SELECT id FROM j) AND parent_id IS NULL
 UNION ALL SELECT label_id, 'tag' FROM engine_labeledimage WHERE job_id IN (SELECT id FROM j))
SELECT l.name, count(*) n FROM c JOIN engine_label l ON l.id=c.label_id GROUP BY l.name ORDER BY n DESC, l.name;
```
