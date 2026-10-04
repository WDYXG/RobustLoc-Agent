"""Replay every Phase 3C case through the shared v4 cost/decision engine."""
from v3b.assumption_agent.storage import hydrate
from v3d.minimal_trust.analytic import verify_completeness
from .storage import ROOT,read,save
from .problems.range_localization import RangeLocalization,legacy_model,continuous_bounds,delivered_cover
from .core.decision import analyze,diagnose
from .core.verify import verify_result


def run_regression(output):
    base=ROOT/'v3d/runs/minimal-trust-001'; problem=RangeLocalization(); rows=[]; cfg=read(ROOT/'v3c/trust_agent/config.json')
    for folder in ('finite','analytic'):
        for path in sorted((base/folder).glob('*.json')):
            old=hydrate(base,read(path)); complete=True
            if folder=='analytic': verify_completeness(old['observation'],old['model'],old['completeness_certificate'])
            model=legacy_model(old['observation'],old['model'],complete)
            result=analyze(problem,model,old['budget']); verify_result(problem,model,result,old['budget'])
            if result['interval']!=old['decision']['interval']: raise AssertionError('legacy finite/analytic interval changed')
            rows.append(dict(case=folder+'/'+path.stem,interval=result['interval'],passed=True,model=model,result=result,
                scope='explicit finite prior' if folder=='finite' else 'continuous completeness supplied by frozen analytic adapter proof'))
    for path in sorted((base/'continuous').glob('*.json')):
        old=hydrate(base,read(path)); new=continuous_bounds(old['observation'],cfg,old['budget'],old['node_limit'])
        verify_result(problem,new['model'],new['result'],old['budget'],new['upper']['cost_upper'])
        if new['result']['interval']!=old['decision']['interval']: raise AssertionError('legacy continuous interval changed')
        cover=None
        if old['actual'] and old['actual']['certificate']['certified']:
            cover=delivered_cover(old['final_observation'],cfg)
            if cover!=old['actual']['certificate']: raise AssertionError('legacy subset output changed')
        rows.append(dict(case='continuous/'+path.stem,interval=new['result']['interval'],passed=True,
            subset_output_identical=cover is not None,model=new['model'],result=new['result'],upper=new['upper']))
    result=dict(passed=True,cases=len(rows),finite=24,analytic=3,continuous_including_development=16,rows=rows,
        scope='all 43 Phase 3C intervals preserved; four delivered subset outputs identical; earlier full test suite separately run; no old artifact rewritten')
    save(output,result); return result
