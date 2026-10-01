"""Full conditional capacity diagnostic, separate from frozen simulation run.

Checks all integer q through the empty-survivor budget. It never estimates the
actual number of corrupted observations or authorizes the localization policy.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from robustloc.storage import save
from v3.freeze import check
from v3.certified_agent.certificates import profile

def capacity(obs):
    result=profile(obs,max_q=(len(obs['anchors'])+1)//2)
    tau=F(result['threshold'])
    possible=max((r['q'] for r in result['rows'] if F(r['upper'])>=tau),default=None)
    result.update(possible_capacity_upper=possible,
        capacity_determined=result['certified_capacity_lower']==possible,
        scope='full conditional profile bracket; a capacity lower bound is not actual corruption count',
        status='proved-in-project',novelty='not established')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args(); check()
    p=Path(args.input); obs=json.loads(p.read_text(encoding='utf-8'),parse_float=str)
    result=capacity(obs)
    result['provenance']=dict(input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='post-run diagnostic; does not rewrite the historical run or its decisions')
    save(args.output,result); print(json.dumps(result,indent=2)); check()
