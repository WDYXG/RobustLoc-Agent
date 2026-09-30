"""Protected evaluator v1.0; split policy is independent of the proposer."""
import time
import numpy as np
from .simulator import simulate
from .scenarios import SCENARIOS
from .metrics import summarize

VERSION = '1.0'
SPLIT_SEEDS = {'development': 110000, 'validation': 220000, 'heldout': 930000}

def case_seed(split, scenario_index, case_index):
    if not 0 <= case_index < 10000:
        raise ValueError('case index outside split allocation')
    return SPLIT_SEEDS[split] + scenario_index * 10000 + case_index

def evaluate(solver, split, count=100):
    rows = []
    for j, scenario in enumerate(SCENARIOS):
        for k in range(count):
            case = simulate(scenario, case_seed(split, j, k))
            started = time.perf_counter()
            try:
                result = solver(case.observation)
                error = float(np.linalg.norm(result.position - case.truth))
                if not np.isfinite(error):
                    error = float('inf')
                success, message = bool(result.success), result.message
                position = np.asarray(result.position).tolist()
            except Exception as exc:
                error, success, message, position = float('inf'), False, repr(exc), None
            rows.append(dict(scenario=scenario, seed=case.seed, error=error, success=success,
                             message=message, position=position, runtime_s=time.perf_counter()-started))
    return dict(evaluator_version=VERSION, split=split, count_per_scenario=count,
                overall=summarize(rows), by_scenario={s: summarize([r for r in rows if r['scenario']==s]) for s in SCENARIOS}, rows=rows)
