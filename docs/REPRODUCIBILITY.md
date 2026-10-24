# Reproducibility and Evaluation Notes

This document defines what the hardened public AIoT repository does and does not reproduce.

## Public runtime defaults

Both sketches keep `ENABLE_BLYNK` at `0`. The Kitchen/Living Room sketch also keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`. A public clone therefore runs local Wokwi logic without private cloud credentials or a generated Edge Impulse package.

When ML is disabled, the actionable environmental state is deterministic and persistence-gated. ML confidence is `N/A` and the raw ML prediction is `DISABLED`. If a compatible generated runtime is explicitly supplied and enabled, its prediction is advisory telemetry only and does not drive safety actuators.

## Dataset provenance

`data/environmental_training_dataset.csv` contains simulated gas, temperature and humidity values. Labels are generated deterministically from project-specific demonstration boundaries. Humidity is included as an input but does not determine the synthetic ground-truth label. Strong classifier performance is therefore expected and is not independent real-world predictive validation.

## Runtime reliability contract

Kitchen/Living Room gas actions use a persistence-gated state machine: 15 s MQ2 warm-up, 2.5 s fumes persistence, 8 s normal danger persistence, 1.2 s severe-path persistence and 5 s clear persistence. The optional ML path cannot bypass these timers.

If DHT data becomes invalid, both modules force the AC off. Kitchen gas monitoring remains available independently of DHT validity, while heat-only classification becomes unavailable until valid temperature/humidity data returns.

## What is reproducible from this repository

A reviewer can reproduce or inspect:

1. both checked-in Wokwi ESP32-S3 room configurations;
2. deterministic room-control and safety logic;
3. the complete synthetic dataset and labelling contract;
4. repository validation with `python scripts/validate_repo.py`;
5. temporal/design scenario contracts with `python scripts/test_scenarios.py`;
6. both public ESP32-S3 builds with pinned toolchain/library versions;
7. a CI compile of the optional Edge Impulse integration surface using a mock generated header;
8. the professional public PDF report;
9. historical Edge Impulse screenshots and the evidence-based model card.

The hosted Wokwi projects are convenience demos; the checked-in `sketch.ino`, `diagram.json` and `libraries.txt` files are authoritative.

## Historical Edge Impulse run vs exact reproduction

The repository preserves historical screenshots and the metrics that those screenshots support. It does **not** preserve independently verifiable machine-readable evidence for the exact historical train/validation/test split, random seed or training hyperparameters, and therefore does not assert them.

The generated inferencing archive is not present in the current source tree. An equivalent workflow can be recreated from the public dataset and model description, but the exact historical hosted run is not claimed to be bit-for-bit reproducible.

## Enabling optional integrations

### Blynk

Supply your own template/auth values outside public commits, set `ENABLE_BLYNK` to `1`, and validate your own virtual-pin configuration.

### Edge Impulse

Create your own Edge Impulse project, import equivalent simulated data, train/test a five-class classifier, export a compatible Arduino/C++ library, set `EDGE_IMPULSE_INFERENCING_HEADER` to its generated header, enable `USE_EDGE_IMPULSE_RUNTIME`, and validate on the intended target. The resulting ML output remains advisory unless you deliberately redesign and revalidate the safety architecture.

## Real-world validation still required

A production-oriented follow-up needs calibrated physical sensors, independently labelled real data, collection-aware data splits, sensor-fault/drift tests, false-positive/false-negative analysis, actual target latency/RAM/flash/power measurements, secure credential provisioning and domain safety review.
