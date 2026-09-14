from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from a3 import evaluate_case  # noqa: E402


def load_reference():
    return json.loads((ROOT / "data" / "reference_case.json").read_text())


def resign(source):
    source["content_sha256"] = hashlib.sha256(source["content"].encode()).hexdigest()


class EvaluationTests(unittest.TestCase):
    def test_reference_answer_supported_but_not_authorised(self):
        result = evaluate_case(load_reference())
        self.assertEqual(result["decision"], "SUPPORTED")
        self.assertTrue(result["evaluation_complete"])
        self.assertFalse(result["publication_authorised"])
        self.assertEqual(result["claims"][0]["status"], "SUPPORTED")

    def test_low_consequence_supported_answer_can_record_publication_approval(self):
        case = load_reference()
        case["consequence"] = "low"
        case["human_approval"] = True
        self.assertTrue(evaluate_case(case)["publication_authorised"])

    def test_approval_cannot_override_material_contradiction(self):
        case = json.loads((ROOT / "data" / "hostile_mandatory_claim.json").read_text())
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "SAFE_STOP")
        self.assertFalse(result["publication_authorised"])

    def test_tampered_source_fails_closed(self):
        case = load_reference()
        case["sources"][0]["content"] += " tampered"
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "SAFE_STOP")
        self.assertFalse(result["evaluation_complete"])

    def test_unknown_citation_fails_closed(self):
        case = load_reference()
        case["answer"] = "The framework is voluntary [UNKNOWN]."
        self.assertEqual(evaluate_case(case)["decision"], "SAFE_STOP")

    def test_uncited_claim_is_insufficient(self):
        case = load_reference()
        case["answer"] = "The framework is voluntary."
        self.assertEqual(evaluate_case(case)["decision"], "INSUFFICIENT_EVIDENCE")

    def test_required_retrieval_omission_safe_stops(self):
        case = load_reference()
        case["retrieved_passages"] = []
        self.assertEqual(evaluate_case(case)["decision"], "SAFE_STOP")

    def test_stale_evidence_is_qualified(self):
        case = load_reference()
        case["max_source_age_days"] = 100
        self.assertEqual(evaluate_case(case)["decision"], "QUALIFIED")

    def test_low_authority_is_qualified_for_high_consequence(self):
        case = load_reference()
        case["consequence"] = "high"
        case["sources"][0]["authority"] = "low"
        self.assertEqual(evaluate_case(case)["decision"], "QUALIFIED")

    def test_numeric_conflict_is_detected(self):
        case = load_reference()
        content = "The measured failure rate is 12 percent in the bounded evaluation."
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "The measured failure rate is 45 percent [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "CONTRADICTED")
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")

    def test_incomplete_task_safe_stops(self):
        case = load_reference()
        case["query"] = ""
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "SAFE_STOP")
        self.assertFalse(result["evaluation_complete"])

    def test_no_sources_safe_stops(self):
        case = load_reference()
        case["sources"] = []
        self.assertEqual(evaluate_case(case)["decision"], "SAFE_STOP")

    def test_altered_retrieved_passage_safe_stops(self):
        case = load_reference()
        case["retrieved_passages"][0]["text"] += " Fabricated extension."
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "SAFE_STOP")
        self.assertIn("PASSAGE_INTEGRITY_FAILURE", {x["code"] for x in result["findings"]})

    def test_explicit_context_truncation_is_qualified(self):
        case = load_reference()
        case["retrieved_passages"][0]["truncated"] = True
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "QUALIFIED")
        self.assertIn("CONTEXT_TRUNCATION", {x["code"] for x in result["findings"]})

    def test_novel_guaranteed_safety_claim_is_unsupported(self):
        case = load_reference()
        case["answer"] = "NIST guarantees that every compliant AI system is safe [NIST-AI-RMF]."
        result = evaluate_case(case)
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["claims"][0]["status"], "UNSUPPORTED")

    def test_answer_without_material_claim_safe_stops(self):
        case = load_reference()
        case["answer"] = "Yes."
        self.assertEqual(evaluate_case(case)["decision"], "SAFE_STOP")

    def test_audit_ends_with_authority_decision(self):
        result = evaluate_case(load_reference())
        self.assertEqual(result["audit"][-1]["node"], "publication_authority")
        self.assertEqual(result["audit"][-1]["status"], "NOT_AUTHORISED")


    def test_fabio_causal_overclaim_is_contradicted(self):
        case = load_reference()
        content = (
            "Resolution time fell from 10 minutes to 7 minutes after a process change. "
            "The study was observational and does not establish that the process change caused the reduction."
        )
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "The process change caused resolution time to fall from 10 to 7 minutes [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "CONTRADICTED")
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(result["publication_authorised"])

    def test_fabio_explicit_no_causation_is_not_supported(self):
        case = load_reference()
        content = (
            "Resolution time fell from 10 minutes to 7 minutes. "
            "The evidence does not permit concluding causation."
        )
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "The intervention caused resolution time to fall from 10 to 7 minutes [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "CONTRADICTED")
        self.assertNotEqual(result["decision"], "SUPPORTED")

    def test_fabio_directional_numeric_inversion_is_contradicted(self):
        case = load_reference()
        content = "Resolution time decreased from 10 minutes to 7 minutes in the measured period."
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "Resolution time increased from 7 minutes to 10 minutes [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "CONTRADICTED")
        self.assertNotEqual(result["decision"], "SUPPORTED")

    def test_fabio_related_but_absent_evidence_is_neutral(self):
        case = load_reference()
        content = (
            "Customer volume grew by 20 percent during the period. "
            "The report does not provide data on resolution time."
        )
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "Resolution time improved by 20 percent [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "NEUTRAL")
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(result["publication_authorised"])

    def test_fabio_scope_overreach_is_not_supported(self):
        case = load_reference()
        content = (
            "Resolution time fell from 10 minutes to 7 minutes in the selected comparable cases. "
            "Complex cases were excluded and the populations were not comparable."
        )
        source = case["sources"][0]
        source["content"] = content
        resign(source)
        case["retrieved_passages"][0]["text"] = content
        case["answer"] = "Resolution time fell from 10 to 7 minutes across all cases [NIST-AI-RMF]."
        case["required_evidence_ids"] = []
        result = evaluate_case(case)
        self.assertEqual(result["claims"][0]["status"], "CONTRADICTED")
        self.assertNotEqual(result["decision"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main()
