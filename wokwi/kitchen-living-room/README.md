# Kitchen and Living Room Module

Public Wokwi files for the Kitchen/Living Room ESP32-S3 controller. The checked-in files are authoritative for the portfolio version.

## Features

- MQ2 gas-score monitoring with persistence/hysteresis;
- DHT22 temperature/humidity sensing;
- AC fail-safe OFF when DHT data is invalid;
- gas warning/danger and heat anomaly states;
- buzzer, blinds and emergency-cooling indicator;
- Home/Away security;
- optional Blynk;
- optional Edge Impulse inference as **advisory telemetry only**.

[Open Kitchen/Living Room Wokwi simulation](https://wokwi.com/projects/465661368262601729)

## Public defaults

```cpp
#define ENABLE_BLYNK 0
#define USE_EDGE_IMPULSE_RUNTIME 0
```

With ML disabled, `V29` is the deterministic persistence-gated environmental state, `V30` is `N/A`, and `V31` is `DISABLED`. No fabricated confidence/prediction is emitted.

Gas actions cannot be triggered by one isolated raw reading: fumes, danger, severe escalation and clearing all have explicit persistence windows. Optional ML does not bypass those windows or drive safety actuators.

The current source tree does not include a generated Edge Impulse archive. See [`../../edge-impulse/README.md`](../../edge-impulse/README.md).

Thresholds and emergency behaviour are demonstration constructs, not calibrated safety limits.
