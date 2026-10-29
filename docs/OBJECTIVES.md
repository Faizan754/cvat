# Objectives

Machine: AMD Ryzen 5 5500U (12 threads), 4.8 GiB RAM visible to WSL2, Ubuntu 26.04.1 on WSL2,
Docker 29.9.2 / Compose v5.6.1, CVAT base commit `30d86df3cd413dba39fcbf39eead67b72e8c016a`.

| ID | Field | Entry |
|----|-------|-------|
| MO-1 | What is measured | Total time of an authenticated `GET` on the per-label counts endpoint for the imported COCO task, as seen by the client. |
| | How | From the host, `curl -s -o /dev/null -w '%{time_total}\n'` against `http://localhost:8080/api/...?task_id=N` (through Traefik), with a valid session or token. One warm-up request is sent and discarded, then 5 timed requests in a row. The median and the min-max spread are taken from the 5 values. |
| | Target | Median of 5 runs at or below **150 ms**, on the task holding all annotations of the imported subset (about 500 images). |
| | Conditions | Local Docker stack from `docker-compose.yml` + `docker-compose.dev.yml`, warm server and database, no import, export or build running, no browser open on the task. Image and annotation counts of the task are recorded with the results. |
| | Not included | Cold start (first request after a container restart), page render time, the WebSocket path, video tasks, and the per-type grouping if it adds a parameter (measured separately only if time allows). |

## Why this number

150 ms is roughly where a page update still feels immediate when the chart is fetched on load and
again after each live update. The work is three `GROUP BY label_id` queries on foreign-key columns
that already have indexes, returning one row per label (80 for COCO), so on ~500 images it should
fit well inside that. CVAT's own annotations endpoint for the same task serialises every shape and
is much slower; the counts endpoint exists to avoid that, so it has to be clearly faster. The
honest risk: the queries filter through job -> segment -> task, and there is no index on
`job.type`, which I need for the job selection rule. If the target is missed I will look at the
query plan (`EXPLAIN ANALYZE`) before changing anything, and report the miss as it is.

**Update (2026-10-30 01:27): the endpoint path is `GET /api/annotation_counts?task_id=N`. Correction: the sentence above saying CVAT's own annotations endpoint "is much slower" is an expectation, not a measurement. It has not been measured.**

**Update (2026-10-30 02:10): the measurement task is task 1: 500 images, 4012 shapes, 5 annotation jobs. Results are still pending.**

## Results

_pending — raw output of 5 runs, median, spread (min–max), commit SHA will be pasted here_
