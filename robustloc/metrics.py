"""Protected metric definitions. Nonfinite estimates count as infinite errors."""
import numpy as np
FAILURE_THRESHOLD = 10.0

def summarize(rows):
    errors = np.array([r['error'] for r in rows], float)
    return dict(n=len(rows), mean=float(np.mean(errors)), median=float(np.median(errors)),
                cep50=float(np.quantile(errors, .5)), cep90=float(np.quantile(errors, .9)),
                failure_rate=float(np.mean(errors > FAILURE_THRESHOLD)),
                runtime_mean_s=float(np.mean([r['runtime_s'] for r in rows])),
                optimization_failures=sum(not r['success'] for r in rows),
                nonfinite_cases=sum(not np.isfinite(r['error']) for r in rows))
