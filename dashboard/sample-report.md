# A3 sample findings memo
Synthetic challenge exercise; author: Shofi Ahmed Uddin.

## Decision
Use reviewer-led evidence review. Lexical matching is insufficient for automatic semantic assurance.

## Measured limitation
60 authored synthetic cases from 12 templates with five variants each. Legacy claim-support screening: TP 10, FP 20, TN 25, FN 5 (precision 33.3%, recall 66.7%).
Conservative exact-text adapter: TP 5, FP 0, TN 45, FN 10. It trades semantic coverage for abstention; zero observed false positives here does not establish general reliability.

## Review action
Check changed entities, negation, extra properties and low-overlap paraphrases manually. Publish the failing cases. Use client-labelled samples for the next evaluation; these are neither independently adjudicated nor held-out operational examples.
