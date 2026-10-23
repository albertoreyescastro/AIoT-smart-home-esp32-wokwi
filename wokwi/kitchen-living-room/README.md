# Kitchen and Living Room Module

This folder contains the public Wokwi files for the Kitchen/Living Room ESP32-S3 controller.

## Scope

The module focuses on environmental monitoring, deterministic gas/heat safety logic, emergency response, Home/Away security and an **optional** Edge Impulse inference path.

Main features:

- ESP32-S3 Wokwi simulation;
- MQ2 gas-score monitoring;
- DHT22 temperature/humidity sensing;
- PIR and indoor/outdoor light sensing;
- servo blind and manual-lamp control;
- AC relay simulation;
- buzzer + emergency-cooling indicator;
- LCD feedback;
- Normal, Privacy and Eco room modes;
- Standard, Elderly and Child profiles;
- deterministic environmental state and gas persistence logic;
- optional Blynk and Edge Impulse integrations.

## Live simulation

[Open Kitchen and Living Room Wokwi simulation](https://wokwi.com/projects/465661368262601729)

## Offline-first public defaults

```cpp
#define ENABLE_BLYNK 0
#define USE_EDGE_IMPULSE_RUNTIME 0
```

The local simulation therefore runs without private Blynk credentials or a generated Edge Impulse library.

### ML-disabled semantics

When `USE_EDGE_IMPULSE_RUNTIME` is `0`:

- no classifier runs;
- environmental status is rule-derived;
- ML confidence is `N/A`;
- raw ML prediction is `DISABLED`.

The project does **not** fabricate a model prediction or confidence value in Wokwi-safe mode.

## Edge Impulse integration

The generated inferencing ZIP is intentionally **not** stored in this public repository. To enable a compatible runtime:

1. generate your own Arduino/C++ inferencing library;
2. add it to the build environment;
3. change `EDGE_IMPULSE_INFERENCING_HEADER` in `sketch.ino` to your generated header;
4. set `USE_EDGE_IMPULSE_RUNTIME` to `1`;
5. compile and validate on the intended target.

See [`../../edge-impulse/README.md`](../../edge-impulse/README.md) and [`../../edge-impulse/HISTORICAL_MODEL_CARD.md`](../../edge-impulse/HISTORICAL_MODEL_CARD.md).

## Synthetic dataset

The environmental dataset is simulated and rule-labelled. Its five classes are generated from project-specific gas/temperature demonstration boundaries. It is suitable for demonstrating the TinyML workflow, not for validating a production safety model.

## Blynk

The source contains placeholders and keeps Blynk disabled by default:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
#define ENABLE_BLYNK 0
```

Provide private values and explicitly enable the integration if dashboard connectivity is required.

## Run

1. Open the Kitchen/Living Room Wokwi project.
2. Start the simulation and allow the MQ2 warm-up period to finish.
3. Change gas, temperature, humidity, light and motion inputs.
4. Observe deterministic environmental state, alerts, AC/blinds, emergency-cooling indicator, LCD and Serial Monitor.
5. Optionally configure Blynk or a generated Edge Impulse runtime separately.

## Limitations

Gas thresholds, emergency responses and ML evidence are simulation/portfolio constructs. Real deployment would require calibrated sensors, real independently labelled data, physical-hardware testing, fault analysis and safety review.
