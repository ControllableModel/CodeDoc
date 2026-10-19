# Batch concurrency scaling

* endpoint: gpt-6-luna, priced in USD (standard / short context)
* each configuration runs the same sampled entity set, so the work is identical

| workers | wall (s) | entities | failed | entities/min | s/entity | cost/entity |
|---|---|---|---|---|---|---|
| 1 | 158.5 | 8 | 0 | 3.03 | 19.82 | $0.000799 |
| 2 | 101.9 | 8 | 0 | 4.71 | 12.74 | $0.000863 |
| 4 | 88.7 | 8 | 0 | 5.41 | 11.08 | $0.000836 |
| 8 | 31.0 | 8 | 0 | 15.49 | 3.87 | $0.000776 |
| 12 | 38.0 | 8 | 0 | 12.63 | 4.75 | $0.000805 |

* peak throughput: 15.49 entities/min at 8 workers
* speed-up over serial: 5.1x
