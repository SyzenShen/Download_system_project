# Storage Capacity Stress Test

This experiment estimates how the system behaves when thousands of large files are ingested, and helps infer the practical storage ceiling under current infrastructure limits.

## Prerequisites

1. Backend and frontend services running locally (default: `http://localhost:8000` + `5173`).
2. A Django superuser or API token with upload permissions.
3. Python environment with the following packages:
   ```bash
   pip install requests
   ```
4. Optional (for JSON parsing/plotting): `pandas`, `matplotlib`.

## Folder Contents

| File | Purpose |
| --- | --- |
| `config.example.json` | Scenario template describing staged loads, file sizes, and concurrency hints. Copy to `config.json` (gitignored) and customise. |
| `run_storage_stress.py` | Main runner that creates synthetic files, uploads them via REST API, records performance metrics, and optionally cleans up generated data. |
| `REPORT.md` | Markdown report capturing methodology, metrics to record, and placeholders for real results. Fill this after each test campaign. |

All generated artefacts (temporary files, JSON logs, markdown summaries) are written to the same directory unless overridden with CLI flags.

## Usage

1. Create a config file:
   ```bash
   cd tests/storage_capacity_stress
   cp config.example.json config.json
   ```
   Update parameters such as stage sizes or per-stage file counts. Keep secrets out of the file—provide authentication via environment variables.

2. Export authentication token (or set `--token` later):
   ```bash
   export BIOFILE_TOKEN=<your-drf-token>
   ```

3. Run the stress script:
   ```bash
   python run_storage_stress.py \
       --config config.json \
       --base-url http://localhost:8000 \
       --token "$BIOFILE_TOKEN" \
       --output-dir results \
       --cleanup-after
   ```

   Key flags:

   | Flag | Description |
   | --- | --- |
   | `--config` | Path to JSON scenario file. |
   | `--base-url` | Root URL of Django service. |
   | `--token` | DRF token (if not supplied, script will read `BIOFILE_TOKEN`). |
   | `--output-dir` | Where to place JSON summaries and optional Markdown digest. |
   | `--max-total-bytes` | Hard-stop guard to avoid exhausting local disk. |
   | `--cleanup-after` | Delete uploaded test files once metrics are gathered. |
   | `--dry-run` | Print planned actions without uploading data. |

4. After execution, review:
   * JSON summary under `results/`.
   * Update `REPORT.md` with observed numbers, trends, and any anomalies.
   * Attach relevant logs if storage limits were hit (e.g., 507 Insufficient Storage).

## Reproducibility Guidelines

* Always record:
  - Git commit hash (backend + frontend).
  - Database state (clean, seeded, production snapshot).
  - Available disk capacity before/after test (`df -h`).
  - Token scope / user role.
* Use the same config file for baseline vs regression runs; commit configs or archive them with summaries.
* If multiple runners participate, sync clocks (`ntp`) to keep timestamps comparable.

## Extending the Test

* Add new stages in the config to mimic tiered storage (e.g., 1 GB × 1,000, then 5 GB × 200).
* Enable `results_to_markdown` flag to emit auto-generated table fragments for inclusion in `REPORT.md`.
* Hook `results.json` into notebooks (`notebooks/storage_stress.ipynb`) for visualisation.

This folder contains no secrets or large binaries; all large files are generated on-the-fly and deleted when `--cleanup-after` is used.
