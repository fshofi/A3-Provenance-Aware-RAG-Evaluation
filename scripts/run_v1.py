#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from a3.evaluator import evaluate_file  # noqa: E402


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "reference_case.json"
    report = evaluate_file(source)
    output = ROOT / "outputs" / f"{source.stem}_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "output": str(output), **{key: report[key] for key in ("decision", "evaluation_complete", "publication_authorised")}}, indent=2))
    return 0 if report["decision"] in {"SUPPORTED", "QUALIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
