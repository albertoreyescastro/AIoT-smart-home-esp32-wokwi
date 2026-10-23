# Reproducibility and Evaluation Notes

This document defines what the hardened public AIoT repository does and does not reproduce.

## Public runtime defaults

The repository is a **simulation-based portfolio prototype**. Both sketches keep cloud connectivity disabled by default:

```cpp
#define ENABLE_BLYNK 0
```

The Kitchen/Living Room sketch also keeps the generated Edge Impulse runtime disabled by default:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

That default is intentional. A public clone should run its local Wokwi logic without requiring private Blynk credentials or a generated third-party ML package.

When the Edge Impulse runtime is disabled, the kitchen/living-room environmental state is **rule-derived**. The code reports ML confidence as `N/A` and the raw ML prediction as `DISABLED`; it does not fabricate a model prediction or confidence value.

## Dataset provenance

`data/environmental_training_dataset.csv` contains simulated sensor values:

- `gas_score` - simulated MQ2 score, 0-1000
- `temperature` - simulated DHT22 temperature in degrees Celsius
- `humidity` - simulated DHT22 relative humidity in percent

The labels are synthetic and deterministic:

| Condition | Label |
|---|---|
| `gas_score >= 850` and `temperature >= 55 C` | `GAS_HEAT_EMERGENCY` |
| `gas_score >= 850` | `GAS_DANGER` |
| `temperature >= 55 C` | `HEAT_ANOMALY` |
| `gas_score >= 420` | `COOKING_FUMES` |
| otherwise | `NORMAL` |

These are project-specific demonstration boundaries, not calibrated safety limits. Humidity is an input feature but does not determine the synthetic ground-truth label.

Because the labels are derived from the same simulated inputs used for training, strong classifier performance is expected. The historical Edge Impulse run demonstrates the TinyML workflow; it does **not** establish independent real-world predictive validity or superiority over the rules.

## What is reproducible from this repository

A reviewer can reproduce or inspect:

1. Both Wokwi ESP32-S3 room simulations.
2. The deterministic room-control and safety logic.
3. The complete synthetic dataset and its labelling contract.
4. Repository validation with `python scripts/validate_repo.py`.
5. Design-level scenario contracts with `python scripts/test_scenarios.py`.
6. Both ESP32-S3 builds in CI using pinned toolchain/library versions.
7. The concise public PDF report from `scripts/build_public_report.py`.
8. Historical Edge Impulse screenshots and the recorded model card.

The Bedroom module uses the physical Wokwi outdoor LDR by default. If Blynk is explicitly enabled, V3 can take control of the outside-light score; moving the physical LDR again returns control to Wokwi.

## Historical Edge Impulse run vs exact reproduction

The repository records the historical training configuration and results in `edge-impulse/HISTORICAL_MODEL_CARD.md` and retains screenshots under `assets/`.

The generated inferencing archive is intentionally not redistributed. The public repository also does not contain a complete hosted Edge Impulse project snapshot that guarantees byte-for-byte reconstruction of the historical training run. Therefore:

- the **public deterministic demo is reproducible**;
- an **equivalent TinyML experiment can be regenerated** from the documented dataset/configuration;
- the **exact historical Edge Impulse run is not claimed to be bit-for-bit reproducible**.

## Enabling optional integrations

### Blynk

1. Supply your own Blynk template/auth values outside any public commit.
2. Set `ENABLE_BLYNK` to `1`.
3. Validate connectivity and virtual-pin configuration for your own project.

### Edge Impulse

1. Create or clone your own Edge Impulse project.
2. Import equivalent simulated data and train/test a classifier.
3. Export an Arduino/C++ inferencing library under the terms applicable to your project/account.
4. Add the generated library to the Arduino/Wokwi environment.
5. Update `EDGE_IMPULSE_INFERENCING_HEADER` in `wokwi/kitchen-living-room/sketch.ino` to the generated header name.
6. Set `USE_EDGE_IMPULSE_RUNTIME` to `1`.
7. Validate the build and runtime on the intended target.

## Real-world validation still required

A production-oriented follow-up would need calibrated physical sensors, independently labelled real data, collection-level train/validation/test separation, sensor-fault/drift tests, false-positive/false-negative analysis, actual target latency/RAM/flash/power measurements, secure credential provisioning and domain safety review.
