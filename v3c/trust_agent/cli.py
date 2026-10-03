import argparse
from pathlib import Path
from v3b.assumption_agent.storage import read,save
from .policy import choose,trust_frontier

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); obs=read(a.input); cfg=read(Path(__file__).with_name('config.json'))
    save(a.output,dict(frontier=trust_frontier(obs),decision=choose(obs,'trust-directed',cfg,cfg['random_seed'])))
