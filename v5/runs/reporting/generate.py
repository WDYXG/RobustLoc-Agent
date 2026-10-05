"""Descriptive plots/cost tables from immutable records; no scoring changes."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Patch
from v5.researcher.io import ROOT,read


def generate():
    runs=ROOT/'v5/runs';out=runs/'figures';out.mkdir(exist_ok=True)
    pairs=[('Scripted',runs/'paired-v2-scripted-001/scientific'),('Codex',runs/'paired-v2-codex-001/scientific')]
    colors={'proved-in-project':'#297c67','refuted':'#b5464a','numerically-supported':'#527ca5',
            'unresolved':'#ce973b','provider-failure':'#747982'}
    fig,ax=plt.subplots(figsize=(13,4.3))
    for y,(label,path) in enumerate(pairs):
        for i,e in enumerate(read(path/'ledger.json')):
            status='provider-failure' if e['failure_kind']=='provider-failure' else e['status']
            ax.add_patch(Rectangle((i+.06,y+.12),.88,.70,facecolor=colors[status],edgecolor='white'))
            text={'proved-in-project':'P','refuted':'R','numerically-supported':'N','unresolved':'U','provider-failure':'I'}[status]
            ax.text(i+.5,y+.47,text,ha='center',va='center',color='white',weight='bold',fontsize=14)
    ax.set_xlim(0,12);ax.set_ylim(2.05,-.05);ax.set_xticks([i+.5 for i in range(12)],labels=[f'{i+1:02d}' for i in range(12)])
    ax.set_yticks([.47,1.47],labels=['Scripted','Codex']);ax.tick_params(length=0,labelsize=11)
    for s in ax.spines.values():s.set_visible(False)
    ax.set_xlabel('Planned research slot (one formal claim per completed proposal)',labelpad=13)
    fig.suptitle('Verifier-governed research: different trajectories, ledger progress tied 8–8',fontsize=15,x=.51,y=.97)
    legend=[Patch(color=colors[k],label=t) for k,t in [('proved-in-project','P: exact proof'),('refuted','R: exact counterexample'),
                ('numerically-supported','N: bounded support'),('unresolved','U: unresolved / rejected certificate'),('provider-failure','I: interrupted')]]
    fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.5,.10),ncol=3,frameon=False,fontsize=9)
    fig.text(.5,.035,'12 slots per policy; 11 captured Codex completions. Acceptance is not literature novelty or proof of policy superiority.',ha='center',fontsize=9,color='#555555')
    fig.subplots_adjust(left=.09,right=.98,top=.81,bottom=.33)
    fig.savefig(out/'phase5_trajectory.png',dpi=180);fig.savefig(out/'phase5_trajectory.svg');plt.close(fig)
    with (runs/'trajectory.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['policy','round','parent','family','status','ledger_advancing','claim_unverified_prose'])
        for label,path in pairs:
            for e in read(path/'ledger.json'):
                writer.writerow([label,e['id'],e['parent_id'],e['family'],e['status'],e['ledger_advancing'],e['proposal_claim_unverified']])
    with (runs/'provider_costs.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['cohort','round','completed_receipts','input_tokens_observed','output_tokens_observed',
                                             'wall_seconds_observed','cost_capture_incomplete'])
        for name,path in [('aborted-pilot',runs/'codex-001'),('primary',pairs[1][1])]:
            for p in sorted((path/'iterations').glob('r*')):
                r=read(p/'runtime.json') if (p/'runtime.json').exists() else None
                usage=r.get('usage',[]) if r else []
                writer.writerow([name,p.name,len(usage),sum(u.get('input_tokens',0) for u in usage) if usage else '',
                    sum(u.get('output_tokens',0) for u in usage) if usage else '',
                    r['wall_seconds'] if r and not r.get('wall_seconds_is_lower_bound') else '',not bool(usage)])


if __name__=='__main__':generate()
