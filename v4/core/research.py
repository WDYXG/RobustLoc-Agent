"""A deterministic research protocol; task order is declared by the human."""
from itertools import combinations
from .symmetry import discover
from .corruption import common_corrupted_transcript
from .certificate import recover,verify_recovery,support_union_check
from .decision import analyze
from .verify import verify_result
from .information_action import key
from .arithmetic import F
from .diagnostics import classify_pair


def search_ambiguity(problem,candidates,q):
    checked=0; inexact=0
    for x,z in combinations(candidates,2):
        if not problem.in_domain(x) or not problem.in_domain(z) or problem.equivalent(x,z): continue
        checked+=1; a=problem.observe(x); b=problem.observe(z)
        if any(F(lo)!=F(hi) for lo,hi in a+b): inexact+=1; continue
        witness=common_corrupted_transcript(a,b,q)
        if witness is not None:
            return dict(found=True,left=list(map(str,x)),right=list(map(str,z)),transcript=witness,checked=checked,
                skipped_inexact=inexact,scope='exact finite candidate search; failure to find is not injectivity')
    return dict(found=False,checked=checked,skipped_inexact=inexact,scope='search unresolved, not a theorem')


def research_cycle(problem,transcript,candidates,model,budget,external_upper=None):
    """Identical control flow across problem adapters, no problem-name branch."""
    symmetry=discover(problem)
    witness=search_ambiguity(problem,candidates,transcript['q'])
    if witness['found']: witness['diagnosis']=classify_pair(problem,witness['left'],witness['right'],transcript['q'])
    recovery=recover(problem,transcript,candidates)
    if recovery['action']=='recover': verify_recovery(problem,transcript,recovery)
    support=None
    if witness['found']:
        t=dict(values=witness['transcript']['values'],q=transcript['q'])
        support=support_union_check(problem,witness['left'],witness['right'],t)
    decision=analyze(problem,model,budget,external_upper)
    verification=verify_result(problem,model,decision,budget,external_upper)
    return dict(problem=problem.name,symmetry=symmetry,ambiguity=witness,support_union=support,
        recovery=recovery,decision=decision,verification=verification,
        stages=['symmetry','2q-support-union','robust-recovery-bound','ambiguity-witness','active-information-decision'],
        provenance='human-declared hypotheses and order; deterministic search, adapter algebra and hard consumers; no LLM proposer')


def execute_policy(model,decision,reply_provider):
    """Receives replies; has no actual-world identifier or target input."""
    if model['semantics']!='complete-finite-prior':
        return dict(action='abstain',reason='restriction-tree-is-not-a-continuous-policy')
    if decision['interval']['state']!='certifiably-recoverable':
        return dict(action='abstain',reason=decision['interval']['state'])
    node=decision['tree']
    if node is None: return dict(action='abstain',reason='no successful policy')
    history=[]; spent=F(0)
    while not node['terminal']:
        a=next(a for a in model['actions'] if a['id']==node['action']); reply=reply_provider(a)
        history.append(dict(action=a['id'],reply=reply,cost=a['cost'])); spent+=F(a['cost'])
        k=key(reply)
        if k not in node['children']: return dict(action='abstain',reason='reply-outside-declared-model',history=history,spent=str(spent))
        node=node['children'][k]
    return dict(action='recover',history=history,spent=str(spent),position=node['ball']['centre'],radius2=node['ball']['radius2'])
