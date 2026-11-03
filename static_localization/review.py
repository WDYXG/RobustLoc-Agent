"""Recompute metrics/errors, replay stratified solvers, and produce a bounded report."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from robustloc.verifier import verify
from .study import save, hashes, frozen_history, metrics, one, POLICY
from .service import INCUMBENT
from .simulation import generate, specifications


def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def audit(run, output):
    out=Path(output)
    if out.exists(): raise FileExistsError(out)
    manifest=load(run/'manifest.json')
    assert hashes()==manifest['source_sha256']
    selected=load(run/'selected-method.json'); assert selected['source_sha256']==hashes()
    recorded_inputs=[]
    with gzip.open(run/'observations.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line); assert generate(row['specification'])[0]==row['data']; recorded_inputs.append(row['specification'])
    assert recorded_inputs==list(specifications('test'))
    with gzip.open(run/'evaluation-private.jsonl.gz','rt') as f:
        private_rows=[json.loads(line) for line in f]
    assert len(private_rows)==len(recorded_inputs)
    for row,spec in zip(private_rows,recorded_inputs):
        assert row['specification']==spec and generate(spec)[1]==row['data']
    baseline=load(run/'validation-baseline.json'); incumbent=load(run/'validation-incumbent.json')
    best=dict(name='frozen-cauchy',config=INCUMBENT)
    for folder in sorted(run.glob('iteration-*')):
        candidate=load(folder/'validation.json'); verdict=verify(candidate,incumbent,baseline,POLICY)
        assert verdict==load(folder/'verdict.json')
        if verdict['verdict']=='supported':
            best=dict(name='proposal-'+str(int(folder.name.split('-')[-1])),config=load(folder/'proposal.json')['config'])
            incumbent=candidate
    assert selected['config']==best['config'] and selected['name']==best['name']
    specs=recorded_inputs
    jobs=[]; expected=[]
    completion=load(run/'completion.json')
    for method,cfg in [('unweighted-ls',None),('weighted-ls',None),('frozen-cauchy',INCUMBENT),('final',selected['config'])]:
        path=run/f'test-{method}.json'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==completion['final_sha256'][path.name]
        result=load(path); assert len(result['rows'])==len(specs)
        assert metrics(result['rows'])==result['overall']
        for row,spec,pr in zip(result['rows'],specs,private_rows):
            assert all(row[k]==v for k,v in spec.items())
            assert abs(np.linalg.norm(np.array(row['estimate'])-pr['data']['truth'])-row['error'])<1e-10
            if spec['seed']%1000==0:
                jobs.append((spec,method,cfg)); expected.append(row)
    with ProcessPoolExecutor(max_workers=4) as pool:
        for row,old in zip(pool.map(one,jobs,chunksize=16),expected):
            assert np.allclose(row['estimate'],old['estimate'],atol=1e-8,rtol=0)
            assert row['optimizer_success']==old['optimizer_success']
    save(out,dict(passed=True,historical_files_unchanged=frozen_history(),
         source_hashes_match=True,all_observations_and_private_labels_regenerated=True,
         all_final_error_values_recomputed=True,verifier_decisions_replayed=True,
         stratified_solver_replays=len(jobs),full_solver_replay=False))


def report(run, reliability, real, output):
    out=Path(output)
    if out.exists(): raise FileExistsError(out)
    selected=load(run/'selected-method.json'); trace=load(run/'research-trace.json')
    lines=['# 静态定位实际结果','',
      '结论范围：本轮是米制合成实验与公开真实数据适用性审查。原题静态目标已核对；没有获得原题验证数据，不宣称 HarmonyOS 实测达标。',
      '',f'最终配置由验证集选择：`{selected["name"]}`，`{json.dumps(selected["config"])}`。最终测试前已冻结。',
      '', '## n>10 的主要结果','',
      '以下覆盖所有数值输出，包括未获可靠性证书的估计；失败指误差>30米。不同生成模型分开汇总。',
      '', '|模型|方法|样本数|CEP90 米|失败率|优化未成功|', '|---|---|---:|---:|---:|---:|']
    for model in ('distance-proxy','synthetic-rssi'):
        for method in ('unweighted-ls','weighted-ls','frozen-cauchy','final'):
            rows=load(run/f'test-{method}.json')['rows']; rs=[r for r in rows if r['n']>10 and r['model']==model]
            m=metrics(rs)
            lines.append(f'|{model}|{method}|{len(rs)}|{m["cep90"]:.2f}|{m["failure_rate"]:.1%}|{m["optimization_failures"]}|')
    rows=load(run/'test-final.json')['rows']
    lines+=['','## 最终方案按场景分组','',
      '下表每行汇总 n=11/16/32；完整 n×几何×噪声×异常比例表见 `study/strata.csv`。不能用总平均代替特定场景达标。',
      '', '|场景|案例|CEP90 米|30米点估计达标|失败率|','|---|---:|---:|---|---:|']
    for s in sorted({r['scenario'] for r in rows}):
        m=metrics([r for r in rows if r['n']>10 and r['scenario']==s])
        lines.append(f'|{s}|{m["cases"]}|{m["cep90"]:.2f}|{"是" if m["meets_30m_point_estimate"] else "否"}|{m["failure_rate"]:.1%}|')
    strata=[r for r in load(run/'strata.json') if r['method']=='final' and r['n']>10]
    lines+=['',f'n>10 共 {len(strata)} 个最终单元，其中 {sum(r["meets_30m_point_estimate"] for r in strata)} 个 CEP90 点估计≤30米。每单元40例，尾部估计不精确；区间保存在 strata.json/csv，不作真实环境保证。',
      '', '## Agent 实际做了什么','']
    for r in trace:
        if r.get('historical_skip'): continue
        p,v=r['proposal'],r['result']
        lines.append(f'- {p["mechanism"]}：{v["verdict"]}；验证 CEP90 相对改善 {v["relative_cep90_gain"]:.2%}，场景退化数 {len(v["scenario_regressions"])}。保存了 proposal、开发/验证误差和独立 verifier 裁决。')
    lines+=['','这是既有规则型研究 Agent 的三轮迁移检查；运行时是数值求解器和条件决策模块。本轮没有新的 Codex 自主研究调用，不能把有限策略列表说成开放式发现。',
      '', '## 可靠性与实际信息获取','',
      '主实验的 Gaussian 不确定性没有硬上界，所有最终估计均未冒充 certified 输出：证书覆盖率为0，可靠性出口拒绝输出；数值位置仍保留并全部评价。这是系统限制，不计作精度成功。',
      '', '|独立受控契约组|案例|获得条件认证|误差>30米的认证输出|', '|---|---:|---:|---:|']
    rr=load(reliability/'rows.json')
    for regime in sorted({r['regime'] for r in rr}):
        rs=[r for r in rr if r['regime']==regime]
        lines.append(f'|{regime}|{len(rs)}|{sum(r["certified"] for r in rs)}|{sum(r["false_output"] for r in rs)}|')
    acq=load(reliability/'acquisition.json')
    for s in acq['steps']:
        a=s['answer']; rel=a['reliability']; f=rel.get('frontier',rel.get('decision',{}).get('frontier',{}))
        margin=f['rows'][-1]['lower'] if f else None
        lines.append(f'- 信息获取 step {s["step"]}：n={a["n_reporters"]}，{a["decision"]}，q=1 几何下界={float(__import__("fractions").Fraction(margin)) if margin else None}，评价误差={s["evaluation_error"]:.3f}米。')
    lines+=['','该轨迹真的调用了仿真信息提供端并重新认证；未执行现实设备扫描。该有限例子不证明主动选择一般优于随机。失配组展示共同坐标偏差会使错误的外部契约产生错误安全感，几何内核不能自行鉴别。',
      '', '## 真实数据与尚未解决问题','',
      'UCI 原始 BLE 数据已下载：1,420 条标签记录只有1–5个可见信标，0条满足 n>10；地图米制比例未验证。未用重复包凑人数，未伪造米制定位准确率。详见 real-data/audit.json 和 data/SOURCES.md。',
      '', '仍需：原题指定的米制真实验证集、设备间 RSSI 校准、可信 reporter 误差/异常数量上界、复杂几何下稳定解算与证书计算规模控制。当前 API 接收局部米制坐标，没有完成 GNSS 地理坐标投影、移动检测或设备端部署。',
      '', '## 失败场景与证据边界','',
      '近共线/单侧几何、较大正常定位误差、异常污染和 RSSI 传播系数失配均在预先固定网格中保留。观察到的关联不等于分离出的因果机制。下面列出最终误差最大的5例，完整记录包含所有成功与失败。','']
    for r in sorted(rows,key=lambda r:r['error'],reverse=True)[:5]:
        lines.append(f'- seed={r["seed"]}，n={r["n"]}，{r["scenario"]}：误差{r["error"]:.2f}米，优化成功标志={r["optimizer_success"]}。')
    lines+=['','本轮新增结论均为 **numerically-supported**；沿用的已证明界见 v2/v3b 原账本。没有新增原创定理，没有把有限仿真当作真实 BLE 性能证明。','']
    out.write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('run',type=Path); p.add_argument('--audit',required=True)
    p.add_argument('--reliability',type=Path,required=True); p.add_argument('--real',type=Path,required=True); p.add_argument('--report',required=True)
    a=p.parse_args(); audit(a.run,a.audit); report(a.run,a.reliability,a.real,a.report)
