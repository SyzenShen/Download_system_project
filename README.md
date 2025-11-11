# BioFileManager

BioFileManager is a lightweight Django + Vue 3 platform that modernizes how research groups manage sequencing data and derived analytical artifacts. It replaces brittle FTP/NAS shares with structured metadata, granular permissions, resumable transfers, and a bridge to Cellxgene so laboratories can publish `.h5ad` files directly from the same workspace. The system is currently deployed at Capital Medical University.

The stack combines a Vue 3 single-page application (built with Vite) and a Django REST backend. Uploaded files are indexed with 22 domain-specific metadata fields (organism, assay type, data type, etc.) and lightweight format-aware parsers enrich FASTA/FASTQ/VCF/BAM files with counts, GC content, BAM headers, and more. A reserved Intelligent Analytics Interface (`ml_interface`) lets future AI/ML modules plug in for auto-tagging, QC, summarization, embedding generation, and `.h5ad` preprocessing without touching the front end.

## Key Capabilities

| Capability | Description |
| --- | --- |
| Metadata indexing | 22 biological & technical fields plus parsers for FASTA/FASTQ/VCF/BAM that capture sequence counts, GC content, BAM headers, etc. |
| Faceted search | Millisecond filters by organism × assay × tags × permission level. |
| Access control & audit | Public/Internal/Restricted policies cascade to users, groups, projects, and folders; every operation is logged. |
| Reliable transfer | Chunked uploads, resumable downloads, pause/resume, retries, and cleanup of aborted fragments. |
| Cellxgene integration | One-click publish for `.h5ad`, automatic embedding generation, backend restart, UI masking, and inline visualization. |
| Dual interface | Vue 3 SPA + REST API for both manual workflows and scripted automation. |
| NCBI bridge | Detects Gene/Protein/SRA/PubMed/BioProject/BioSample links, downloads sources, and pre-populates metadata. |

## Architecture Overview

```
Vue 3 SPA  ⇄  Django REST  ⇄  Metadata DB & File Store  ⇄  Cellxgene Viewer
           ↕                                 ↕
     Browser Clients                    media/, cellxgene_data/
```

The frontend ships with Vite; the backend relies on Django + DRF. Cellxgene is orchestrated by Django but runs in its own virtual environment (`.venv-cellxgene`) on a configurable port.

## Requirements

| Component | Minimum |
| --- | --- |
| Python | 3.10 |
| Node | 18.x |
| npm | 9.x |
| PostgreSQL / SQLite | Latest LTS |
| Redis (optional) | 6.x |
| OS | macOS or Linux with `bash`, `curl`, `lsof` |

Cellxgene runs inside `.venv-cellxgene` to keep dependencies isolated from the primary Django environment.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm --prefix frontend install
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver
npm --prefix frontend run dev
```

Open `http://localhost:5173` in the browser. Use `scripts/start_services.sh` / `scripts/stop_services.sh` if you prefer a single command to manage both processes.

## Cellxgene Workflow

1. Upload or select an `.h5ad` file.
2. Click **Send to Cellxgene**.
3. The backend copies the file into `cellxgene_data/<id>__filename.h5ad`, generates missing embeddings with TruncatedSVD, kills stale processes, and starts a fresh Cellxgene instance.
4. The frontend displays a mask and polls `/cellxgene/api/v0.2/config`. When the dataset name matches the requested file the mask disappears and the UI routes to `/cellxgene-app?file=<filename>`.
5. The navbar keeps the most recent publication handy; if no file was published the link opens the default Cellxgene welcome page.

Configuration overrides (env vars or `file_project/settings.py`):

| Setting | Default | Description |
| --- | --- | --- |
| `CELLXGENE_DATA_DIR` | `<BASE_DIR>/cellxgene_data` | Storage location |
| `CELLXGENE_PORT` | `5005` | Listening port |
| `CELLXGENE_CMD` | `.venv-cellxgene/bin/cellxgene` | Executable path |
| `CELLXGENE_LOG_FILE` | `logs/cellxgene.log` | Log destination |
| `CELLXGENE_AUTO_RESTART` | `True` | Restart viewer on publish |

## NCBI Data Bridge

* The file workspace exposes an **NCBI Download** dialog that imports resources into the active folder.
* Supported patterns include Gene, Protein, SRA (FASTQ, up to 1 GiB by default), PubMed (abstract text), BioProject, and BioSample.
* The backend calls E-utilities (`efetch`, `esummary`) to fetch both payload and metadata and stores the result as a regular file entry with `upload_method="NCBI Import"`.

API summary:

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/files/ncbi/import/` | Payload `{ "url": "<NCBI link>", "parent_folder": optional }`; response includes `file` and `metadata`. |
| `GET` | `/api/files/ncbi/import/<accession>/status/` | Check a previously triggered download. |

## Intelligent Analytics Interface

`ml_interface` reserves a single gateway for downstream ML automations:

| Task Type | Purpose |
| --- | --- |
| `autotag` | Auto-complete or fix organism/assay/document metadata. |
| `qc` | Lightweight QC on FASTQ/BAM/VCF with automatic flagging. |
| `summary` | Produce concise summaries for experiment logs or results. |
| `embedding` | Generate embeddings for search-by-similarity. |
| `h5ad_vis` | Pre-compute UMAP/TSNE suggestions prior to Cellxgene publication. |

### API Snapshot

```http
POST /api/ml/trigger/
{
  "task_type": "autotag",
  "file_id": 123
}
→ { "task_id": 45, "status": "queued" }
```

* Authentication follows the global token/session model.
* Standard users can only access their own tasks; admins see everything.
* Tasks are persisted in `ml_interface.MLTask` with type, status (`pending|queued|running|done|failed`), result JSON, submitter, and timestamps.
* `ml_interface.utils` exposes no-op handlers such as `handle_autotag` and `handle_qc`; swap in Celery workers or external inference services without frontend changes.

## Performance Evaluation

**Testbed**

| Component | Spec |
| --- | --- |
| CPU | 2 × Intel Xeon Gold 6430 (32 cores total, 2.1 GHz) |
| RAM | 256 GB DDR5 |
| Storage | 4 × 3.84 TB NVMe SSD (RAID10, 5.5 GB/s sustained) |
| Network | 10 Gbps fiber |
| OS | Ubuntu Server 22.04.4 LTS |

**Scope**: single file transfers (10 MB → 100 GB), concurrency (1/10/50/100 clients), resumable transfer resilience (30% packet loss), baseline comparison (SCP/rsync/native HTTP), security and compliance review, and production-scale simulation (15,000 users / 50 TB data).

**Key Findings**

| Metric | Result |
| --- | --- |
| Upload throughput | 95–125 MB/s |
| Download throughput | 110–155 MB/s |
| Concurrency success | > 99% @ 100 clients |
| Average response @ 100 clients | 540–580 ms |
| Resume recovery | < 3 s |
| File integrity | 100% |
| Availability | 99.9% |

Full scripts and datasets live in `performance_test_project/`.

## Security Controls

| Dimension | Mechanism |
| --- | --- |
| Data encryption | AES-256 at rest for sensitive fields, mandatory HTTPS/TLS, signed resumable URLs. |
| Access audit | Auth, file CRUD, and ACL changes land in append-only logs ready for ELK/Prometheus ingestion. |
| Retention & deletion | Project-level retention windows, soft-delete + purge workflow, multi-pass wipe for compliance. |
| Compliance checks | Built-in GDPR/HIPAA prompts, DSAR exports, download audit trails, and sensitive-field redaction hints. |

## Project Layout

```
Download_system_project/
├── authentication/                # Auth flows
├── file_project/                  # Django settings
├── file_upload/, file_download/   # File CRUD logic
├── ml_interface/                  # Intelligent analytics placeholders
├── frontend/                      # Vue 3 SPA
├── tests/storage_capacity_stress/ # Storage ceiling stress harness
├── cellxgene/                     # Cellxgene source & build
├── cellxgene_data/                # Published .h5ad artifacts
├── logs/                          # Runtime logs
├── .pids/                         # Background process IDs
├── performance_test_project/      # Performance suite
├── scripts/                       # Start/stop helpers
└── README.md
```

## Troubleshooting

| Issue | Cause | Resolution |
| --- | --- | --- |
| Cellxgene shows “Not Found” | No `.h5ad` published or port conflict | Publish a file and ensure nothing else binds `CELLXGENE_PORT`. |
| Mask never clears | Corrupted data or embedding failure | Inspect `logs/cellxgene.log`, verify `.h5ad` integrity. |
| Upload interrupted | Network blips or limit exceeded | Use pause/resume; inspect server upload limits. |
| Empty download | User canceled or network drop | Retry; the system cleans incomplete artifacts. |
| npm dependency conflict | Node version mismatch | Remove `frontend/node_modules` and reinstall. |
| numpy conflict | Colliding with Cellxgene requirements | Keep `.venv` and `.venv-cellxgene` isolated. |

---

Released under the MIT License — contributions and discussions are welcome.
