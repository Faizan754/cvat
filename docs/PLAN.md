# Plan: Annotation Analytics

Goal: add an endpoint that counts annotations per label for a CVAT task in the database, and a
task page that draws those counts as a bar chart. Then add speed, access control and live updates
in the brief's order, as far as 8 hours allows.

## Environment

- CVAT base commit: `30d86df3cd413dba39fcbf39eead67b72e8c016a`, branch `dev-test01`
- CPU: AMD Ryzen 5 5500U, 12 threads
- RAM: 4.8 GiB visible to WSL2
- OS: Ubuntu 26.04.1 on WSL2; Docker 29.9.2, Compose v5.6.1
- Data: COCO val2017. Image count: to be recorded after import. I plan a subset of about 500
  images, because the full 5000 will not fit comfortably in 4.8 GiB.

## Steps (time budget out of 8 h)

| # | Step | Brief item | Budget |
|---|------|-----------|--------|
| 1 | Read the brief and the relevant CVAT code, start build and COCO import | setup | 0.75 h |
| 2 | Write and commit these three docs, before any code | rules | 0.5 h |
| 3 | `cvat/apps/test` app, endpoint, count query, check counts against the DB | 1 | 1.0 h |
| 4 | Task page, bar chart, loading / empty / error-with-retry states | 2, 3, 4 | 1.5 h |
| | **Gate: items 1-4 working end to end before anything below. This is the floor.** | | |
| 5 | Permission class; show 401, 403 and 404 with raw curl output | 5 | 0.5 h |
| 6 | Measure MO-1 five times, record the result in OBJECTIVES.md | 6 | 0.75 h |
| 7 | One grouping beyond the plain count (see below) | 7 | 0.5 h |
| 8 | Live chart updates over WebSocket | 8 | 1.5 h |
| 9 | Reconnect with backoff, re-fetch on reconnect, show connection state | 9 | 0.5 h |
| 10 | Decision record, tick the DoD with evidence, list what is unfinished | 10 | 0.5 h |
| | **Total** | | **8.0 h** |

If I run short, I stop at the last working item and list the rest in the DoD with the reason.

## Design decisions

- Backend lives in a new Django app `cvat/apps/test` with no models, wired in with one line each
  in `settings/base.py` and `urls.py`.
- Endpoint: a DRF `ViewSet` with a `list` action, `GET /api/<resource>?task_id=N`. A ViewSet,
  not an `APIView`, because CVAT's `PolicyEnforcer` expects every view to have an IAM class.
- Permission: a small subclass that loads the task (404 if missing, 400 if `task_id` is not an
  int) and reuses `TaskPermission`'s view scope. No new `.rego` file. Expected: 401 anonymous,
  403 no access to the task.
- Counting: one `GROUP BY label_id` query each on `LabeledShape`, `LabeledTrack` and
  `LabeledImage`, merged in Python by label. Annotations are never loaded into Python.
- Which jobs count: annotation jobs; ground-truth jobs only when the task's validation mode is
  GT pool; consensus replica jobs never. This follows CVAT's own rule in
  `dataset_manager/task.py`.
- Skeletons: only top-level objects count (`parent IS NULL`), not their points.
- Tracks: one track counts as one object, not one per keyframe.
- Labels come from `task.get_labels()`, so project tasks work, and labels with no annotations
  are returned with 0.
- UI: route `/tasks/:tid/<feature>` beside the existing analytics route, linked from the task
  actions menu. Requests go through `core.server.request` (session, CSRF, org headers already
  handled). Chart with `react-chartjs-2`, which is already a dependency. No new packages.

## Item 7 candidate

Per-label breakdown by annotation type (shape / track / tag). It costs nothing extra: the three
GROUP BY queries already produce it, I only stop summing them. It tells a reviewer whether a class
is labelled with boxes on single frames or with tracks. Alternative considered: filtering by job.
I will confirm the choice when I reach item 7.

## WebSocket approach (tentative)

Annotation saves use `bulk_create`, so no per-shape signal fires, but every save calls
`task.touch()`, which fires `post_save(Task)`. I plan to listen for that in `cvat/apps/test`,
publish through Redis pub/sub after `transaction.on_commit` (there are several server processes,
so an in-process broadcast will not reach every socket), and serve the socket under `/api/` so
Traefik needs no change. The socket checks the same task view permission before accepting.
Django Channels versus a small hand-written ASGI router is undecided; the decision record will
say which and why.

## Skipped up front

- Video-specific handling (per-frame counts for tracks, interpolated shapes)
- Per-frame time series and historical trends
- A caching layer, unless MO-1 is missed and the cause is the query
- Cypress end-to-end tests
- i18n of the new page

## Known deviations from the brief

- The PR targets `develop` on my fork, because the fork has no `main` branch.
- The machine has 4.8 GiB RAM for WSL2, not the suggested 8 GB, hence the COCO subset.

## Changes to this plan

Entries are added with date and reason when the plan changes.

**Update (2026-10-30 01:27): about 2 hours of the 8 h window remain when this plan is committed, so I am revising the budget.**

Revised steps (about 2 h):

| Step | What | Brief items | Budget |
|------|------|-------------|--------|
| 1 | Commit these three docs | — | 5 min |
| 2 | `cvat/apps/test`: endpoint `GET /api/annotation_counts?task_id=N`, count query, permission class (built in parallel with step 3) | 1, 5 | 35 min |
| 3 | Task page, bar chart, loading / empty / error-with-retry states | 2, 3, 4 | 35 min (parallel with step 2) |
| 4 | Build images; check counts against psql and the COCO json; 401/403/404 with curl | 1, 5 | 20 min |
| 5 | Measure MO-1 five times | 6 | 15 min |
| 6 | Short decision record, tick the DoD with evidence, list what is unfinished | 10 | 10 min |

Now skipped, with reason:

- Item 8 (WebSocket live updates) and item 9 (reconnect): not enough time. They need a new ASGI route and Redis pub/sub, and I would rather not ship them half-done.
- Item 7 (per-type grouping) is a stretch. The endpoint already returns shapes / tracks / tags per label, so only the UI part would be left.
- Unit tests and regenerating `cvat/schema.yml` are skipped. Evidence comes from curl and psql instead.

The endpoint path is now fixed as `/api/annotation_counts`.

**Update (2026-10-30 02:10): dataset changed. The plan said "about 500 images from the full zip". The full `val2017.zip` download stalled at about 14 KB/s, so I used the COCO annotations file plus individually downloaded images instead.**

- Subset: the first 500 images by ascending id that have at least one annotation (ids 139 to 57232).
- These hold 3591 COCO annotations (39 of them `iscrowd`) and 78 of the 80 categories.
- CVAT task id 1, "COCO val2017 subset 500": 500 frames, segment size 100, so 5 annotation jobs (ids 1-5). Labels are type "any".
- Upload and processing took 15.4 s; the COCO 1.0 annotation import took 15.0 s.

**Update (2026-10-30 02:10): definition of "annotation" for the counts. One annotation is one shape, track or tag as CVAT stores it, not one COCO object.**

- The endpoint returns 4012 for task 1. The COCO json has 3591 objects for the same 500 images. The difference is +421.
- Cause: 298 non-crowd COCO objects have a segmentation made of several polygons. CVAT's COCO import stores each polygon part as a separate `LabeledShape` and links the parts with `group`. Task 1 has 719 grouped polygons = 298 objects + 421 extra parts.
- Check: predicting the shape count from the COCO json (number of polygon parts per object, 1 per crowd mask) gives the API count for all 80 labels, with zero mismatches.
- In the DB: 3973 polygons + 39 masks = 4012, and psql gives the same per-label numbers as the API.
- Why I chose this: it is the simpler query, and it matches what CVAT stores and shows in the job. Counting COCO objects would need a count of distinct groups instead of rows.
- What it costs: the number differs from COCO's object count. Anyone comparing the chart with COCO has to know that multi-part objects count once per part.

**Update (2026-10-30 02:24): where I stopped. Items 1-6 are done. Items 7, 8 and 9 were not reached (time). Item 10 is the decision record below.**

Actual commit order (`git log --oneline 30d86df3c..HEAD`, oldest at the bottom):

```
b3c41aa51 Link annotation counts page from the task actions menu
6fcf648ad Add annotation counts page with bar chart, empty and error states
e58a3c73f docs: record MO-1 measurement (median 126.9 ms, target met) and empty-task check
e5df67ba7 docs: record 500-image dataset, shape-count definition and endpoint evidence
bcd9bac09 Expose annotation counts at GET /api/annotation_counts behind task view permission
4e4ff966e Add per-label annotation count query for a task
8e7020117 docs: add plan, definition of done and objectives before any code
```

## Decision record

(written when item 10 is reached)

**Update (2026-10-30 02:24): decision record.**

- **Taken:** count in SQL. One `GROUP BY label_id` per annotation table (shapes, tracks, tags) in `cvat/apps/test/counts.py:28-39`, filtered to the task's jobs with CVAT's job-type rule, merged by label in Python. Access uses a small permission class that reuses `TaskPermission`'s view scope, so no new OPA rule. Measured: median 126.9 ms (OBJECTIVES.md); the shapes query itself executes in ~6 ms (`EXPLAIN ANALYZE`).
- **Rejected:** reuse CVAT's own loader, `TaskAnnotation` in `cvat/apps/dataset_manager/task.py:1025` (what the export uses), and count in Python. Why: it loads every shape with its points into memory, which is the wrong cost on a 4.8 GiB machine and against a 150 ms target, and it is far more code to trace and explain.
- **What rejecting it cost:** `TaskAnnotation.init_from_db` (task.py:1185-1203) merges job after job through `_merge_data` (task.py:1077-1079) into `AnnotationManager.merge(..., overlap=task.overlap)` (`cvat/apps/dataset_manager/annotation.py:233-246`). On the overlapping frames it matches objects from neighbouring jobs (Hungarian matching, annotation.py:424-509) and unites them. My counts skip that, so in a task with overlap > 0 (typical for video) an object on the overlapping frames is counted once per job. Task 1 has overlap = 0 (segment size 100, 500 frames), so it is not affected here.
- I also count stored shapes, not merged objects: a multi-part COCO object counts once per part (+421 on task 1, see "Changes to this plan").

Second, smaller decision:

- **Taken:** a new endpoint in app `test`, `GET /api/annotation_counts?task_id=N`.
- **Rejected:** a nested action `/api/tasks/{id}/...` on the engine's `TaskViewSet`.
- **Why:** the brief requires the backend work in app `test`, and this leaves the engine's `TaskViewSet` untouched.
- **Cost:** the URL is less RESTful, and the permission class has to parse `task_id` and load the task itself (`cvat/apps/test/permissions.py:20-27`).
