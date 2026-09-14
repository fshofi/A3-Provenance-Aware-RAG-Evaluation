# A3 V1 Methodology

## Scope

A3 evaluates a proposed answer against supplied retrieval evidence. It does not generate the answer, retrieve from the open web, or inspect hidden reasoning.

## Observable evaluation layers

1. **Source identity:** source ID, publisher, URL or recoverable identifier, dates and authority label.
2. **Integrity:** SHA-256 comparison of recorded source content.
3. **Retrieval:** source resolution, required-evidence coverage and bounded query relevance.
4. **Claim support:** sentence-level claim atomisation, citation resolution and deterministic lexical support.
5. **Contradiction:** explicit mandate/voluntary, negation and numeric-conflict patterns.
6. **Temporal validity:** evidence age against a declared threshold.
7. **Governance:** consequence-aware source authority and a separate publication-authority decision.

## Why deterministic V1

The first release favours replayable, inspectable failure logic over opaque evaluator-model scoring. This makes the exact boundary testable. It also limits semantic coverage, which is disclosed rather than hidden.

## Reference source

The included reference passage is a short project-authored paraphrase of the official NIST AI RMF page, retrieved 14 September 2026. It is not presented as a complete reproduction of the NIST publication.
