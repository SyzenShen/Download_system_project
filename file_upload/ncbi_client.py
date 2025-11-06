import os
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"
ESUMMARY_URL = f"{EUTILS_BASE}/esummary.fcgi"
SRA_FASTQ_URL = "https://trace.ncbi.nlm.nih.gov/Traces/sra-reads-be/fastq"

DEFAULT_MAX_BYTES = getattr(settings, "NCBI_MAX_DOWNLOAD_BYTES", 1024 * 1024 * 1024)  # 1 GiB
DEFAULT_TIMEOUT = getattr(settings, "NCBI_HTTP_TIMEOUT", 120)


class NCBIDownloadError(Exception):
  """Raised when an NCBI resource cannot be fetched."""


class NCBIDownloadTooLarge(NCBIDownloadError):
  """Raised if the download exceeds the configured size limit."""


@dataclass
class NCBIDownloadResult:
  accession: str
  db: str
  filename: str
  file_path: str
  file_format: str
  document_type: str
  metadata: Dict[str, object]


RESOURCE_MAP: Dict[str, Dict[str, str]] = {
  "nuccore": {"db": "nuccore", "rettype": "fasta", "retmode": "text", "ext": "fasta", "document_type": "Dataset"},
  "nucleotide": {"db": "nuccore", "rettype": "fasta", "retmode": "text", "ext": "fasta", "document_type": "Dataset"},
  "protein": {"db": "protein", "rettype": "fasta", "retmode": "text", "ext": "fasta", "document_type": "Dataset"},
  "gene": {"db": "gene", "rettype": "xml", "retmode": "xml", "ext": "xml", "document_type": "Dataset"},
  "pubmed": {"db": "pubmed", "rettype": "abstract", "retmode": "text", "ext": "txt", "document_type": "Paper"},
  "bioproject": {"db": "bioproject", "rettype": "xml", "retmode": "xml", "ext": "xml", "document_type": "Dataset"},
  "biosample": {"db": "biosample", "rettype": "xml", "retmode": "xml", "ext": "xml", "document_type": "Dataset"},
  # Special handling keys use the "strategy" field
  "sra": {"strategy": "sra_fastq", "ext": "fastq.gz", "document_type": "Dataset"},
}

ACCESSION_PREFIX_MAP = {
  "SR": "sra",
  "ER": "sra",
  "DR": "sra",
  "PRJ": "bioproject",
  "SAM": "biosample",
  "GSE": "pubmed",  # fallback to summary text
  "GSM": "pubmed",
}

FORMAT_MAP = {
  "fasta": "FASTA",
  "fa": "FASTA",
  "fastq": "FASTQ",
  "fastq.gz": "FASTQ",
  "fq": "FASTQ",
  "fq.gz": "FASTQ",
  "gb": "other",
  "gbff": "other",
  "xml": "XML",
  "txt": "txt",
  "pdb": "other",
}


def parse_ncbi_url(url: str) -> Tuple[str, str]:
  """
  Attempt to infer (resource, accession) from an arbitrary NCBI URL.
  Raises NCBIDownloadError if parsing fails.
  """
  parsed = urlparse(url)
  path_parts = [part for part in parsed.path.split("/") if part]

  resource = path_parts[0].lower() if path_parts else ""
  accession = path_parts[1] if len(path_parts) > 1 else ""

  query = parse_qs(parsed.query)
  candidate_keys = ("id", "term", "acc", "run")
  if not accession:
    for key in candidate_keys:
      if key in query and query[key]:
        accession = query[key][0]
        break

  if accession:
    accession = accession.strip()

  if not accession:
    # Try to extract accession-like token from URL
    match = re.search(r"(PRJ[A-Z0-9]+|SAMN[0-9]+|SR[RPX][0-9]+|ER[RPX][0-9]+|DR[RPX][0-9]+|GSE[0-9]+|GSM[0-9]+|[A-Z]{2}_[0-9.]+)", url)
    if match:
      accession = match.group(1)

  if not resource or resource == "entrez":
    # Guess resource from accession prefix
    if accession:
      for prefix, mapped in ACCESSION_PREFIX_MAP.items():
        if accession.upper().startswith(prefix):
          resource = mapped
          break

  if not resource:
    raise NCBIDownloadError("无法识别 NCBI 链接类型")
  if not accession:
    raise NCBIDownloadError("无法从链接中解析出 accession/ID")

  resource = resource.lower()
  return resource, accession


def _download_streaming(url: str, params: Optional[Dict[str, str]], suffix: str, max_bytes: int) -> Tuple[str, int, Dict[str, str]]:
  with requests.get(url, params=params, stream=True, timeout=DEFAULT_TIMEOUT) as resp:
    if resp.status_code != 200:
      raise NCBIDownloadError(f"NCBI 返回错误状态码 {resp.status_code}")
    total_bytes = 0
    headers = resp.headers
    content_length = headers.get("Content-Length")
    if content_length and int(content_length) > max_bytes:
      raise NCBIDownloadTooLarge(f"文件大小 {content_length} 超过限制 {max_bytes}")

    handle, file_path = tempfile.mkstemp(suffix=f".{suffix}")
    with os.fdopen(handle, "wb") as tmp:
      for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
          continue
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
          tmp.close()
          os.remove(file_path)
          raise NCBIDownloadTooLarge(f"文件大小超过限制 {max_bytes} 字节")
        tmp.write(chunk)
    return file_path, total_bytes, headers


def _fetch_summary(db: str, accession: str) -> Dict[str, object]:
  params = {"db": db, "id": accession, "retmode": "json"}
  try:
    resp = requests.get(ESUMMARY_URL, params=params, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
  except Exception:
    return {}

  result = data.get("result", {})
  uid = (result.get("uids") or [None])[0]
  if not uid:
    return {}

  summary = result.get(uid, {})
  metadata = {
    "title": summary.get("title") or summary.get("extra", ""),
    "organism": summary.get("organism") or summary.get("taxname"),
    "length": summary.get("slen") or summary.get("length"),
    "status": summary.get("status"),
    "summary": summary.get("summary") or summary.get("caption") or summary.get("subname"),
    "experiment_type": summary.get("strategy") or summary.get("librarystrategy"),
    "links": summary.get("linksetdbs"),
  }
  return {k: v for k, v in metadata.items() if v}


def _normalize_file_format(extension: str) -> str:
  extension = extension.lower()
  if extension in FORMAT_MAP:
    return FORMAT_MAP[extension]
  return "other"


def download_ncbi_resource(url: str, max_bytes: Optional[int] = None) -> NCBIDownloadResult:
  resource, accession = parse_ncbi_url(url)
  config = RESOURCE_MAP.get(resource)

  if not config:
    raise NCBIDownloadError(f"暂不支持的 NCBI 资源类型：{resource}")

  max_allowed = max_bytes or DEFAULT_MAX_BYTES
  strategy = config.get("strategy")

  if strategy == "sra_fastq":
    suffix = config["ext"]
    params = {"acc": accession}
    file_path, total_bytes, headers = _download_streaming(SRA_FASTQ_URL, params=params, suffix=suffix, max_bytes=max_allowed)
    file_format = _normalize_file_format(suffix)
    metadata = _fetch_summary("sra", accession)
    metadata.update({
      "ncbi_db": "sra",
      "download_bytes": total_bytes,
      "source_url": url,
    })
    filename = f"{accession}.{suffix}"
    return NCBIDownloadResult(
      accession=accession,
      db="sra",
      filename=filename,
      file_path=file_path,
      file_format=file_format,
      document_type=config.get("document_type", "Dataset"),
      metadata=metadata,
    )

  db = config["db"]
  params = {
    "db": db,
    "id": accession,
    "rettype": config.get("rettype"),
    "retmode": config.get("retmode"),
  }
  suffix = config.get("ext", "txt")
  params = {k: v for k, v in params.items() if v}

  file_path, total_bytes, headers = _download_streaming(EFETCH_URL, params=params, suffix=suffix, max_bytes=max_allowed)
  file_format = _normalize_file_format(suffix)
  metadata = _fetch_summary(db, accession)
  metadata.update({
    "ncbi_db": db,
    "download_bytes": total_bytes,
    "source_url": url,
  })

  content_disposition = headers.get("Content-Disposition")
  if content_disposition:
    match = re.search(r'filename=\"?([^\";]+)', content_disposition)
    if match:
      filename = match.group(1)
    else:
      filename = f"{accession}.{suffix}"
  else:
    filename = f"{accession}.{suffix}"

  return NCBIDownloadResult(
    accession=accession,
    db=db,
    filename=filename,
    file_path=file_path,
    file_format=file_format,
    document_type=config.get("document_type", "Dataset"),
    metadata=metadata,
  )
