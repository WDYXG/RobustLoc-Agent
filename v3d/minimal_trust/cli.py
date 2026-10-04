import argparse
from pathlib import Path
from v3b.assumption_agent.storage import read,save
from .agent import finite_decision,continuous_decision
from .analytic import analyze_case
from .freeze import ROOT


def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    output=Path(a.output)
    if output.exists(): raise RuntimeError('choose a new output path')
    data=read(Path(a.input)); obs=data['observation']; budget=data['budget']
    if data['mode']=='finite': result=finite_decision(obs,data['model'],budget)
    elif data['mode']=='continuous':
        cfg=read(ROOT/'v3c/trust_agent/config.json'); result=continuous_decision(obs,cfg,budget,node_limit=data.get('node_limit'))
    elif data['mode']=='analytic': result=analyze_case(obs,data['model'],data['completeness'],budget)
    else: raise ValueError('finite, continuous or checked analytic mode required')
    save(output,result); print(result['interval'])


if __name__=='__main__': main()
