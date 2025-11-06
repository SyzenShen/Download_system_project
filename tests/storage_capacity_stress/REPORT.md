# Storage Stress Report

> **Objective:** Estimate the storage saturation point of BioFileManager by progressively uploading synthetic payloads, observe API responsiveness, and capture failure signatures as available capacity diminishes.

## Test Metadata

- **Date:** (fill)
- **Operator:** (fill)
- **Git commit:** `$(git rev-parse HEAD)`
- **Backend URL:** `http://localhost:8000`
- **Client machine:** (CPU, RAM, disk type, OS)
- **Initial free space (`df -h`):** (fill)

## Scenario

| Stage | Files | Size per file | Planned Volume | Notes |
| --- | --- | --- | --- | --- |
| baseline-50mb | 20 | 50 MB | 1.0 GB | warm-up |
| scaleup-200mb | 15 | 200 MB | 3.0 GB | sustained load |
| upper-bound-1024mb | 5 | 1,024 MB | 5.0 GB | probing limit |

> Update the table to reflect the actual `config.json` used during the run.

## Results Snapshot

| Stage | Success | Fail | Avg Latency (s) | Avg Throughput (MB/s) | Additional Notes |
| --- | --- | --- | --- | --- | --- |
| baseline-50mb | (fill) | (fill) | (fill) | (fill) | e.g. “No throttling observed” |
| scaleup-200mb | (fill) | (fill) | (fill) | (fill) | e.g. “CPU steady at 35%” |
| upper-bound-1024mb | (fill) | (fill) | (fill) | (fill) | e.g. “Received 507 after 3 files” |

- **Total uploaded volume:** (from JSON summary)  
- **Total duration:** (seconds)  
- **Average throughput:** (MB/s)  
- **Failures / error codes:** (e.g. 507 Insufficient Storage)  
- **Backend stats after run:** paste excerpt from `/api/files/stats/` response.

## Observations

- **Storage ceiling estimate:** Describe the payload size or cumulative volume at which uploads started failing or throughput degraded sharply.
- **API behaviour:** Were responses consistent (201) until failure? Any timeouts?
- **System metrics:** Summarise CPU, memory, disk I/O stats (collect via `pidstat`, `iostat`, `dstat`, or `docker stats` if applicable).
- **Cleanup:** Confirm whether `--cleanup-after` removed generated files; note residual data if any.

## Recommendations

- (Example) Provision additional storage once utilisation exceeds 80% to avoid 507 errors.
- (Example) Add disk-space monitors and alerting based on `/api/files/stats/total_size`.
- (Example) Consider parallel upload throttling once latency > 10 s for 1 GB payloads.

## Artefacts

- JSON summary: `results/storage_stress_YYYYMMDDTHHMMSSZ.json`
- Markdown digest: `results/storage_stress_YYYYMMDDTHHMMSSZ.md`
- Raw logs: attach relevant `logs/backend.log` or shell transcripts.

> Keep this report version-controlled to track storage limit drifts over time.
