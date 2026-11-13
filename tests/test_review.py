import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from a3.review import evaluate_review_case
class ReviewTests(unittest.TestCase):
    def fixture(self):
        return json.loads((Path(__file__).resolve().parents[1]/'data/reference_case.json').read_text())
    def test_nonexact_support_needs_review(self):
        case=self.fixture();result=evaluate_review_case(case)
        self.assertFalse(result['publication_authorised'])
        self.assertTrue(any(c['status']=='REVIEW_REQUIRED' for c in result['claims']))
    def test_approval_never_grants_publication(self):
        case=self.fixture();case.update(human_approval=True,consequence='low')
        self.assertFalse(evaluate_review_case(case)['publication_authorised'])
    def test_integrity_failure_still_blocks(self):
        case=self.fixture();case['sources'][0]['content']='tampered'
        self.assertEqual(evaluate_review_case(case)['decision'],'SAFE_STOP')
