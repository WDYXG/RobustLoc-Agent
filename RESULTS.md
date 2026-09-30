A persistent bounded research agent tested 8 hypotheses on synthetic crowd-localization observations. The frozen method is iteration-6. On 2000 held-out cases, weighted baseline CEP90 was 18.652 m and final CEP90 was 6.344 m (66.0% relative reduction). Failure rates were 25.700% and 5.250%. These are simulation observations, not a proof or an industrial claim.

| Scenario | WLS CEP90 | Final CEP90 | WLS failure | Final failure |
|---|---:|---:|---:|---:|
| clean | 0.246 | 0.283 | 0.000% | 0.000% |
| gaussian | 1.780 | 2.069 | 0.000% | 0.000% |
| heteroscedastic | 2.138 | 2.324 | 0.000% | 0.000% |
| outliers10 | 11.461 | 2.919 | 15.600% | 0.000% |
| outliers20 | 15.043 | 3.007 | 28.000% | 0.800% |
| outliers30 | 20.143 | 3.423 | 42.400% | 0.800% |
| poor_geometry | 26.618 | 11.214 | 54.800% | 13.600% |
| sparse | 33.168 | 23.671 | 64.800% | 26.800% |
