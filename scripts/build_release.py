#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {"__pycache__", ".git", ".venv"}
EXCLUDED_NAMES = {"SHA256_MANIFEST.txt"}


def files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in {".pyc", ".pyo"}:
            continue
        yield path


def main():
    lines = []
    selected = list(files())
    for path in selected:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    manifest = ROOT / "SHA256_MANIFEST.txt"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    archive = ROOT.parent / "A3-Provenance-Aware-RAG-Evaluation-V1.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in [*selected, manifest]:
            bundle.write(path, (Path(ROOT.name) / path.relative_to(ROOT)).as_posix())
    print(f"manifest_entries={len(lines)}")
    print(f"archive={archive}")


if __name__ == "__main__":
    main()
