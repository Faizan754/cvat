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

**Update (2026-10-30 02:19): MO-1 measured. Results below.**

- Commit: `e5df67ba7` (HEAD). The backend code is committed, and I checked that the server code deployed in the image (`/opt/cvat`) is identical to the repo.
- Date: Fri Oct 30 02:17-02:18 PKT 2026.
- Machine: as at the top of this file (`nproc` = 12).
- Task: task 1, 500 images, 4012 shapes, 5 annotation jobs.
- Conditions: warm server and database; no build or download running. `free -h` before: Mem 4.8Gi total, 1.7Gi used, 3.1Gi available; swap 3.1Gi used. During the basic-auth series (snapshot 02:17:38) `cvat_clickhouse` was at ~49% CPU and `cvat_grafana` ~10%. At 02:18:07: clickhouse 5.9%, grafana 7.6%, server 0.5%.
- Each series sends a warm-up request (run=0) that is discarded, then 5 timed runs. The basic-auth warm-up took 14.54 s because the server was cold.

Commands (scripts kept in the scratchpad, not committed; password masked, token read from a local file):

```
# basic auth
for i in 0 1 2 3 4 5; do curl -s -o /dev/null -u 'analytics_admin:***' -w "run=$i http=%{http_code} time_total=%{time_total} ttfb=%{time_starttransfer}\n" 'http://localhost:8080/api/annotation_counts?task_id=1'; done

# token auth
KEY=$(cat "$(dirname "$0")/token.key")
for i in 0 1 2 3 4 5; do curl -s -o /dev/null -H "Authorization: Token $KEY" -w "run=$i http=%{http_code} time_total=%{time_total} ttfb=%{time_starttransfer}\n" 'http://localhost:8080/api/annotation_counts?task_id=1'; done
```

Raw output, token auth:

```
run=0 http=200 time_total=0.138100 ttfb=0.135738
run=1 http=200 time_total=0.131363 ttfb=0.129903
run=2 http=200 time_total=0.146297 ttfb=0.145826
run=3 http=200 time_total=0.126941 ttfb=0.126061
run=4 http=200 time_total=0.096979 ttfb=0.094891
run=5 http=200 time_total=0.094256 ttfb=0.093652
```

Raw output, basic auth:

```
run=0 http=200 time_total=14.540263 ttfb=14.537856
run=1 http=200 time_total=0.531135 ttfb=0.529050
run=2 http=200 time_total=0.588198 ttfb=0.587709
run=3 http=200 time_total=0.547548 ttfb=0.545129
run=4 http=200 time_total=0.538453 ttfb=0.537130
run=5 http=200 time_total=0.488317 ttfb=0.487239
```

Arithmetic (runs 1-5, run=0 discarded):

- Token, sorted: 0.094256, 0.096979, 0.126941, 0.131363, 0.146297 → median **126.9 ms**, spread 94.3–146.3 ms. Target ≤ 150 ms: **met**.
- Basic auth, sorted: 0.488317, 0.531135, 0.538453, 0.547548, 0.588198 → median **538.5 ms**, spread 488.3–588.2 ms. This would miss the target.

Verdict: MO-1 is met with token auth (the method says "session or token"). I report basic auth too because it is 4x slower and the reason matters. The ~410 ms gap is consistent with the password hash that basic auth checks on every request. That is the likely cause; I did not profile it separately.

Database share: `EXPLAIN ANALYZE` of the shapes `GROUP BY` query (a hand-written SQL mirror of `cvat/apps/test/counts.py`) gave Planning 5.190 ms, Execution 5.815 ms, using an index scan on `job_id`. I did not run it for the tracks and tags queries. So the database is a small part of the ~127 ms; the Django, permission and HTTP stack takes most of it.

Caveat: ClickHouse was loading the CPU in the background during the basic-auth series, swap was in use, and the worst token run (146.3 ms) is only ~3 ms under the target.
