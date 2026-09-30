"""Charts generated exclusively from saved experiment outputs."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .storage import read, history
from .simulator import simulate

def finish(run, name):
    path=run/'figures'; path.mkdir(exist_ok=True)
    plt.tight_layout(); plt.savefig(path/(name+'.png'),dpi=160); plt.close()

def compare(run, results, prefix):
    names=list(results); scenarios=list(results[names[0]]['by_scenario'])
    plt.figure(figsize=(8,4))
    for name,data in results.items():
        e=np.sort([r['error'] for r in data['rows']]); plt.plot(e,np.arange(1,len(e)+1)/len(e),label=name)
    plt.xlim(0,40); plt.xlabel('Localization error (m)'); plt.ylabel('Empirical CDF'); plt.legend(); plt.grid(alpha=.2)
    finish(run,prefix+'error_distribution')
    for metric,label in [('cep90','CEP90 (m)'),('failure_rate','Failure rate (>10 m)')]:
        plt.figure(figsize=(10,4)); x=np.arange(len(scenarios)); width=.8/len(names)
        for j,name in enumerate(names):
            plt.bar(x+j*width,[results[name]['by_scenario'][s][metric] for s in scenarios],width,label=name)
        plt.xticks(x+width*(len(names)-1)/2,scenarios,rotation=25,ha='right'); plt.ylabel(label); plt.legend()
        finish(run,prefix+metric+'_by_scenario')

def baseline_figures(run):
    compare(run,{m:read(run/f'baseline_validation_{m}.json') for m in ['unweighted','weighted']},'baseline_')

def iteration_figures(run):
    records=history(run/'research_log.jsonl')
    with (run/'iterations.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['iteration','mechanism','parent','verdict','cep90','failure_rate','best'])
        for r in records:
            m=r['metrics']['validation']['overall']; writer.writerow([r['iteration'],r['proposal']['mechanism'],r['proposal']['parent'],r['verdict'],m['cep90'],m['failure_rate'],r['best_method']['name']])
    for metric,label in [('cep90','Validation CEP90 (m)'),('failure_rate','Validation failure rate')]:
        incumbent=read(run/'baseline_validation_weighted.json')['overall'][metric]
        values=[incumbent]; candidates=[incumbent]
        for r in records:
            value=r['metrics']['validation']['overall'][metric]
            if r['verdict']=='supported': incumbent=value
            values.append(incumbent); candidates.append(value)
        plt.figure(figsize=(8,4)); plt.plot(range(len(values)),values,'o-',label='incumbent'); plt.plot(range(len(values)),candidates,'x--',label='candidate')
        plt.xlabel('Research iteration'); plt.ylabel(label); plt.legend(); plt.grid(alpha=.2); finish(run,'iteration_'+metric)

def final_figures(run):
    results={m:read(run/f'heldout_{m}.json') for m in ['unweighted','weighted','final']}
    compare(run,results,'final_')
    plt.figure(figsize=(7,4))
    for m,data in results.items():
        plt.plot([0,.1,.2,.3],[data['by_scenario'][s]['cep90'] for s in ['heteroscedastic','outliers10','outliers20','outliers30']],'o-',label=m)
    plt.xlabel('Nominal outlier fraction (actual counts rounded at n=16)'); plt.ylabel('Held-out CEP90 (m)'); plt.legend(); finish(run,'outlier_ratio')
    final=results['final']['rows']; base=results['weighted']['rows']
    worst=max(range(len(final)),key=lambda i:final[i]['error'])
    typical=min(range(len(final)),key=lambda i:abs(final[i]['error']-results['final']['overall']['median']))
    for label,i in [('typical_case',typical),('failure_case',worst)]:
        row=final[i]; case=simulate(row['scenario'],row['seed']); obs=case.observation
        plt.figure(figsize=(7,6))
        plt.scatter(obs.positions[:,0],obs.positions[:,1],c=np.where(case.outlier_mask,'tomato','steelblue'),label='reporters (red = corrupted, analysis only)')
        plt.scatter(*case.truth,marker='*',s=180,c='black',label='truth')
        for name,pos in [('weighted',base[i]['position']),('final',row['position'])]:
            if pos is not None: plt.scatter(*pos,marker='x',s=90,label=name)
        plt.axis('equal'); plt.xlabel('x (m)'); plt.ylabel('y (m)'); plt.title(f'{label}: {row["scenario"]}, seed {row["seed"]}, final error {row["error"]:.2f} m'); plt.legend(fontsize=8)
        finish(run,label)
