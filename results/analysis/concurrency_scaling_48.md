# Batch concurrency scaling

* endpoint: gpt-6-luna, priced in USD (standard / short context)
* each configuration runs the same sampled entity set, so the work is identical
* wall time is quantised by ceil(limit/workers) waves, so a coarse entity count shows
  a saw-tooth rather than a smooth curve; read s/entity together with the wave count

| workers | entities | waves | wall (s) | failed | entities/min | s/entity | cost/entity |
|---|---|---|---|---|---|---|---|
| 12 | 38 | 4 | 81.6 | 0 | 27.96 | 2.15 | $0.000694 |
| 24 | 38 | 2 | 54.3 | 0 | 42.01 | 1.43 | $0.000688 |
| 32 | 38 | 2 | 42.7 | 0 | 53.4 | 1.12 | $0.000684 |

* peak throughput: 53.4 entities/min at 32 workers
