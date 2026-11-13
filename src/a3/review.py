"""Conservative client-review adapter; exact matches are not truth certificates."""
import copy
import re
from .evaluator import evaluate_case
from .text import citations

def normalise(text):
    text=re.sub(r'\[[A-Za-z0-9_.:-]+\]','',text)
    return ' '.join(re.sub(r'[^\w\s]',' ',text.casefold()).split())

def evaluate_review_case(case):
    result=copy.deepcopy(evaluate_case(case))
    passages=case.get('retrieved_passages',[])
    requires_review=False
    for claim in result['claims']:
        if claim['status']=='SUPPORTED':
            cited=set(citations(claim['text']))
            exact=any(p.get('source_id') in cited and normalise(claim['text'])==normalise(str(p.get('text',''))) for p in passages)
            if not exact:
                claim['status']='REVIEW_REQUIRED'
                claim['reason']='Lexical similarity alone cannot establish semantic support; reviewer must adjudicate.'
                requires_review=True
    if requires_review:
        result['findings'].append({'code':'SEMANTIC_REVIEW_REQUIRED','severity':'HIGH','detail':'Non-exact lexical matches require reviewer adjudication.'})
        if result['decision'] in ('SUPPORTED','QUALIFIED'): result['decision']='INSUFFICIENT_EVIDENCE'
    result['publication_authorised']=False
    result['review_mode']='Conservative exact-text screening; no automated publication authority'
    result['audit'].append({'sequence':len(result['audit'])+1,'node':'client_review_boundary','status':'REVIEW_REQUIRED' if requires_review else 'RECORDED','detail':'Publication remains with accountable reviewer.'})
    return result
