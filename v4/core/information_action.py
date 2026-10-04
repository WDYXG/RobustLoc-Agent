"""Positive-cost deterministic reply partitions, shared by both adapters."""
import json


def key(value): return json.dumps(value,sort_keys=True,separators=(',',':'))


def partitions(model,indices,action):
    groups={}
    for i in indices:
        r=key(action['responses'][model['worlds'][i]['id']])
        groups.setdefault(r,[]).append(i)
    return groups
