"""One observation-only decision from a JSON input; does not acquire externally."""
import argparse
import json
from pathlib import Path
from robustloc.storage import read,save
from v3.freeze import check
from .policy import decide
from .verifier import residual_check,require
from v2.global_stability.verifier import verify_certificate
from fractions import Fraction as F

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True); parser.add_argument('--output',required=True)
    parser.add_argument('--model',help='Optional persisted learning.json; diagnostic only')
    args=parser.parse_args(); check()
    # Decimal JSON tokens retain their declared value, not a binary-float approximation.
    obs=json.loads(Path(args.input).read_text(encoding='utf-8'),parse_float=str)
    required={'anchors','measurements','weights','domain','epsilon','error_tolerance'}
    if required-set(obs): parser.error('Missing explicit input fields: '+','.join(sorted(required-set(obs))))
    obs.setdefault('q_budget',None); obs.setdefault('estimated_corruption',None)
    obs.setdefault('available_anchors',[]); obs.setdefault('acquisitions_remaining',0)
    obs.setdefault('random_choice_index',0)
    require(len(obs['anchors'])==len(obs['measurements'])==len(obs['weights']),'observation vector lengths')
    require(all(F(w)==1 for w in obs['weights']),'Phase 3A calibration requires fixed weights 1')
    cfg=read(Path(__file__).with_name('config.json'))
    model=read(args.model)['model'] if args.model else None
    decision=decide(obs,cfg,model=model)
    if decision['action']=='recover':
        result=verify_certificate(decision['geometry']['certificate']); b=F(result['certified_lower'])
        upper2,_=residual_check(obs,decision['candidate']['position'],obs['q_budget'])
        require(upper2<=F(obs['epsilon'])**2 and b>=2*F(obs['epsilon'])/F(obs['error_tolerance']),
                'independent recovery gate')
    save(args.output,decision); check()
    print(json.dumps(dict(action=decision['action'],reason=decision['reason'],
        error_bound=decision.get('error_bound'),conditional_profile=decision['conditional_profile']),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
