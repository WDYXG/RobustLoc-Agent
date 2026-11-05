"""CLI for the frozen stage's observation-only final model bundle."""
import argparse,json
from pathlib import Path
import numpy as np
from .core import estimate
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('bundle');p.add_argument('observation');p.add_argument('output');a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise FileExistsError(out)
    b=json.loads(Path(a.bundle).read_text());obs=json.loads(Path(a.observation).read_text())
    result=estimate(obs,np.array(b['anchors']),b['model'],b['method'])
    result.update(reliability='uncertified empirical estimate',decision='estimate' if result['position'] is not None else 'abstain')
    out.write_text(json.dumps(result,indent=2)+'\n')
