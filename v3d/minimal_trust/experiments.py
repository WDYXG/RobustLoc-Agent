"""Predeclared development regression and held-out synthetic inputs."""
from fractions import Fraction as F
from v3c.trust_agent.simulator import make


def continuous_case(kind,index,seed,cfg):
    obs,private=make('bounded-references',index,cfg,seed)
    budget='18/5'; limit=None
    if kind in ('positive-gap','insufficient-budget','search-limited'):
        for a in obs['hard_refs']: a['radius']='1/5'
        obs['tolerance']='1/20'; budget='2'
    if kind=='insufficient-budget': budget='1/2'
    if kind=='search-limited': limit=1
    if kind=='family-limited': obs['epsilon']='1/10'; obs['tolerance']='1/100'; budget='2'
    obs['episode_id']=kind+'-'+str(index); obs['budget']=budget
    return obs,private,budget,limit
