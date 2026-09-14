# A3 architecture

| Node | Input | Output | Failure behaviour |
|---|---|---|---|
| Task intake | Query, answer, consequence | Fixed evaluation contract | Safe-stop if incomplete |
| Source identity | Source metadata | Recoverable source record | Safe-stop if absent |
| Provenance | Content and recorded SHA-256 | Integrity verdict | Safe-stop on mismatch |
| Retrieval | Passages and required evidence | Coverage and passage integrity | Safe-stop on omission or alteration |
| Relevance | Query and passages | Bounded overlap score | Qualification warning |
| Claim atomiser | Proposed answer | Sentence-level claim records | Safe-stop if no material claim |
| Citation resolver | Claim citations and source IDs | Resolved evidence candidates | Safe-stop on unknown citation |
| Support evaluator | Claim and cited passages | Supported, partial or unsupported | Insufficient evidence |
| Contradiction gate | Claim and cited passages | Explicit conflict signal | Safe-stop when high-consequence |
| Temporal gate | Source dates and declared age limit | Staleness finding | Qualification warning |
| Governance gate | Findings and consequence | Evidence decision | Defaults away from authority |
| Publication authority | Decision and approval | Boolean authority record | Approval cannot repair evidence |

All nodes are bounded deterministic services. “Agent” describes explicit responsibility and state transition, not an autonomous persona.
