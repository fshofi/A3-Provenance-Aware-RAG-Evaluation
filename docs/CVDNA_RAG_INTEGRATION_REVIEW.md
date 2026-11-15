# CVDNA RAG integration — A3 review baseline

**Status:** DESIGN / REVIEW ONLY. No claim of completed integration or passing new tests.

**Baseline:** main tree `949054fd40d2cd29908add6f63f3918b905771ca` (inspected 2026-11-15).

## Observed A3 architecture

A3 evaluates supplied retrieved passages and proposed answers using deterministic lexical support, provenance SHA-256, citation resolution, explicit contradiction rules, staleness checks, decision states and audit events. It does not implement live retrieval, embeddings, vector search or reranking. Preserve the current evaluator, existing fixtures and tests unchanged until regression evidence is captured.

## Proposed versioned interface

- `schemas/cvdna_evidence_record.v1.schema.json` is a proposed cross-project record for retrieved chunks.
- The record is not a replacement for `schemas/evaluation_input.schema.json`; an adapter is required.
- SHA-256 hashes are hex-encoded digests of the exact source and chunk text bytes; canonical encoding and offset rules must be specified before claiming replay equivalence.
- Similarity scores are not calibrated probabilities. Store the scoring method and version alongside any future scores.
- `dependency_group` is a review annotation, not proof of source independence.

## Next implementation gates

1. Run the original A3 test suite on an unmodified checkout and record interpreter, commit, command and full output.
2. Validate the new schema against valid and invalid fixtures (schema validation is not yet executed).
3. Add a non-invasive adapter from existing A3 source/passage records, preserving source identifiers and citations.
4. Implement the twelve R01–R12 adversarial fixtures with machine-checkable expected dispositions and replay traces.
5. Verify no existing evaluator decision or publication-authority behaviour changes.
6. Only then consider retrieval/reranking modules; benchmark against a lexical baseline.

## Boundary

A3 remains the evaluator of supplied retrieval. SDA evaluates evidential sufficiency; CVDNA governs proposed external execution. A human approval flag cannot repair a failed evidence gate. No autonomous execution is authorised by this document.
