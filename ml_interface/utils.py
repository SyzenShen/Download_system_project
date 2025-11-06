"""
Lightweight placeholders for future ML integrations.

Real implementations can call external services, GPU workers, etc.
"""


def handle_autotag(file_path):
  return {"labels": [], "notes": "Auto-tagging not implemented yet."}


def handle_qc(file_path):
  return {"qc_passed": True, "details": {}, "notes": "QC checks pending implementation."}


def handle_summary(file_path):
  return {"summary": "", "notes": "Summary generation pending implementation."}


def handle_embedding(file_path):
  return {"vector": [], "notes": "Embedding extraction pending implementation."}


def handle_h5ad_vis(file_path):
  return {"umap": None, "tsne": None, "clusters": None, "notes": "h5ad preprocessing pending implementation."}
