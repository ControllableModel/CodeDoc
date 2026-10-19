# Batch concurrency: measured scaling

Endpoint: gpt-6-luna (`https://apic1.ohmycdn.com/v1`), priced USD standard/short.
Every configuration documents the same sampled entities, so the work is identical.

A batch takes `ceil(entities / workers)` waves, so throughput is only comparable at a
similar wave count. The 8-entity run is included to show that artefact, not to rank
configurations: 4 workers looked worse than 8 only because 8 entities split into 2
waves and 1 wave.

| entities | workers | waves | wall (s) | failed | entities/min | s/entity | efficiency |
|---|---|---|---|---|---|---|---|
| 8 | 1 | 8 | 158.5 | 0 | 3.03 | 19.82 | 100% |
| 8 | 2 | 4 | 101.9 | 0 | 4.71 | 12.74 | 78% |
| 8 | 4 | 2 | 88.7 | 0 | 5.41 | 11.08 | 45% |
| 8 | 8 | 1 | 31.0 | 0 | 15.49 | 3.87 | 64% |
| 8 | 12 | 1 | 38.0 | 0 | 12.63 | 4.75 | 35% |
| 24 | 4 | 6 | 178.6 | 0 | 8.06 | 7.44 | 67% |
| 24 | 8 | 3 | 87.3 | 0 | 16.49 | 3.64 | 68% |
| 24 | 12 | 2 | 49.5 | 0 | 29.07 | 2.06 | 80% |
| 24 | 16 | 2 | 39.1 | 0 | 36.82 | 1.63 | 76% |
| 24 | 24 | 1 | 29.4 | 0 | 48.95 | 1.23 | 67% |
| 38 | 12 | 4 | 81.6 | 0 | 27.96 | 2.15 | 77% |
| 38 | 24 | 2 | 54.3 | 0 | 42.01 | 1.43 | 58% |
| 38 | 32 | 2 | 42.7 | 0 | 53.4 | 1.12 | 55% |

## Reading

* efficiency is `ideal / measured` where ideal = entities x 19.8 s / workers, and 19.8 s
  is the measured serial latency per entity;
* throughput improves monotonically with workers, but efficiency does not: 77-80% of
  ideal at 12 workers, 58-67% at 24 and 55% at 32. Two effects cause this: wave
  quantisation (only 2-3 waves at high worker counts) and contention above 12;
* the 8-entity rows are dominated by quantisation (1-8 waves) and should not be read as a
  scaling law at all;
* no configuration produced a single failure, so the proxy tolerated 32 concurrent
  generations and retries never had to rescue a batch;
* cost per entity is flat (USD 0.00068-0.00086) across concurrency, so concurrency buys
  latency only, not money.

## Practical choice

| repo | entities | 12 workers | 24 workers |
|---|---|---|---|
| ragflow | 38 | 1.4 min | 0.9 min |
| flask-main | 431 | 15.4 min | 10.3 min |
| fairseq | 5,229 | 3.1 h | 2.1 h |
| torch | 49,451 | 29.4 h | 19.6 h |

Default is 12: near-linear efficiency, and the whole validation suite finishes in
about a quarter of an hour. Raise to 24 for the large repos once the experiment
matrix is fixed, since throughput is still improving there.

## Caveat

Efficiency at 24 and 32 workers is measured with 2 wave boundaries only; the numbers
carry the same quantisation error the 8-entity run exposed. Treat 12 as solid and the
higher settings as roughly one-and-a-half to one-and-three-quarter times faster.
