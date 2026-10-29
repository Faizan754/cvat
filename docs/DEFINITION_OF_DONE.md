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
- [x] The task page opens from the task actions menu and renders a bar chart of the counts.
      — evidence: browser check by me on task 1 (Actions → Annotation counts, total 4012); commits 6fcf648ad, b3c41aa51
- [x] A task with no annotations shows an empty state, not an empty chart. — evidence: browser check on task 2 (3 images, no annotations) shows 'No annotations in this task yet'; API output in Evidence
- [ ] A failed request shows an error state with a retry button, and retry recovers.
      — evidence: _pending_
  **Update (2026-10-30 02:24): not ticked. The error panel with a Retry button was seen for task 999999 (404). Retry recovering after a transient failure was not demonstrated.**

## Items 5-10

- [x] No login returns 401 (raw curl output). — evidence: see Evidence section below.
- [x] A logged-in user without access to the task gets 403 (raw curl output). — evidence: see Evidence section below.
- [x] MO-1 measured: 5 runs, raw output pasted in OBJECTIVES.md, median and spread (min-max),
      commit SHA. — evidence: OBJECTIVES.md Results, commit e5df67ba7, median 126.9 ms (94.3–146.3)
- [x] MO-1 target met, or missed with the reason written down. — evidence: met: 126.9 ms ≤ 150 ms (token); basic auth 538.5 ms reported with reason
- [ ] The filter/grouping works on the endpoint and the page, and the choice is justified in the
      Plan. — evidence: _pending_
- [ ] Live update observed: saving an annotation in a job changes the chart without a page reload.
      — evidence: _pending_
- [ ] Reconnect observed: after restarting `cvat_server` the page shows the dropped state,
      reconnects on its own and re-fetches the counts. — evidence: _pending_
- [x] Decision record written at the end of the Plan. — evidence: PLAN.md, Decision record

## Presentation

- [ ] black, isort (line length 100) and eslint report nothing on the changed files (command
      output). — evidence: _pending_
  **Update (2026-10-30 02:24): not ticked. black and isort are clean on all changed Python files (backend agent run). eslint and tsc were NOT run: there is no node on the host, and the Docker UI build only transpiles with babel (no type check). The page was verified in the browser instead.**
- [x] No dead code, commented-out blocks, debug prints or stray files in the diff
      (`git diff --stat` against the base SHA). — evidence: `git diff --stat 30d86df3c..HEAD`: `16 files changed, 671 insertions(+)` (no deletions; only `cvat/apps/test/`, the UI folder `annotation-counts/`, the route, the menu entry, one line each in `settings/base.py` and `urls.py`, and the three docs)
- [x] Commits are small and their messages say what changed and why; the first commit holds only
      these three docs (`git log --oneline`). — evidence: `git log --oneline 30d86df3c..HEAD`:
      ```
      b3c41aa51 Link annotation counts page from the task actions menu
      6fcf648ad Add annotation counts page with bar chart, empty and error states
      e58a3c73f docs: record MO-1 measurement (median 126.9 ms, target met) and empty-task check
      e5df67ba7 docs: record 500-image dataset, shape-count definition and endpoint evidence
      bcd9bac09 Expose annotation counts at GET /api/annotation_counts behind task view permission
      4e4ff966e Add per-label annotation count query for a task
      8e7020117 docs: add plan, definition of done and objectives before any code
      ```
- [x] Everything not finished is listed below with the reason. — evidence: see Not finished
- [x] The three docs describe only what the repository contains. — evidence: re-read against the code and git log at 2026-10-30 02:24

## Not finished

_To be filled at the end: each item not reached or not working, and why._

**Update (2026-10-30 01:27): with about 2 h left, items 8 and 9 are dropped up front (reason: time). Their lines above stay unticked and will be marked as not reached. Item 7 is a stretch.**

**Update (2026-10-30 02:24): final list of what is not finished, with the reason.**

- Item 7 (per-type grouping): the endpoint already returns `shapes` / `tracks` / `tags` per label, but the UI part was not done (time). Also, the COCO import stores everything as shapes, so on task 1 the split would show 0 tracks and 0 tags.
- Item 8 (WebSocket live updates) and item 9 (reconnect): not reached (time). The planned design is in the Plan, "WebSocket approach (tentative)".
- eslint and tsc were not run: no node on the host. The page was checked in the browser instead.
- Retry recovering after a transient failure was not demonstrated; only the error panel with Retry (task 999999, 404) was seen.
- No unit tests. Evidence is from curl and psql instead.
- `cvat/schema.yml` was not regenerated. drf-spectacular also describes the 200 response as an array, because the action is `list`; the real response is an object.
- A missing `task_id` returns the same "must be an integer" 400 message as a non-integer one (see Evidence).
- The counts do not merge annotations on overlapping segment frames, so a task with overlap > 0 would count those objects once per job. Task 1 has overlap 0. See Plan, Decision record.

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

**Update (2026-10-30 02:19): empty-task check. Task 2 has 3 images, labels person/car/dog and no annotations. Raw response of `GET /api/annotation_counts?task_id=2`:**

```
{"task_id":2,"total":0,"labels":[{"id":81,"name":"person","color":"#c06060","shapes":0,"tracks":0,"tags":0,"total":0},{"id":82,"name":"car","color":"#2080c0","shapes":0,"tracks":0,"tags":0,"total":0},{"id":83,"name":"dog","color":"#406040","shapes":0,"tracks":0,"tags":0,"total":0}]}
```
