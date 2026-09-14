# Project A Pro — A3

## Provenance-Aware RAG / Semantic Search Evaluation

**Status:** bounded V1 vertical slice.  
**Governing boundary:** retrieval is not evidence, and citation is not proof of support.

A3 evaluates a supplied RAG answer against the passages that were retrieved for it. It verifies source identity and integrity, atomises the answer into claims, checks citation resolution and claim–passage support, identifies contradiction and staleness signals, distinguishes retrieval omission from synthesis failure, and separates answer evaluation from publication authority.

The V1 evaluator is deterministic and inspectable. It does **not** expose hidden model reasoning, certify truth, replace subject-matter review, or claim production deployment.

## Evaluation chain

`QUERY → RETRIEVAL → SOURCE IDENTITY → PROVENANCE → PASSAGE RELEVANCE → CLAIM ATOMISATION → CLAIM–SOURCE SUPPORT → CONTRADICTION → EVIDENCE BOUNDARY → HUMAN REVIEW → REPLAY`

## Run

```bash
python scripts/run_v1.py data/reference_case.json
python -m unittest discover -s tests -v
```

The reference fixture uses a paraphrased statement grounded in the official NIST AI Risk Management Framework page. NIST describes AI RMF 1.0 as intended for voluntary use. A3 tests whether a proposed answer preserves that boundary rather than converting it into a mandatory-certification claim.

Official source: https://www.nist.gov/itl/ai-risk-management-framework

## Decision states

- `SUPPORTED`: all material claims have resolved support and no blocking finding.
- `QUALIFIED`: usable evidence exists, but a visible limitation requires qualification.
- `INSUFFICIENT_EVIDENCE`: one or more material claims lack adequate support.
- `SAFE_STOP`: provenance failure, invalid citation, material contradiction, or required-evidence omission blocks progression.

`evaluation_complete` and `publication_authorised` are separate fields. Approval cannot repair defective evidence.

The browser dashboard also includes one restrained Plotly evidence-to-publication gate. It visualises provenance, retrieval, citation, support, contradiction, temporal validity and publication authority as categorical PASS / REVIEW / FAIL states. These visual states are not truth probabilities and do not alter the evaluator decision.

## V1 limitations

- Claim atomisation is sentence-based.
- Support scoring is deterministic lexical evidence matching, not a neural entailment model.
- Contradiction rules cover explicit negation, mandate/voluntary conflicts and incompatible numbers; they are not exhaustive.
- Source-authority labels are supplied metadata and must be independently governed in real use.
- V1 evaluates supplied retrieval; it does not connect to a vector database or production knowledge store.
- Human validation and production security testing remain future gates.

## AI assistance

A3 is an AI-assisted software and research artifact owned and publication-controlled by Shofi Ahmed Uddin. Public claims must remain bounded to the included code, fixtures and test evidence.
