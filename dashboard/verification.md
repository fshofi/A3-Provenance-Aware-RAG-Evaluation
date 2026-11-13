# Current verification — 13 November 2026

25/25 tests pass, including 3 conservative-review adapter checks. A separate 60-case synthetic challenge set measures claim-support screening, not final governance decisions. Legacy TP/FP/TN/FN = 10/20/25/5. Conservative = 5/0/45/10. Template variants are correlated; no independent adjudication or generalisation estimate. Browser screening now also routes non-exact matches to review and never grants publication authority. The browser and Python adapters are separate implementations.

Raw test output: `../evidence/client_readiness/unit_tests.txt`.

Test log checkout prefixes are normalised for public sharing. Browser checks: A1 numeric error → REPAIR REQUIRED; A2 leakage → DATA_QUALITY_FAILURE; A3 contradiction → SAFE_STOP and paraphrase → INSUFFICIENT_EVIDENCE, publication false. Desktop rendering inspected; narrow-screen behaviour not interactively tested.
