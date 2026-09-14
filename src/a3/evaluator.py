"""Evidence-governed evaluator for supplied RAG retrieval and answers."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .text import citations, claims, numbers, overlap_score, tokens


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _event(audit: list[dict[str, Any]], node: str, status: str, detail: str) -> None:
    audit.append({"sequence": len(audit) + 1, "node": node, "status": status, "detail": detail})


def _ordered_numbers(text: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?%?", text)


def _contradiction(claim: str, passage: str) -> str | None:
    c, p = tokens(claim), tokens(passage)
    claim_lower = claim.lower()
    passage_lower = passage.lower()

    negated_requirement = bool(re.search(r"(?:not|does\s+not|no)\b.{0,35}\b(?:require|required|requirement|mandatory|certif)", claim_lower))
    if "require" in c and "voluntary" in p and "voluntary" not in c and not negated_requirement:
        return "claim converts voluntary guidance into a requirement"
    if "voluntary" in c and "require" in p and "voluntary" not in p:
        return "claim describes a requirement as voluntary"

    causal_claim = bool(re.search(r"\b(cause|causes|caused|causal|because of|led to|leads to|resulted in|drives?|produced)\b", claim_lower))
    causal_denial = bool(re.search(r"\b(cannot|can not|does not|did not|no)\b.{0,45}\b(caus|attribut|establish|infer)", passage_lower)) or bool(
        re.search(r"\b(association|correlation|observational)\b.{0,55}\b(?:not|cannot|does not)\b.{0,35}\bcaus", passage_lower)
    )
    if causal_claim and causal_denial:
        return "claim asserts causation where the cited evidence explicitly withholds causal inference"

    universal_claim = bool(re.search(r"\b(all|every|across all|universally|general(?:ise|ize|ises|izes|ised|ized))\b", claim_lower))
    scope_limit = bool(re.search(r"\b(exclud(?:e|ed|es|ing)|non-comparable|not comparable|cannot general(?:ise|ize)|limited to|selected cases|subset)\b", passage_lower))
    if universal_claim and scope_limit:
        return "claim exceeds an explicit scope or comparability limitation in the cited evidence"

    cn, pn = numbers(claim), numbers(passage)
    if cn and pn and cn.isdisjoint(pn):
        return f"incompatible numeric values: claim={sorted(cn)}, passage={sorted(pn)}"

    cseq, pseq = _ordered_numbers(claim), _ordered_numbers(passage)
    if len(cseq) >= 2 and len(pseq) >= 2 and set(cseq[:2]) == set(pseq[:2]) and cseq[:2] == list(reversed(pseq[:2])):
        return f"directional numeric relation is reversed: claim={cseq[:2]}, passage={pseq[:2]}"

    opposite_direction = (
        bool(re.search(r"\b(increase|increased|rose|rise|higher|grew|growth)\b", claim_lower))
        and bool(re.search(r"\b(decrease|decreased|fell|reduced|reduction|lower)\b", passage_lower))
    ) or (
        bool(re.search(r"\b(decrease|decreased|fell|reduced|reduction|lower)\b", claim_lower))
        and bool(re.search(r"\b(increase|increased|rose|rise|higher|grew|growth)\b", passage_lower))
    )
    if opposite_direction and cn and pn and not cn.isdisjoint(pn):
        return "claim reverses the direction of the cited quantitative change"
    return None


def _neutral_reason(claim: str, passage: str) -> str | None:
    claim_lower = claim.lower()
    passage_lower = passage.lower()

    absence = re.search(
        r"\b(?:does not|did not|cannot|can not|no)\b.{0,55}\b(?:contain|include|provide|report|measure|record|show|give)\b.{0,55}\b(?:data|evidence|information|measure|metric|result)",
        passage_lower,
    )
    if absence:
        claim_terms = tokens(claim)
        passage_terms = tokens(passage)
        shared = claim_terms & passage_terms
        if len(shared) >= 2:
            return "cited passage is topically related but explicitly states that the required evidence is absent"

    qualification = bool(re.search(r"\b(exclud(?:e|ed|es|ing)|non-comparable|not comparable|limited to|selected cases|subset)\b", passage_lower))
    overreach = bool(re.search(r"\b(all|every|across all|universally|general(?:ise|ize|ises|izes|ised|ized))\b", claim_lower))
    if qualification and overreach:
        return "cited passage is related but does not support the claim beyond its stated scope"

    return None


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    audit: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    blocking = False
    warnings = False

    query = str(case.get("query", "")).strip()
    answer = str(case.get("answer", "")).strip()
    sources = {item["id"]: item for item in case.get("sources", []) if item.get("id")}
    passages = case.get("retrieved_passages", [])
    consequence = case.get("consequence", "moderate")
    _event(audit, "task_intake", "PASS" if query and answer else "FAIL", "query and proposed answer received")
    if not query or not answer:
        return _finish("SAFE_STOP", False, False, findings + [{"code": "TASK_INCOMPLETE", "severity": "CRITICAL", "detail": "query and answer are required"}], audit)

    provenance_ok = bool(sources)
    if not sources:
        findings.append({"code": "NO_SOURCES", "severity": "CRITICAL", "detail": "no source records supplied"})
    for source in sources.values():
        expected = source.get("content_sha256")
        actual = _sha(str(source.get("content", "")))
        if not expected or expected != actual:
            provenance_ok = False
            findings.append({"code": "PROVENANCE_FAILURE", "severity": "CRITICAL", "detail": f"source {source['id']} hash is absent or does not match"})
    _event(audit, "provenance", "PASS" if provenance_ok else "FAIL", f"verified {len(sources)} source record(s)")
    blocking |= not provenance_ok

    passage_by_source: dict[str, list[dict[str, Any]]] = {}
    invalid_passages = []
    altered_passages = []
    truncated_passages = []
    for passage in passages:
        source_id = passage.get("source_id")
        if source_id not in sources:
            invalid_passages.append(str(source_id))
        else:
            passage_by_source.setdefault(source_id, []).append(passage)
            if str(passage.get("text", "")) not in str(sources[source_id].get("content", "")):
                altered_passages.append(str(passage.get("passage_id", source_id)))
            if passage.get("truncated") is True:
                truncated_passages.append(str(passage.get("passage_id", source_id)))
    if invalid_passages:
        findings.append({"code": "UNKNOWN_RETRIEVAL_SOURCE", "severity": "CRITICAL", "detail": f"unresolved source ids: {', '.join(invalid_passages)}"})
        blocking = True
    if altered_passages:
        findings.append({"code": "PASSAGE_INTEGRITY_FAILURE", "severity": "CRITICAL", "detail": f"passage not recoverable from recorded source content: {', '.join(altered_passages)}"})
        blocking = True
    if truncated_passages:
        findings.append({"code": "CONTEXT_TRUNCATION", "severity": "HIGH", "detail": f"retrieved context marked truncated: {', '.join(truncated_passages)}"})
        warnings = True
    _event(audit, "retrieval", "FAIL" if invalid_passages or altered_passages else "WARN" if truncated_passages else "PASS", f"received {len(passages)} passage(s)")

    required = set(case.get("required_evidence_ids", []))
    retrieved_ids = set(passage_by_source)
    omitted = sorted(required - retrieved_ids)
    if omitted:
        findings.append({"code": "RETRIEVAL_OMISSION", "severity": "CRITICAL", "detail": f"required evidence not retrieved: {', '.join(omitted)}"})
        blocking = True
    _event(audit, "omission_gate", "FAIL" if omitted else "PASS", "required-evidence coverage checked")

    as_of = datetime.strptime(case.get("as_of_date", date.today().isoformat()), "%Y-%m-%d").date()
    max_age = case.get("max_source_age_days")
    stale_ids: list[str] = []
    if max_age is not None:
        for source_id in retrieved_ids:
            published = sources[source_id].get("published_at")
            if published and (as_of - datetime.strptime(published, "%Y-%m-%d").date()).days > int(max_age):
                stale_ids.append(source_id)
    if stale_ids:
        findings.append({"code": "STALE_EVIDENCE", "severity": "HIGH", "detail": f"age threshold exceeded: {', '.join(sorted(stale_ids))}"})
        warnings = True
    _event(audit, "temporal_validity", "WARN" if stale_ids else "PASS", "source age checked")

    query_relevance = []
    for passage in passages:
        query_relevance.append(overlap_score(query, str(passage.get("text", ""))))
    low_relevance = bool(passages) and max(query_relevance, default=0.0) < float(case.get("query_relevance_threshold", 0.12))
    if low_relevance:
        findings.append({"code": "LOW_RETRIEVAL_RELEVANCE", "severity": "HIGH", "detail": "no passage clears the query-relevance threshold"})
        warnings = True
    _event(audit, "passage_relevance", "WARN" if low_relevance else "PASS", "query–passage relevance measured")

    claim_rows: list[dict[str, Any]] = []
    unsupported = False
    contradicted = False
    atomised_claims = claims(answer)
    if not atomised_claims:
        findings.append({"code": "NO_MATERIAL_CLAIM", "severity": "CRITICAL", "detail": "answer contains no evaluable material claim"})
        blocking = True
    for index, claim in enumerate(atomised_claims, 1):
        cited = citations(claim)
        if not cited:
            claim_rows.append({"claim_id": f"C{index}", "text": claim, "citations": [], "support_score": 0.0, "status": "UNSUPPORTED", "reason": "no citation"})
            unsupported = True
            continue
        unresolved = [source_id for source_id in cited if source_id not in sources]
        if unresolved:
            claim_rows.append({"claim_id": f"C{index}", "text": claim, "citations": cited, "support_score": 0.0, "status": "INVALID_CITATION", "reason": f"unknown citation: {', '.join(unresolved)}"})
            blocking = True
            continue
        candidate_passages = [p for source_id in cited for p in passage_by_source.get(source_id, [])]
        best_score, contradiction, neutral_reason = 0.0, None, None
        for passage in candidate_passages:
            text = str(passage.get("text", ""))
            best_score = max(best_score, overlap_score(claim, text))
            contradiction = contradiction or _contradiction(claim, text)
            neutral_reason = neutral_reason or _neutral_reason(claim, text)
        claim_tokens = tokens(claim)
        passage_tokens = set().union(*(tokens(str(p.get("text", ""))) for p in candidate_passages)) if candidate_passages else set()
        high_stakes_novel = sorted(({"guarantee", "safe", "certify", "illegal", "prohibit", "approve"} & claim_tokens) - passage_tokens)
        if contradiction:
            status, reason = "CONTRADICTED", contradiction
            contradicted = True
        elif neutral_reason:
            status, reason = "NEUTRAL", neutral_reason
            unsupported = True
        elif high_stakes_novel:
            status, reason = "UNSUPPORTED", f"material terms absent from cited evidence: {', '.join(high_stakes_novel)}"
            unsupported = True
        elif best_score >= float(case.get("support_threshold", 0.35)):
            status, reason = "SUPPORTED", "cited passage clears bounded lexical-support threshold after contradiction and neutral-evidence checks"
        elif best_score >= 0.18:
            status, reason = "PARTIAL", "some overlap exists, but support is incomplete"
            unsupported = True
        else:
            status, reason = "UNSUPPORTED", "cited passage does not support enough of the claim"
            unsupported = True
        claim_rows.append({"claim_id": f"C{index}", "text": claim, "citations": cited, "support_score": round(best_score, 4), "status": status, "reason": reason})
    _event(audit, "claim_atomisation", "PASS", f"created {len(claim_rows)} claim record(s)")
    _event(audit, "claim_support", "FAIL" if unsupported else "PASS", "claim–source support evaluated")
    _event(audit, "contradiction", "FAIL" if contradicted else "PASS", "explicit contradiction patterns evaluated")

    if contradicted:
        findings.append({"code": "MATERIAL_CONTRADICTION", "severity": "CRITICAL" if consequence == "high" else "HIGH", "detail": "one or more claims conflict with cited evidence"})
        blocking |= consequence == "high"
    if unsupported:
        findings.append({"code": "UNSUPPORTED_CLAIM", "severity": "HIGH", "detail": "one or more material claims lack adequate cited support"})

    low_authority = [source_id for source_id in retrieved_ids if sources[source_id].get("authority") == "low"]
    if consequence == "high" and low_authority:
        findings.append({"code": "SOURCE_AUTHORITY_MISMATCH", "severity": "HIGH", "detail": f"high-consequence answer relies on low-authority source(s): {', '.join(sorted(low_authority))}"})
        warnings = True
    _event(audit, "authority_quality", "WARN" if low_authority and consequence == "high" else "PASS", "source authority matched to consequence")

    if blocking:
        decision = "SAFE_STOP"
    elif unsupported or contradicted:
        decision = "INSUFFICIENT_EVIDENCE"
    elif warnings or findings:
        decision = "QUALIFIED"
    else:
        decision = "SUPPORTED"
    complete = not blocking
    authorised = bool(case.get("human_approval")) and decision == "SUPPORTED" and consequence == "low"
    _event(audit, "governance", decision, "evidence-bound decision issued")
    _event(audit, "publication_authority", "AUTHORISED" if authorised else "NOT_AUTHORISED", "approval cannot repair evidence failure")
    return _finish(decision, complete, authorised, findings, audit, claim_rows)


def _finish(decision: str, complete: bool, authorised: bool, findings: list[dict[str, str]], audit: list[dict[str, Any]], claim_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "decision": decision,
        "evaluation_complete": complete,
        "publication_authorised": authorised,
        "claims": claim_rows or [],
        "findings": findings,
        "audit": audit,
    }


def evaluate_file(path: Path) -> dict[str, Any]:
    return evaluate_case(json.loads(path.read_text(encoding="utf-8")))
