# Reproducibility

A3 V1 uses Python's standard library only. The supported minimum is Python 3.10.

```bash
python -m unittest discover -s tests -v
python scripts/run_v1.py data/reference_case.json
python scripts/run_v1.py data/hostile_mandatory_claim.json
```

The hostile runner exits with code 2 by design because `SAFE_STOP` is not a successful evidence disposition. Generated JSON reports are written beneath `outputs/`.

Run `python scripts/build_release.py` after all checks. It creates `SHA256_MANIFEST.txt` and a ZIP beside the repository directory. The manifest excludes itself and transient Python cache files.
