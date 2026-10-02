"""Observation-only frontier and first decision; performs no external request."""
import argparse
from pathlib import Path
from .storage import read,save
from .certificates import frontier
from .contracts import check_observation
from .policy import choose


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input',required=True); parser.add_argument('--output',required=True)
    parser.add_argument('--method',default='multi-step',choices=['measurement-only','random-information','one-step-gain','multi-step'])
    args=parser.parse_args(); obs=read(args.input); cfg=read(Path(__file__).with_name('config.json'))
    check_observation(obs); save(args.output,dict(frontier=frontier(obs),decision=choose(obs,args.method,cfg,cfg['random_policy_seed'])))
