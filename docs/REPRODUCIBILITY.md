# Reproducibility and Evaluation Notes

This document explains what can and cannot be inferred from the public AIoT/TinyML results in this repository.

## Scope

The project is a **simulation-based portfolio prototype**. The Wokwi room controllers, Blynk integration, safety-state logic and Edge Impulse workflow are intended to demonstrate embedded/AIoT engineering practice. They are not evidence that the system is ready for a safety-critical real-world deployment.

## Dataset provenance

`data/environmental_training_dataset.csv` contains simulated sensor values with three columns used as model inputs:

- `gas_score` — simulated MQ2 score on a 0–1000 scale
- `temperature` — simulated DHT22 temperature in °C
- `humidity` — simulated DHT22 relative humidity in %

The target labels were generated deterministically from demonstration thresholds:

| Condition | Label |
|---|---|
| `gas_score >= 850` and `temperature >= 55°C` | `GAS_HEAT_EMERGENCY` |
| `gas_score >= 850` | `GAS_DANGER` |
| `temperature >= 55°C` | `HEAT_ANOMALY` |
| `gas_score >= 420` | `COOKING_FUMES` |
| otherwise | `NORMAL` |

These thresholds are **project-specific demonstration values, not calibrated safety limits**.

Because the labels are derived from the same synthetic input variables used to train the classifier, strong model performance is expected. The Edge Impulse results therefore demonstrate that the embedded ML workflow can reproduce the designed decision regions; they do **not** demonstrate independent real-world predictive validity or superiority over the deterministic rules.

Humidity is included as an input feature in the demonstration dataset but does not determine the synthetic ground-truth label. It should therefore be treated as a non-causal/noise feature in this specific experiment.

## What is reproducible from this repository

A reviewer can reproduce or inspect:

1. The two Wokwi ESP32-S3 simulations.
2. The deterministic room-control and safety logic in the Arduino sketches.
3. The synthetic training dataset and its documented label-generation rules.
4. The repository integrity checks with:

   ```bash
   python scripts/validate_repo.py
   ```

5. The public Edge Impulse training/test evidence shown in `assets/`.
6. The technical report in `report/`.

GitHub Actions also runs the repository validator and attempts to compile both public ESP32-S3 sketches with the Edge Impulse runtime disabled.

## Edge Impulse export

The generated Edge Impulse inferencing archive is intentionally **not redistributed** in the hardened public source tree. Generated deployment packages can contain Edge Impulse SDK/runtime components and other third-party material under their own licence terms. The project MIT licence applies to the original repository code and documentation, not automatically to third-party generated dependencies.

To reproduce the TinyML deployment path:

1. Create or clone an Edge Impulse project.
2. Import equivalent simulated data and train a classifier.
3. Export the project as an Arduino/C++ inferencing library under the licence terms applicable to your Edge Impulse account/project.
4. Add the generated library to the Arduino/Wokwi environment.
5. In `wokwi/kitchen-living-room/sketch.ino`, replace the placeholder inferencing header with the header generated for your project.
6. Set `USE_EDGE_IMPULSE_RUNTIME` to `1` and validate the build/runtime on the intended target.

The checked-in public Wokwi demo keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`; safety behaviour remains deterministic and inspectable without a generated ML runtime.

## What would be required for real-world validation

A production-oriented follow-up would need, at minimum:

- physical ESP32-S3 hardware tests;
- calibrated MQ2/DHT22/PIR/LDR measurements;
- real environmental data collected under a documented protocol;
- independently labelled ground truth;
- train/validation/test separation at the data-collection level;
- robustness tests for sensor drift and missing/faulty readings;
- false-positive/false-negative analysis for safety events;
- latency, memory and power measurements on the actual target device;
- security review of authentication, Blynk credentials and network configuration;
- domain/safety review before any real emergency-response behaviour is trusted.

## Interpretation

The strongest portfolio claim for this project is therefore:

> A modular ESP32-S3 smart-home simulation that integrates IoT control, safety-state logic, cloud dashboard interaction and a transparent TinyML experimentation path, with explicit separation between deterministic safety behaviour and synthetic-model evaluation.

That claim is supported by the public artefacts without overstating the evidence.
