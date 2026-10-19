# Batch concurrency scaling

* endpoint: gpt-6-luna, priced in USD (standard / short context)
* each configuration runs the same sampled entity set, so the work is identical
* wall time is quantised by ceil(limit/workers) waves, so a coarse entity count shows
  a saw-tooth rather than a smooth curve; read s/entity together with the wave count

| workers | entities | waves | wall (s) | failed | entities/min | s/entity | cost/entity |
|---|---|---|---|---|---|---|---|
| 4 | 24 | 6 | 178.6 | 0 | 8.06 | 7.44 | $0.000791 |
| 8 | 24 | 3 | 87.3 | 0 | 16.49 | 3.64 | $0.00068 |
| 12 | 24 | 2 | 49.5 | 0 | 29.07 | 2.06 | $0.000703 |

* peak throughput: 29.07 entities/min at 12 workers
