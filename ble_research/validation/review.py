"""Independent arithmetic/gate replay and held-out performance report."""
import argparse,hashlib,json,sys,platform
from pathlib import Path
import numpy as np
import scipy
from ble_research.core import read,estimate,predict,aggregate,fit
from ble_research.runner import load,save,summary,sources

def bootstrap(rows):
    labels=sorted({r['label'] for r in rows});rng=np.random.default_rng(7401);vals=[]
    for _ in range(500):
        sample=rng.choice(labels,len(labels),replace=True);rs=[]
        for i,label in enumerate(sample):
            rs.extend([dict(r,label=str(i)) for r in rows if r['label']==label])
        m=summary(rs)
        if m['cep90'] is not None:vals.append([m['cep90'],m['coverage'],m['failure_rate']])
    return dict(cep90_95=np.quantile(vals,[.025,.975],axis=0)[:,0].tolist(),
                coverage_95=np.quantile(vals,[.025,.975],axis=0)[:,1].tolist(),
                failure_rate_95=np.quantile(vals,[.025,.975],axis=0)[:,2].tolist(),unit='resampled physical locations, 500 draws')

def review(out):
    dest=out/'review';dest.mkdir(exist_ok=False);p,g,s=read();lock=load(out/'FINAL_LOCK.json')
    assert sources()==lock['sources'] and g==load(out/'split.json')
    freeze=load(Path('ble_research/PREVIOUS_FREEZE.json'))
    assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in freeze['sha256'].items())
    # Gate implementation here does not call the research runner's gate.
    incumbent=load(out/'validation-global-cauchy.json');accepted=[]
    for folder in sorted(out.glob('r[1-6]-*')):
        candidate=load(folder/'validation.json');c,b=candidate['overall'],incumbent['overall']
        expected=(b['cep90']-c['cep90'])/b['cep90']>=.01 and c['coverage']>=b['coverage']-1e-12
        assert expected==load(folder/'verdict.json')['accepted']
        if expected:incumbent=candidate;accepted.append(folder.name)
    assert lock['selected']['name']==(accepted[-1] if accepted else 'global-cauchy')
    training={tuple(r['truth']) for r in s['calibration']}
    for path in out.glob('r*/model.json'):
        m=load(path)
        if 'field' in m:assert all(tuple(x) in training for x in m['field']['positions'])
    results={};replays=0
    models={'centre':(load(out/'model-global.json'),'centre'),'fixed-wls':(__import__('ble_research.core',fromlist=['FIXED']).FIXED,'wls'),
       'fixed-cauchy':(__import__('ble_research.core',fromlist=['FIXED']).FIXED,'cauchy'),
       'global-wls':(load(out/'model-global.json'),'wls'),'global-cauchy':(load(out/'model-global.json'),'cauchy'),
       'final':(load(out/lock['selected']['model']),lock['selected']['method'])}
    for name,(model,method) in models.items():
        result=load(out/f'test-{name}.json');assert summary(result['rows'])==result['overall']
        first=set()
        for row,r in zip(result['rows'],s['test']):
            assert row['key']==r['key'] and row['label']==r['label']
            error=float(np.linalg.norm(np.array(row['position'])-r['truth'])) if row['position'] is not None else None
            assert error==row['error']
            if r['label'] not in first:
                a=estimate(r['public'],p,model,method);first.add(r['label']);replays+=1
                assert a['success']==row['success'] and a['position']==row['position']
        results[name]=dict(**result['overall'],intervals=bootstrap(result['rows']),n_ge_11=result['n_ge_11'])
    save(dest/'metrics.json',results)
    residuals={}
    for name,model in [('fixed',models['fixed-wls'][0]),('global',models['global-wls'][0]),('receiver',load(out/'r1-receiver/model.json')),
                        ('device',load(out/'r3-device/model.json')),('dual',load(out/'r4-dual/model.json'))]:
        residuals[name]={}
        for split in ('calibration','validation','test'):
            es=[];dist_errors=[]
            for r in aggregate(s[split]):
                rss=np.array(r['public']['rssi']);mask=rss!=-105
                es.extend((predict(np.array(r['truth']),p,r['public']['device'],model)[mask]-rss[mask]).tolist())
                if not model.get('hinge',0):
                    a=np.array(model['intercepts'])+model['device_offsets'].get(r['public']['device'],0)
                    d=10**((rss[mask]-a[mask])/model['slope'])
                    dist_errors.extend((d-np.linalg.norm(p[mask]-r['truth'],axis=1)).tolist())
            residuals[name][split]=dict(rssi_rmse=float(np.sqrt(np.mean(np.square(es)))),
                range_mae=float(np.mean(np.abs(dist_errors))) if dist_errors else None)
    save(dest/'calibration-errors.json',residuals)
    worst=sorted(load(out/'test-final.json')['rows'],key=lambda r:r['error'] if r['error'] is not None else -1,reverse=True)[:20]
    save(dest/'worst-output-cases.json',worst)
    save(dest/'audit.json',dict(passed=True,historical_files_unchanged=freeze['count'],final_sources_unchanged=True,
         all_final_errors_recomputed=True,independent_gate_replays=6,stratified_solver_replays=replays,
         field_labels_calibration_only=True,environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform()),
         heldout_locations=32,conditional_metric_warning='CEP90 only among outputs; failure rate counts no output as failure',
         novelty='All methods are established modeling primitives; new project integration does not prove originality'))
    lines=['# 真实 BLE 静态研究：最终报告','',
       '本阶段完成2024真实数据校准、六轮反馈迭代和一次独立位置测试。结论局限于同一场地、同型号设备和固定接收锚点，不能作为HarmonyOS众包原题的全面达标证明。','',
       f'校准/验证/测试位置数96/32/32，行数分别为{len(s["calibration"])}/{len(s["validation"])}/{len(s["test"])}。同一位置所有设备与重复记录只进入一个分区。',
       '',f'冻结最终选择：{lock["selected"]["name"]}，方法{lock["selected"]["method"]}。','',
       '|方法|输出条件CEP50 m|输出条件CEP90 m|输出覆盖率|全体>30米或无输出失败率|','|---|---:|---:|---:|---:|']
    for name,m in results.items():lines.append(f'|{name}|{m["cep50"]:.3f}|{m["cep90"]:.3f}|{m["coverage"]:.1%}|{m["failure_rate"]:.1%}|')
    lines+=['','以上分位数按位置等权，条件于实际输出；没有把拒绝当零误差。所有位置的5/10/30米成功率、位置聚类95%区间和n≥11子集见metrics.json。少于3接收点保留为无输出。中心基线有位置先验优势，其意义是检查小场地30米指标是否足够区分算法。','',
       '## 真实研究迭代','', '|候选|验证CEP90 m|相对前任改善|gate|','|---|---:|---:|---|']
    for folder in sorted(out.glob('r[1-6]-*')):
        m=load(folder/'validation.json')['overall'];v=load(folder/'verdict.json')
        lines.append(f'|{folder.name}|{m["cep90"]:.3f}|{v["relative_gain"]:.2%}|{"accepted" if v["accepted"] else "rejected"}|')
    lines+=['','研究由当前Codex会话根据验证反馈逐轮提出与修正，proposal-*.json在各轮运行前保存。没有把预先写好的全自动任务列表冒充开放式Agent，也没有新增API模型调用。gate审计独立重算，但不是形式证明。大幅收益首先来自真实校准；额外机制的收益是否超过门槛由实际记录决定。','',
       '## 数学边界与失败解释','',
       'known：若RSSI=A+b log10 d+ε且ε服从N(0,σ²)，直接反演距离的条件均值偏差因子为exp((ln(10)σ/b)²/2)。这解释了误差模型差异，但不证明dB损失必然改善定位；本轮实际检验该猜想。参数拟合及核平滑是已有方法，不宣称新理论。',
       '', '所有性能改善仅为numerically-supported。被拒绝候选只在本次验证准则下不获支持，不能从32个验证位置推出普遍反例。3D高度、墙体、人体遮挡、检测选择偏差和未知设备仍是未解决因素。',
       '', '## 原题结论','',
       '必须同时审视CEP90和覆盖率。即使输出条件CEP90低于30米，也不代表全部案例90%恢复成功。公开锚点中心不读RSSI也可能低于30米，说明小场地阈值宽松。',
       '', 'n≥11仅在原数据8个位置有25行，测试分区实际子集见metrics.json，不把其他位置的结果冒充n>10验证。新21网关公开路径已追踪，但匿名API返回401，未取得可审查原始文件；不得伪造补充测试。详见../../SUPPLEMENTARY_DATA.md。',
       '', '值得继续改进的主线：先提升有效观测覆盖和跨环境校准，而不是继续用相同测试集调损失。重新采集/取得独立21网关数据后应建立新验证与测试划分；当前最终集不再用于候选选择。完整保留失败案例与拒绝proposal。','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();review(a.run)
