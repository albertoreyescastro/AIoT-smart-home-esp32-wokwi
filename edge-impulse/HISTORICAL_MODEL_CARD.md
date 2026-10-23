# Historical Edge Impulse Model Card

This file records the **historical experiment evidence** retained by the portfolio project. It is not a claim that the exact hosted Edge Impulse run can be reproduced byte-for-byte from this repository.

## Task

Five-class tabular environmental classification for the simulated Kitchen/Living Room module.

Inputs:

- `gas_score`
- `temperature`
- `humidity`

Classes:

- `NORMAL`
- `COOKING_FUMES`
- `GAS_DANGER`
- `HEAT_ANOMALY`
- `GAS_HEAT_EMERGENCY`

## Data provenance

The dataset is simulated and rule-labelled from demonstration gas/temperature boundaries. Humidity is retained as an input feature but does not determine the synthetic ground-truth label. Consequently, the metrics below are workflow evidence rather than independent real-world validation.

## Recorded training configuration

- Edge Impulse tabular/raw-feature workflow
- small dense neural-network classifier
- 3 numerical inputs
- 5 output classes
- 100 training cycles
- learning rate: `0.0005`
- historical deployment path: quantised int8 / EON Arduino export

## Recorded platform results

| Metric | Historical evidence |
|---|---:|
| Training accuracy | ~93.4% |
| Held-out test accuracy | ~85.9% |
| AUC | ~0.99 |
| Weighted precision | ~0.91 |
| Weighted recall | ~0.89 |
| Weighted F1 | ~0.89 |
| Estimated inference | ~1 ms |
| Estimated peak RAM | ~1.4 KB |
| Estimated flash | ~14.4 KB |

The original screenshots remain under `assets/`.

## Current public-runtime semantics

The checked-in Wokwi build keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`. It does not fabricate a model confidence or prediction. The deterministic environmental rules drive the public simulation, while the optional generated runtime can be enabled only by a reviewer who provides their own compatible Edge Impulse library and validates it on the intended target.
