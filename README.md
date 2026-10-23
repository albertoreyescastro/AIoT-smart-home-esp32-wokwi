<p align="center">
  <img src="assets/aiot-smart-home-logo.png" alt="AIoT Smart Home ESP32-S3" width="420"/>
</p>

<h1 align="center">AIoT Smart Home ESP32-S3</h1>

<p align="center">
  Simulation-based ESP32-S3 smart-home prototype combining Wokwi, deterministic room automation, optional Blynk monitoring and a transparent TinyML experimentation path.
</p>

<p align="center">
  <a href="https://wokwi.com/projects/465661521735358465">Bedroom Wokwi Demo</a> ·
  <a href="https://wokwi.com/projects/465661368262601729">Kitchen/Living Room Wokwi Demo</a> ·
  <a href="report/aiot_smart_home_public_report.pdf">Technical Report</a> ·
  <a href="docs/REPRODUCIBILITY.md">Reproducibility Notes</a>
</p>

---

## Overview

This repository presents a **simulation-based AIoT smart-home prototype** built around two ESP32-S3 room controllers.

It demonstrates:

- embedded Arduino/C++ programming;
- sensor/actuator orchestration in Wokwi;
- room-specific comfort, privacy, security and environmental-safety logic;
- optional Blynk dashboard integration;
- a synthetic environmental dataset;
- an Edge Impulse / TinyML experimentation workflow;
- explicit separation between deterministic safety behaviour and optional ML inference;
- reproducibility checks, scenario-contract tests and ESP32-S3 CI compilation.

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

A public clone can therefore run the local Wokwi logic without private cloud credentials or a generated third-party ML package.

When ML runtime is disabled, the environmental state is **rule-derived**. The code reports ML confidence as `N/A` and the raw ML prediction as `DISABLED`; it does not fabricate a prediction or confidence value.

---

## Recruiter Snapshot

| Area | Evidence in this repository |
|---|---|
| Embedded systems | Two ESP32-S3 Arduino sketches with room-level state/control logic |
| IoT simulation | Public Wokwi demos for Bedroom and Kitchen/Living Room modules |
| Cloud/dashboard integration | Optional Blynk virtual-pin monitoring and interaction |
| Safety-state modelling | Gas, heat, occupancy and escalation logic with deterministic fallback |
| TinyML workflow | Synthetic dataset, historical Edge Impulse training/test evidence and optional inference integration |
| Reproducibility | Dataset/rule validator, scenario contracts, pinned CI toolchain and deterministic report build |
| Documentation | Architecture visuals, module notes, model card and concise public technical report |

### What the ML result does - and does not - show

The environmental dataset is **simulated and rule-labelled**. Labels are generated from demonstration thresholds using the same synthetic variables supplied to the model. Strong classifier performance is therefore expected: it shows that an embedded-ML workflow can learn the designed decision regions, not that the model has independently discovered real household hazards.

Real-world validation would require physical sensors, calibration, independently labelled data, hardware measurements and a safety review.

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) and [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md).

---

## Live Demos

| Component | Link | Purpose |
|---|---|---|
| Bedroom | [Open in Wokwi](https://wokwi.com/projects/465661521735358465) | Lighting, blinds, comfort, profiles and Home/Away security |
| Kitchen/Living Room | [Open in Wokwi](https://wokwi.com/projects/465661368262601729) | Gas/heat monitoring, emergency logic and optional Blynk interaction |
| 2D/3D house model | [Open Planner 5D](https://planner5d.onelink.me/stDT/wjmc3u8i) | Visual layout of the smart-home concept |
| Technical report | [Open PDF](report/aiot_smart_home_public_report.pdf) | Current public architecture, evaluation and limitations |

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
    ├── PIR occupancy
    ├── indoor/outdoor light sensing
    ├── visual/audible alerts
    ├── emergency-cooling indicator
    ├── optional Blynk dashboard
    ├── deterministic environmental rules
    └── optional Edge Impulse inference layer
```

The deterministic path remains authoritative in the public simulation. If a real Edge Impulse runtime is explicitly enabled and returns a valid prediction, the code may increase the selected environmental severity but does not suppress a more severe deterministic state.

---

## Bedroom Module

Location: [`wokwi/bedroom/`](wokwi/bedroom/)

Main behaviours:

- Normal, Sleep, Privacy and Eco modes;
- Standard, Elderly and Child profiles;
- adaptive lighting using indoor/outdoor brightness;
- servo-controlled blind automation;
- PIR-based occupancy tracking;
- temperature/humidity monitoring;
- AC relay logic with hysteresis;
- Home/Away state and repeated-motion escalation;
- demonstration-only authentication/recovery flows.

### Outside-light source

The physical Wokwi outdoor LDR is authoritative by default. If Blynk is explicitly enabled, V3 can take control of the outside-light score; moving the physical LDR again returns control to Wokwi.

---

## Kitchen / Living Room Module

Location: [`wokwi/kitchen-living-room/`](wokwi/kitchen-living-room/)

Main behaviours:

- MQ2-based simulated gas monitoring;
- DHT22 temperature/humidity sensing;
- gas warning/danger persistence logic;
- heat anomaly and gas+heat emergency states;
- buzzer and visual alerts;
- deterministic fallback safety logic;
- optional Edge Impulse classifier integration.

The public build keeps the generated Edge Impulse runtime disabled by default. In that mode:

- `V29` / environment status reflects deterministic rules;
- ML confidence is `N/A`;
- raw ML prediction is `DISABLED`.

No generated Edge Impulse inferencing archive is redistributed in the hardened public source tree.

---

## TinyML / Edge Impulse Experiment

### Dataset

[`data/environmental_training_dataset.csv`](data/environmental_training_dataset.csv) contains:

- `gas_score` - simulated MQ2 score, 0-1000;
- `temperature` - simulated DHT22 temperature in C;
- `humidity` - simulated relative humidity in %;
- `label` - one of five environmental states.

Synthetic labels are generated from demonstration rules:

| Rule | Label |
|---|---|
| `gas_score >= 850` and `temperature >= 55 C` | `GAS_HEAT_EMERGENCY` |
| `gas_score >= 850` | `GAS_DANGER` |
| `temperature >= 55 C` | `HEAT_ANOMALY` |
| `gas_score >= 420` | `COOKING_FUMES` |
| otherwise | `NORMAL` |

These are **not calibrated safety thresholds**. Humidity is included as an input feature but does not determine the synthetic ground-truth label in this experiment.

### Historical model evidence

The repository retains Edge Impulse training/test screenshots under [`assets/`](assets/) and records the historical configuration/metrics in [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md).

The historical run is evidence of the workflow, not a claim of exact bit-for-bit reproducibility. An equivalent experiment can be regenerated, but the complete historical hosted project/export is not stored here.

---

## Visual Evidence

### System layout

<p align="center">
  <img src="assets/system-layout.png" alt="AIoT smart home system layout" width="100%"/>
</p>

### Simulation

| Kitchen/Living Room | Bedroom intruder alert |
|---|---|
| <img src="assets/kitchen-wokwi-serial.png" alt="Kitchen and living room Wokwi simulation and Serial Monitor"/> | <img src="assets/intruder-alert-demo.png" alt="Bedroom intruder alert scenario in Wokwi"/> |

### Historical Edge Impulse experiment

| Test results | Estimated on-device performance |
|---|---|
| <img src="assets/edge-impulse-test-results.png" alt="Historical Edge Impulse test results and confusion matrix"/> | <img src="assets/edge-impulse-on-device-performance.png" alt="Historical Edge Impulse estimated on-device performance"/> |

---

## Repository Quality Checks

Run locally:

```bash
python scripts/validate_repo.py
python scripts/test_scenarios.py
```

The validator checks dataset integrity, Wokwi diagrams, public placeholders, token patterns, offline Blynk defaults, ML-disabled semantics, dependency/CI pinning, public documentation and report size/currentness.

GitHub Actions additionally:

- compile both ESP32-S3 sketches with pinned toolchain/library versions;
- run deterministic scenario-contract tests;
- rebuild the public PDF with pinned ReportLab and fail if the committed PDF has drifted.

Pinned versions are visible in [`.github/workflows/quality.yml`](.github/workflows/quality.yml).

---

## Blynk Configuration

The public sketches intentionally contain placeholders:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
#define ENABLE_BLYNK 0
```

`Wokwi-GUEST` is used only as the simulator network. To use Blynk, supply your own private values and explicitly set `ENABLE_BLYNK` to `1`.

Any PINs or secret words visible in the source are demonstration values, not production credentials.

---

## Repository Structure

```text
.
├── .github/workflows/quality.yml
├── README.md
├── LICENSE
├── assets/
├── data/
├── docs/REPRODUCIBILITY.md
├── edge-impulse/
│   ├── README.md
│   └── HISTORICAL_MODEL_CARD.md
├── report/
│   ├── README.md
│   └── aiot_smart_home_public_report.pdf
├── scripts/
│   ├── build_public_report.py
│   ├── test_scenarios.py
│   └── validate_repo.py
└── wokwi/
    ├── bedroom/
    └── kitchen-living-room/
```

---

## Limitations

- sensors are simulated;
- gas/heat thresholds are demonstration values;
- the ML dataset is synthetic and rule-labelled;
- model performance is not independent real-world validation;
- no physical ESP32-S3 deployment is claimed;
- Edge Impulse performance screenshots are historical platform evidence, not measurements from the current Wokwi runtime;
- the generated Edge Impulse runtime is disabled by default in the public simulation;
- Blynk is disabled by default so the demo does not depend on placeholder cloud credentials;
- emergency-response behaviour would need professional/domain review before real deployment;
- demonstration authentication values are not secure production credentials.

---

## Technical Report

The current public report is generated deterministically from source and is available at:

[`report/aiot_smart_home_public_report.pdf`](report/aiot_smart_home_public_report.pdf)

---

## Licence

Original project code and documentation are provided under [`LICENSE`](LICENSE). Third-party tools, libraries and generated deployment components remain subject to their own licence terms.

---

## Author

**Alberto Reyes Castro**  
Physics graduate · MSc Artificial Intelligence Technology student

Portfolio focus: applied AI, embedded/IoT systems, TinyML experimentation, scientific computing and reliable automation.
