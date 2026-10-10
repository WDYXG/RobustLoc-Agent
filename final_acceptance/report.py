"""Predeclared descriptive aggregation; no method or threshold optimization."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from . import study as s


def rows_from(cases):
    rows = []
    for case in cases:
        for policy, checkpoints in case['tracks'].items():
            for c in checkpoints:
                frontier = c['decisions']['certified']['frontier']
                for method, e in c['evaluations'].items():
                    rows.append(dict(episode_id=case['public']['episode_id'], scenario=case['private']['scenario'],
                        stratum='valid-premises' if case['private']['expected_valid'] else 'violation-stress',
                        policy=policy, k=c['k'], method=method, **e,
                        correct_output=e['output'] and not e['wrong'],
                        lower=float(s.F(frontier['rows'][case['public']['q_max']]['lower'])),
                        conservative_bound=float(s.F(frontier['worst_error_bound'])) if frontier['worst_error_bound'] else None,
                        optimizer_failure_count=len(c['decisions'][method].get('optimizer_failures', [])),
                        estimator_seconds=c['estimator_seconds'][method]))
    return rows


def summary(rows):
    n = len(rows)
    outputs = sum(r['output'] for r in rows)
    errors = [r['error'] for r in rows if r['output']]
    wrong = sum(r['wrong'] for r in rows)
    return dict(cases=n, outputs=outputs, coverage=outputs/n, abstentions=n-outputs,
                correct_outputs=sum(r['correct_output'] for r in rows),
                correct_output_fraction=sum(r['correct_output'] for r in rows)/n,
                wrong_outputs=wrong, wrong_output_fraction=wrong/n,
                selective_risk=wrong/outputs if outputs else None,
                output_error_median=float(np.median(errors)) if errors else None,
                output_error_p90=float(np.quantile(errors, .9)) if errors else None,
                severe_outputs=sum(r['severe'] for r in rows),
                bound_violations=sum(r['bound_violation'] for r in rows),
                actual_invalid_contracts=sum(not r['contract_valid'] for r in rows),
                total_cost=sum(r['cost'] for r in rows),
                optimizer_failure_count=sum(r['optimizer_failure_count'] for r in rows),
                estimator_seconds=sum(r['estimator_seconds'] for r in rows))


def aggregate(rows, cfg):
    groups = []
    for scope in ['valid-premises', 'violation-stress']+cfg['scenarios']:
        for policy in ('random', 'active'):
            for k in range(cfg['max_acquisitions']+1):
                for method in s.METHODS:
                    selected = [r for r in rows if (r['stratum'] == scope or r['scenario'] == scope)
                                and r['policy'] == policy and r['k'] == k and r['method'] == method]
                    groups.append(dict(scope=scope, policy=policy, k=k, method=method, **summary(selected)))
    return groups


def paired_intervals(rows, cfg):
    rng = np.random.default_rng(cfg['bootstrap_seed'])
    output = []
    for k in range(cfg['max_acquisitions']+1):
        differences = []
        for scenario in sorted(s.VALID):
            a = {r['episode_id']: r for r in rows if r['scenario'] == scenario and r['k'] == k
                 and r['method'] == 'certified' and r['policy'] == 'active'}
            b = {r['episode_id']: r for r in rows if r['scenario'] == scenario and r['k'] == k
                 and r['method'] == 'certified' and r['policy'] == 'random'}
            assert a.keys() == b.keys()
            differences.append(np.array([int(a[i]['correct_output'])-int(b[i]['correct_output']) for i in sorted(a)]))
        samples = np.zeros(cfg['bootstrap_samples'])
        for d in differences:
            samples += d[rng.integers(0, len(d), size=(cfg['bootstrap_samples'], len(d)))].mean(axis=1)/len(differences)
        low, high = np.quantile(samples, [.025, .975])
        output.append(dict(k=k, active_minus_random=float(np.mean(np.concatenate(differences))),
                           bootstrap95=[float(low), float(high)], positive_interval=bool(low > 0),
                           pairs=sum(map(len, differences)), scope='valid-premises; pointwise stratified paired descriptive interval'))
    return output


def write_csv(path, rows):
    with Path(path).open('x', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(folder):
    folder = Path(folder).resolve()
    cfg = s.read(folder/'manifest.json')['config']
    cases = [s.read(p) for p in sorted((folder/'cases').glob('*.json'))]
    rows = rows_from(cases)
    groups = aggregate(rows, cfg)
    paired = paired_intervals(rows, cfg)
    s.write(folder/'metrics.json', dict(groups=groups, paired_correct_output=paired,
        scope='Synthetic distance proxies; no BLE calibration; no teacher/industrial acceptance.',
        timing_note='Warm shared geometry caches and common k=0 reused; not a speed contest.'))
    write_csv(folder/'results.csv', rows)
    write_csv(folder/'summary.csv', groups)
    failures = [r for r in rows if not r['output'] or r['wrong'] or r['bound_violation'] or not r['contract_valid'] or r['optimizer_failure_count']]
    s.write(folder/'failures.json', failures)
    demo = next((c for c in cases if c['private']['expected_valid'] and
                 c['tracks']['active'][0]['decisions']['certified']['action'] == 'abstain' and
                 c['tracks']['active'][-1]['decisions']['certified']['action'] == 'recover'), cases[0])
    demo_lines = ['# 单个定位闭环示例', '',
        '事后按“有效契约、初始拒绝、主动采集后认证输出”选择首个案例；若无匹配则取首个案例。',
        '它仅用于解释流程，不能替代全部配对结果。真值仅由私有评估器在报告中揭示。', '',
        f'案例：`{demo["public"]["episode_id"]}`；场景：`{demo["private"]["scenario"]}`。', '',
        '| 策略 | 已新增 reporter | 决策 | 位置误差 m | 条件误差上界 m |', '|---|---:|---|---:|---:|']
    for policy, checkpoints in demo['tracks'].items():
        for c in checkpoints:
            d, e = c['decisions']['certified'], c['evaluations']['certified']
            err = f'{e["error"]:.4f}' if e['output'] else '未输出'
            bound = f'{float(s.F(d["error_bound"])):.4f}' if 'error_bound' in d else '未获认证'
            demo_lines.append(f'| {policy} | {c["k"]} | {d["action"]} | {err} | {bound} |')
    demo_lines += ['', f'完整输入、固定未来响应、动作评分与证书：[案例 JSON](cases/{demo["public"]["episode_id"]}.json)。']
    with (folder/'DEMO.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(demo_lines)+'\n')
    lines = ['# 原题闭环验收：众包离线定位', '',
        '**证据级别：numerically-supported。** 本次复用冻结证书与求解器，补充统一配对验收；不是新理论版本，也不是新的 Codex 研究策略竞赛。', '',
        f'执行 {len(cases)} 个新场景实例，每例 2 种采集顺序 × 4 个预算点 × 3 种输出方法。k=0 为共享初始数据，表内并非独立重复样本。', '',
        '题目来源按用户提供的 HarmonyOS 第七期描述记录；原始教师文件、数值指标和真实设备数据尚未独立核对。0.5 m 是本研究阈值，不是老师或华为的验收标准。', '',
        '## 相同预算下的有效契约结果', '',
        '| k | 采集 | 方法 | 输出/案例 | 错误输出 | 正确输出比例 | 输出 P90误差 m |',
        '|---:|---|---|---:|---:|---:|---:|']
    for g in groups:
        if g['scope'] != 'valid-premises' or (g['k'] == 0 and g['policy'] == 'random'):
            continue
        p90 = f'{g["output_error_p90"]:.4f}' if g['output_error_p90'] is not None else '未定义'
        lines.append(f'| {g["k"]} | {g["policy"]} | {g["method"]} | {g["outputs"]}/{g["cases"]} | {g["wrong_outputs"]} | {g["correct_output_fraction"]:.3f} | {p90} |')
    lines += ['', '正确输出比例=误差≤0.5 m 的输出数/全部案例；未输出不算正确。选择性风险以输出数为分母，完整数值见 summary.csv。WLS/Cauchy 的数值位置不带证书。', '',
        '## 主动 vs 随机：同样新增 k 个设备', '',
        '| k | 正确认证输出比例差（主动−随机） | 配对 bootstrap 95% 区间 |', '|---:|---:|---|']
    for p in paired:
        lines.append(f'| {p["k"]} | {p["active_minus_random"]:.3f} | [{p["bootstrap95"][0]:.3f}, {p["bootstrap95"][1]:.3f}] |')
    supported = [p['k'] for p in paired if p['positive_interval']]
    lines += ['', f'区间完全大于零的预算点：{supported}。这是分场景、保持配对的描述性区间，未校正多重比较；不代表真实设备总体优势。',
        '两者每个预算点实际都获取 k 条观测，早已可输出也继续采集；本实验不声称提前停止节约成本。当前主动策略是一步证书质量选择，不是全局最优规划器。', '',
        '## 假设失效压力测试（与主结果分开）', '',
        '| k=3 策略 | 方法 | 输出/案例 | 错误输出 | 违反报告界次数 |', '|---|---|---:|---:|---:|']
    for g in groups:
        if g['scope'] == 'violation-stress' and g['k'] == 3:
            lines.append(f'| {g["policy"]} | {g["method"]} | {g["outputs"]}/{g["cases"]} | {g["wrong_outputs"]} | {g["bound_violations"]} |')
    lines += ['', '证书验证数学条件，不验证物理条件是否真实。异常数超预算、噪声超界、位置误差超界和目标在域外时，条件保证不再适用；输出或报告界失效必须保留。', '',
        '## 验收范围与局限', '',
        '- 此处是静态二维、有限候选、距离代理合成实验。没有使用真实 BLE/RSSI、GNSS/WiFi 数据，没有实现 HarmonyOS 设备通信。',
        '- 正常噪声为有界异方差噪声；输入 Q、E、D、anchor balls 来自假定外部契约。未知 Q 不允许用预测值替代保证。',
        '- 三种方法使用相同已观测数据、位置域和固定起点；认证方法额外使用 Q 进行修剪和拒绝。不能把差异都归因于几何规划或 LLM。',
        '- certificate lower=0 仅表示当前方法未认证，不证明不可恢复；正界也是保守下界，不是真实信息裕度。',
        '- 求解器不完整；随机顺序只有每实例一次实现；各场景等权不是现场分布。零观察风险不等于零总体风险。',
        '- 时长保留在逐例文件；缓存共享和执行顺序影响耗时，因此不据此宣称速度优势。', '',
        '## 证据入口', '',
        '- [预注册协议](../../PROTOCOL.md)、[机器指标](metrics.json)、[逐输出结果](results.csv)、[场景汇总](summary.csv)。',
        '- [所有失败/拒绝/契约失效](failures.json)、[单个流程示例](DEMO.md)、cases/ 中的完整证书与动作日志。',
        '- audit.json 由独立重放命令生成；只有实际存在且 passed=true 才表示审计通过。',
        '- 原题工业验收仍 unresolved；本报告不能代替老师的数值验收标准或真实设备试验。']
    with (folder/'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), constrained_layout=True)
    for policy, marker in [('random', 'o'), ('active', 's')]:
        data = [g for g in groups if g['scope'] == 'valid-premises' and g['method'] == 'certified' and g['policy'] == policy]
        axes[0].plot([g['k'] for g in data], [g['correct_output_fraction'] for g in data], marker=marker, label=policy)
        data = [g for g in groups if g['scope'] == 'violation-stress' and g['method'] == 'certified' and g['policy'] == policy]
        axes[1].plot([g['k'] for g in data], [g['wrong_output_fraction'] for g in data], marker=marker, label=policy)
    for ax in axes:
        ax.set_xticks(range(4)); ax.set_xlabel('Additional reporters (equal cost)'); ax.set_ylim(-.02, 1.02); ax.legend(); ax.grid(alpha=.2)
    axes[0].set_title('Valid premises: correct certified outputs / all cases')
    axes[1].set_title('Violation stress: wrong certified outputs / all cases')
    fig.savefig(folder/'acceptance.png', dpi=160)
    plt.close(fig)
    print(json.dumps({'cases': len(cases), 'rows': len(rows), 'paired': paired}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('run'); a = p.parse_args(); run(a.run)
