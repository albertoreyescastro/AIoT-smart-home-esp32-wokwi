# Environmental Safety Dataset

This folder contains the synthetic environmental dataset used for the Kitchen/Living Room TinyML experiment.

## Inputs

- `gas_score`: simulated MQ2 gas score from 0 to 1000
- `temperature`: simulated DHT22 temperature in degrees Celsius
- `humidity`: simulated DHT22 relative humidity percentage

Target column:

- `label`: environmental safety class

Classes:

- `NORMAL`
- `COOKING_FUMES`
- `GAS_DANGER`
- `HEAT_ANOMALY`
- `GAS_HEAT_EMERGENCY`

## Label generation

The labels are **synthetic and deterministic**. They were generated from demonstration thresholds rather than independently observed real-world outcomes:

| Condition | Label |
|---|---|
| `gas_score >= 850` and `temperature >= 55°C` | `GAS_HEAT_EMERGENCY` |
| `gas_score >= 850` | `GAS_DANGER` |
| `temperature >= 55°C` | `HEAT_ANOMALY` |
| `gas_score >= 420` | `COOKING_FUMES` |
| otherwise | `NORMAL` |

These thresholds are not calibrated safety limits.

Because the target is derived from the same simulated input variables used for training, high classifier performance is expected and should **not** be interpreted as independent evidence of real-world predictive validity. In this experiment, humidity is an input feature but does not determine the synthetic ground-truth label.

The dataset is suitable for demonstrating the Edge Impulse/TinyML workflow and embedded integration path, not for validating a production safety model.

## Integrity check

From the repository root, run:

```bash
python scripts/validate_repo.py
```

The validator checks the schema, numeric ranges, expected classes and consistency between every row and the documented synthetic labelling rules.

For the broader evaluation caveats and reproduction procedure, see [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md).

The dataset contains no personal data, private credentials or real household monitoring records.
