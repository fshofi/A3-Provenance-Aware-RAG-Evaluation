"""Report strengths AND failures; never a production-quality estimate."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from a3.evaluator import evaluate_case
from a3.review import evaluate_review_case

def run(conservative=False):
    rows=[]; counts={'tp':0,'fp':0,'tn':0,'fn':0}
    path=ROOT/'data/client_challenge_pairs.jsonl'
    for item in map(json.loads,path.read_text().splitlines()):
        passage=item['passage']
        source={'id':'S','content':passage,'content_sha256':hashlib.sha256(passage.encode()).hexdigest(),'authority':'primary','published_at':'2026-01-01'}
        result=(evaluate_review_case if conservative else evaluate_case)({'query':'What does the passage establish?', 'answer':item['claim'].rstrip('.')+' [S].','sources':[source],'retrieved_passages':[{'source_id':'S','passage_id':'P','text':passage}],'as_of_date':'2026-11-13','consequence':'moderate','human_approval':False})
        predicted=bool(result['claims']) and all(c['status']=='SUPPORTED' for c in result['claims']); actual=item['expected']=='SUPPORTED'
        category='tp' if predicted and actual else 'fp' if predicted else 'fn' if actual else 'tn'
        counts[category]+=1
        rows.append({**item,'predicted_decision':result['decision'],'category':category,'claim_results':result['claims']})
    tp,fp,tn,fn=(counts[k] for k in ('tp','fp','tn','fn'))
    summary={'n':len(rows),'counts':counts,'support_precision':tp/(tp+fp) if tp+fp else None,'support_recall':tp/(tp+fn) if tp+fn else None,'accuracy':(tp+tn)/len(rows),'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'60 synthetic cases; 12 templates with 5 variants each; related cases are not independent; no held-out or production validity claim','decision':'Human-reviewed evidence review only; automatic semantic assurance not established'}
    out=ROOT/'evidence/client_readiness';out.mkdir(parents=True,exist_ok=True)
    (out/('conservative_results.json' if conservative else 'challenge_results.json')).write_text(json.dumps({'summary':summary,'cases':rows},indent=2))
    print(json.dumps(summary,indent=2))
    return summary
if __name__=='__main__':
    run()
    run(conservative=True)
