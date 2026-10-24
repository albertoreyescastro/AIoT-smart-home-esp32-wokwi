<p align="center">
  <img src="assets/aiot-smart-home-logo.png" alt="AIoT Smart Home ESP32-S3" width="420"/>
</p>

<h1 align="center">AIoT Smart Home ESP32-S3</h1>

<p align="center">
  Simulation-based ESP32-S3 smart-home prototype combining deterministic room automation, Wokwi, optional Blynk monitoring and a documented TinyML experimentation path.
</p>

<p align="center">
  <a href="https://wokwi.com/projects/465661521735358465">Bedroom Wokwi Demo</a> ·
  <a href="https://wokwi.com/projects/465661368262601729">Kitchen/Living Room Wokwi Demo</a> ·
  <a href="report/aiot_smart_home_public_report.pdf">Technical Report</a> ·
  <a href="docs/REPRODUCIBILITY.md">Reproducibility Notes</a>
</p>

---

## Overview

This repository presents a **simulation-based AIoT smart-home prototype** built around two ESP32-S3 room controllers. It demonstrates embedded Arduino/C++ programming, sensor/actuator orchestration, local comfort/privacy/security logic, persistence-gated environmental safety behaviour, optional Blynk integration and a historical Edge Impulse/TinyML experiment.

The project is an academic/portfolio prototype. It is **not a production safety system**, and the TinyML results are not presented as real-world hazard-detection validation.

### Public defaults are offline-first

Both sketches keep Blynk disabled by default:

```cpp
#define ENABLE_BLYNK 0
```

The Kitchen/Living Room sketch also keeps the generated Edge Impulse runtime disabled by default:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

A public clone therefore runs its local Wokwi logic without private cloud credentials or a generated third-party ML package.

When ML is disabled, `V29` reports the deterministic persistence-gated environmental state, `V30` reports `N/A`, and `V31` reports `DISABLED`. If a reviewer supplies a compatible Edge Impulse library and explicitly enables it, the model output is **advisory telemetry only**; safety actuators remain controlled by the deterministic state machine.

---

## Recruiter Snapshot

| Area | Evidence |
|---|---|
| Embedded systems | Two ESP32-S3 Arduino sketches with room-level state/control logic |
| IoT simulation | Public Wokwi demos plus checked-in `sketch.ino`, `diagram.json` and pinned `libraries.txt` |
| Reliability | Persistence-gated gas escalation, DHT fail-safe AC shutdown, deterministic scenario tests |
| Cloud/dashboard | Optional Blynk virtual-pin monitoring and interaction |
| TinyML | Synthetic dataset, historical Edge Impulse screenshots/model card, optional advisory inference surface |
| Reproducibility | Dataset/rule validator, pinned dependencies and ESP32-S3 CI compilation |
| Documentation | Architecture visuals, module notes, model card and professional technical report |

### What the ML result does - and does not - show

The environmental dataset is **simulated and rule-labelled**. Labels are generated from demonstration thresholds using the same synthetic variables supplied to the model. Strong classifier performance is therefore expected: it demonstrates an embedded-ML workflow learning designed decision regions, not independent discovery of real household hazards.

Real-world validation would require physical sensors, calibration, independently labelled data, collection-aware train/validation/test separation, hardware measurements and a safety review.

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) and [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md).

---

## Live Demos

| Component | Link | Purpose |
|---|---|---|
| Bedroom | [Open in Wokwi](https://wokwi.com/projects/465661521735358465) | Lighting, blinds, comfort, profiles and Home/Away security |
| Kitchen/Living Room | [Open in Wokwi](https://wokwi.com/projects/465661368262601729) | Persistence-gated gas/heat monitoring, emergency logic and optional Blynk interaction |
| Technical report | [Open PDF](report/aiot_smart_home_public_report.pdf) | Architecture, implementation, evaluation, evidence and limitations |

The checked-in Wokwi files are the repository authority. If a hosted Wokwi copy ever differs, refresh it from the matching `wokwi/<module>/` folder.

---

## Architecture

```text
Smart Home Prototype
│
├── Bedroom ESP32-S3
│   ├── PIR occupancy
│   ├── indoor/outdoor light sensing
│   ├── DHT22 temperature/humidity
│   ├── servo-controlled blinds
│   ├── PWM ambient + manual lighting
│   ├── AC relay + LCD
│   ├── profile/privacy logic
│   └── Home/Away security state
│
└── Kitchen/Living Room ESP32-S3
    ├── MQ2 gas input
    ├── DHT22 temperature/humidity
    ├── persistence-gated gas state machine
    ├── buzzer + emergency-cooling indicator
    ├── optional Blynk dashboard
    ├── deterministic actionable environmental state
    └── optional advisory Edge Impulse inference
```

---

## Reliability and Safety Semantics

The public Kitchen/Living Room runtime deliberately separates **raw observations** from **actionable state**:

- MQ2 warm-up: 15 s;
- fumes/warning: requires sustained elevation for 2.5 s;
- normal danger path: requires sustained danger/fumes history for 8 s;
- severe gas path: requires 1.2 s persistence;
- clearing a latched gas state: requires 5 s below the clear boundary;
- optional ML never bypasses these timers;
- if DHT data is invalid, the AC is forced **OFF** and heat classification becomes unavailable, while gas monitoring remains active.

These are project-specific demonstration rules, **not calibrated safety limits**.

---

## Bedroom Module

Location: [`wokwi/bedroom/`](wokwi/bedroom/)

- Normal, Sleep, Privacy and Eco modes;
- Standard, Elderly and Child profiles;
- adaptive lighting and servo blind automation;
- PIR-based occupancy tracking;
- DHT22 monitoring with AC hysteresis and invalid-sensor fail-safe;
- Home/Away state, pet-aware motion escalation and demonstration authentication.

The physical Wokwi outdoor LDR is authoritative by default. If Blynk is enabled, V3 can take control; moving the physical LDR again returns control to Wokwi.

---

## Kitchen / Living Room Module

Location: [`wokwi/kitchen-living-room/`](wokwi/kitchen-living-room/)

- MQ2 gas-score monitoring with persistence/hysteresis;
- DHT22 temperature/humidity sensing with fail-safe AC shutdown;
- heat anomaly and gas+heat emergency states;
- buzzer, blinds and emergency-cooling indicator;
- Home/Away security logic;
- optional Blynk dashboard;
- optional Edge Impulse classifier used only as advisory telemetry.

No generated Edge Impulse inferencing archive is present in the **current source tree**.

---

## TinyML / Edge Impulse Experiment

[`data/environmental_training_dataset.csv`](data/environmental_training_dataset.csv) contains simulated `gas_score`, `temperature`, `humidity` and a five-class label. The labels are deterministic demonstration rules: `GAS_HEAT_EMERGENCY`, `GAS_DANGER`, `HEAT_ANOMALY`, `COOKING_FUMES`, or `NORMAL`. Humidity is an input feature but does not generate the synthetic ground-truth label.

Historical Edge Impulse evidence is retained under [`assets/`](assets/) and summarised in [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md). The exact historical split, random seed and training hyperparameters are not asserted because independently verifiable machine-readable configuration is not preserved.

---

## Repository Quality Checks

```bash
python scripts/validate_repo.py
python scripts/test_scenarios.py
```

GitHub Actions additionally compiles:

1. the Bedroom public sketch;
2. the Kitchen/Living Room public default;
3. the **optional Edge Impulse integration surface** against a CI-only mock generated header, so that path cannot silently rot even though the real third-party export is not redistributed.

Toolchain/library versions are pinned in [`.github/workflows/quality.yml`](.github/workflows/quality.yml) and mirrored in both Wokwi `libraries.txt` files.

---

## Blynk Configuration

The public sketches intentionally contain placeholders and keep Blynk off by default. `Wokwi-GUEST` is the simulator network, not a private credential. Any visible PIN or secret word is a demonstration value, not production authentication.

---

## Limitations

- sensors are simulated;
- gas/heat thresholds are demonstration values;
- the ML dataset is synthetic and rule-labelled;
- model metrics are historical platform evidence, not independent real-world validation;
- no physical ESP32-S3 deployment is claimed;
- the generated Edge Impulse runtime is not present in the current source tree and is disabled by default;
- Blynk is disabled by default;
- emergency-response behaviour requires domain review before real deployment;
- demo authentication values are not secure production credentials.

---

## Technical Report

[`report/aiot_smart_home_public_report.pdf`](report/aiot_smart_home_public_report.pdf)

The report is authored from retained LaTeX source. The source package is maintained separately from the public repository so the portfolio tree does not duplicate the report's large figure set.

---

## Licence

Original project code and documentation are provided under [`LICENSE`](LICENSE). Third-party tools, libraries and generated deployment components remain subject to their own licence terms.

---

## Author

**Alberto Reyes Castro**  
Physics graduate · MSc Artificial Intelligence Technology student

Portfolio focus: applied AI, embedded/IoT systems, TinyML experimentation, scientific computing and reliable automation.
