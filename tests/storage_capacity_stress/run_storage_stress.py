#!/usr/bin/env python3
"""
Storage stress harness for BioFileManager.

Generates synthetic files, uploads them via REST API, captures response metrics,
and optionally cleans up the artefacts. Designed to help forecast storage limits.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


DEFAULT_CONFIG = {
    "upload_method": "storage-stress",
    "project": "PerformanceLab",
    "tags": ["performance", "stress-test", "storage"],
    "stages": [
        {"label": "baseline-10mb", "file_size_mb": 10, "file_count": 10, "pause_seconds": 1},
        {"label": "scaleup-100mb", "file_size_mb": 100, "file_count": 10, "pause_seconds": 2},
    ],
    "max_failures": 5,
    "stats_interval": 5
}

API_UPLOAD = "/api/files/upload/"
API_DELETE = "/api/files/{file_id}/delete/"
API_STATS = "/api/files/stats/"


@dataclass
class StageResult:
    label: str
    requested_files: int
    file_size_mb: float
    successful: int = 0
    failed: int = 0
    total_bytes: int = 0
    total_duration_s: float = 0.0
    latencies: List[float] = field(default_factory=list)
    throughputs: List[float] = field(default_factory=list)
    created_ids: List[int] = field(default_factory=list)
    failures: List[Dict[str, str]] = field(default_factory=list)
    stop_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        avg_latency = (sum(self.latencies) / len(self.latencies)) if self.latencies else 0
        avg_throughput = (sum(self.throughputs) / len(self.throughputs)) if self.throughputs else 0
        return {
            "label": self.label,
            "requested_files": self.requested_files,
            "successful": self.successful,
            "failed": self.failed,
            "file_size_mb": self.file_size_mb,
            "total_bytes": self.total_bytes,
            "total_duration_s": self.total_duration_s,
            "avg_latency_s": avg_latency,
            "avg_throughput_mb_s": avg_throughput,
            "created_ids": self.created_ids,
            "failures": self.failures,
            "stop_reason": self.stop_reason,
        }


class StorageStressRunner:
    def __init__(
        self,
        base_url: str,
        token: str,
        config: Dict[str, object],
        output_dir: Path,
        cleanup_after: bool = False,
        dry_run: bool = False,
        max_total_bytes: Optional[int] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Token {token}"})
        self.config = config
        self.output_dir = output_dir
        self.cleanup_after = cleanup_after
        self.dry_run = dry_run
        self.max_total_bytes = max_total_bytes

        self.upload_method = config.get("upload_method", DEFAULT_CONFIG["upload_method"])
        self.project = config.get("project", DEFAULT_CONFIG["project"])
        self.tags = config.get("tags", DEFAULT_CONFIG["tags"])

        self.stages_cfg: List[Dict[str, object]] = config.get("stages", DEFAULT_CONFIG["stages"])
        self.max_failures = int(config.get("max_failures", DEFAULT_CONFIG["max_failures"]))
        self.stats_interval = int(config.get("stats_interval", DEFAULT_CONFIG["stats_interval"]))

        self.results: List[StageResult] = []
        self.total_uploaded_bytes = 0

    # ------------------------------------------------------------------ helpers
    def _api_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _generate_payload_name(prefix: str, index: int, size_mb: float) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return f"{prefix}_{timestamp}_{index:05d}_{size_mb:.0f}MB.bin"

    @staticmethod
    def _write_synthetic_file(target: Path, size_bytes: int) -> None:
        chunk_size = 4 * 1024 * 1024  # 4 MB
        remaining = size_bytes
        with target.open("wb") as fh:
            while remaining > 0:
                this_chunk = min(chunk_size, remaining)
                fh.write(os.urandom(this_chunk))
                remaining -= this_chunk

    def _upload_file(self, file_path: Path, metadata: Dict[str, str]) -> requests.Response:
        with file_path.open("rb") as fh:
            files = {"file": (file_path.name, fh, "application/octet-stream")}
            response = self.session.post(self._api_url(API_UPLOAD), data=metadata, files=files, timeout=300)
        return response

    def _delete_file(self, file_id: int) -> None:
        try:
            self.session.delete(self._api_url(API_DELETE.format(file_id=file_id)), timeout=60)
        except requests.RequestException as exc:
            print(f"[WARN] Failed to delete file {file_id}: {exc}", file=sys.stderr)

    def _fetch_stats(self) -> Optional[Dict[str, object]]:
        try:
            resp = self.session.get(self._api_url(API_STATS), timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            print(f"[WARN] Failed to fetch stats: {exc}", file=sys.stderr)
            return None

    # ---------------------------------------------------------------- execution
    def run(self) -> Dict[str, object]:
        for stage_cfg in self.stages_cfg:
            stage = self._execute_stage(stage_cfg)
            self.results.append(stage)
            if stage.stop_reason and stage.stop_reason.startswith("failure-limit"):
                break
            if self.max_total_bytes and self.total_uploaded_bytes >= self.max_total_bytes:
                print("[INFO] Max total bytes reached, stopping further stages.")
                break

        overall = self._aggregate_results()
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "base_url": self.base_url,
            "config": self.config,
            "overall": overall,
            "stages": [stage.to_dict() for stage in self.results],
            "backend_stats": self._fetch_stats(),
        }
        return payload

    def _execute_stage(self, stage_cfg: Dict[str, object]) -> StageResult:
        label = stage_cfg.get("label", "unnamed-stage")
        file_size_mb = float(stage_cfg.get("file_size_mb", 1))
        file_count = int(stage_cfg.get("file_count", 1))
        pause_seconds = float(stage_cfg.get("pause_seconds", 0))

        stage = StageResult(label=label, requested_files=file_count, file_size_mb=file_size_mb)
        print(f"[STAGE] {label}: {file_count} files × {file_size_mb} MB")

        if self.dry_run:
            print("[DRY-RUN] Skipping uploads.")
            return stage

        size_bytes = int(file_size_mb * 1024 * 1024)

        with tempfile.TemporaryDirectory(prefix=f"storage-stress-{label}-") as tmpdir:
            tmpdir_path = Path(tmpdir)
            for index in range(file_count):
                if stage.failed >= self.max_failures:
                    stage.stop_reason = f"failure-limit({self.max_failures})"
                    print(f"[WARN] Failure limit reached in stage {label}, aborting stage.")
                    break

                if self.max_total_bytes and self.total_uploaded_bytes >= self.max_total_bytes:
                    stage.stop_reason = "max-total-bytes"
                    print(f"[INFO] Total byte cap reached ({self.total_uploaded_bytes}), stopping uploads.")
                    break

                logical_name = self._generate_payload_name(label, index, file_size_mb)
                local_file = tmpdir_path / logical_name
                self._write_synthetic_file(local_file, size_bytes)

                metadata = {
                    "upload_method": self.upload_method,
                    "title": f"[StressTest] {logical_name}",
                    "project": self.project,
                    "file_format": "other",
                    "document_type": "Dataset",
                    "access_level": "Internal",
                    "organism": "",
                    "experiment_type": "",
                    "tags": ",".join(self.tags),
                    "description": "Synthetic payload generated by storage stress harness.",
                }

                start = time.perf_counter()
                try:
                    response = self._upload_file(local_file, metadata)
                    elapsed = time.perf_counter() - start
                except requests.RequestException as exc:
                    elapsed = time.perf_counter() - start
                    stage.failed += 1
                    stage.failures.append(
                        {"index": index, "file": logical_name, "reason": f"network-error: {exc}"}
                    )
                    print(f"[ERROR] Upload failed (network) for {logical_name}: {exc}", file=sys.stderr)
                    continue

                if response.status_code == 201:
                    payload = response.json()
                    file_id = payload.get("id")
                    stage.successful += 1
                    stage.total_bytes += size_bytes
                    stage.total_duration_s += elapsed
                    stage.latencies.append(elapsed)
                    stage.throughputs.append(file_size_mb / elapsed if elapsed > 0 else math.inf)
                    if isinstance(file_id, int):
                        stage.created_ids.append(file_id)
                    self.total_uploaded_bytes += size_bytes
                    print(f"[OK] {logical_name} uploaded in {elapsed:.2f}s ({file_size_mb / max(elapsed, 1e-6):.2f} MB/s)")
                else:
                    stage.failed += 1
                    failure_detail = {
                        "index": index,
                        "file": logical_name,
                        "status": response.status_code,
                        "body": response.text[:500],
                    }
                    stage.failures.append(failure_detail)
                    print(f"[FAIL] {logical_name} returned {response.status_code}: {response.text[:120]}")
                    if response.status_code in (507, 413, 507):
                        stage.stop_reason = f"http-error-{response.status_code}"
                        break

                if pause_seconds > 0:
                    time.sleep(pause_seconds)

        if self.cleanup_after and stage.created_ids:
            for file_id in stage.created_ids:
                self._delete_file(file_id)

        return stage

    # ------------------------------------------------------------------ summary
    def _aggregate_results(self) -> Dict[str, object]:
        total_files = sum(stage.successful for stage in self.results)
        total_failures = sum(stage.failed for stage in self.results)
        total_bytes = sum(stage.total_bytes for stage in self.results)
        total_duration = sum(stage.total_duration_s for stage in self.results)
        avg_throughput = (total_bytes / (1024 * 1024)) / total_duration if total_duration > 0 else 0
        return {
            "total_success": total_files,
            "total_failures": total_failures,
            "total_bytes": total_bytes,
            "total_bytes_gb": round(total_bytes / (1024 ** 3), 3),
            "total_duration_s": total_duration,
            "avg_throughput_mb_s": avg_throughput,
        }


# --------------------------------------------------------------------------- CLI

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BioFileManager storage stress harness")
    parser.add_argument("--config", type=Path, help="Path to JSON configuration file.")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Django backend URL.")
    parser.add_argument("--token", type=str, help="DRF token (fallback: BIOFILE_TOKEN env).")
    parser.add_argument("--output-dir", type=Path, default=Path("results"), help="Where to store output artefacts.")
    parser.add_argument("--cleanup-after", action="store_true", help="Delete uploaded files once the stage completes.")
    parser.add_argument("--dry-run", action="store_true", help="Plan uploads without hitting the API.")
    parser.add_argument("--max-total-bytes", type=str, default=None, help="Abort after uploading this many bytes (supports suffixes: K/M/G).")
    return parser.parse_args()


def load_config(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        print("[INFO] No config provided, using defaults.")
        return DEFAULT_CONFIG.copy()
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_size(size_str: Optional[str]) -> Optional[int]:
    if not size_str:
        return None
    size_str = size_str.strip().upper()
    units = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
    if size_str[-1] in units:
        return int(float(size_str[:-1]) * units[size_str[-1]])
    return int(size_str)


def main() -> None:
    args = parse_args()
    token = args.token or os.getenv("BIOFILE_TOKEN")
    if not token:
        print("ERROR: No token supplied. Use --token or set BIOFILE_TOKEN.", file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = StorageStressRunner(
        base_url=args.base_url,
        token=token,
        config=config,
        output_dir=output_dir,
        cleanup_after=args.cleanup_after,
        dry_run=args.dry_run,
        max_total_bytes=parse_size(args.max_total_bytes),
    )
    results = runner.run()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"storage_stress_{timestamp}.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"[RESULT] JSON summary written to {json_path}")

    # Optional Markdown snippet for quick reporting
    md_path = output_dir / f"storage_stress_{timestamp}.md"
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write("# Storage Stress Summary\n\n")
        fh.write(f"- Generated at: {results['generated_at']}\n")
        fh.write(f"- Base URL: {results['base_url']}\n")
        overall = results["overall"]
        fh.write(f"- Total success: {overall['total_success']} files\n")
        fh.write(f"- Total failures: {overall['total_failures']} files\n")
        fh.write(f"- Total volume: {overall['total_bytes_gb']:.3f} GB\n")
        fh.write(f"- Avg throughput: {overall['avg_throughput_mb_s']:.2f} MB/s\n\n")
        fh.write("| Stage | Success | Fail | Size (MB) | Avg Latency (s) | Avg Throughput (MB/s) |\n")
        fh.write("| --- | --- | --- | --- | --- | --- |\n")
        for stage in results["stages"]:
            fh.write(
                f"| {stage['label']} | {stage['successful']} | {stage['failed']} | "
                f"{stage['file_size_mb']} | {round(stage.get('avg_latency_s', 0), 2)} | "
                f"{round(stage.get('avg_throughput_mb_s', 0), 2)} |\n"
            )
    print(f"[RESULT] Markdown digest written to {md_path}")


if __name__ == "__main__":
    main()
