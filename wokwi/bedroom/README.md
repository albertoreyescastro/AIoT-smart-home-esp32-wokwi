# Bedroom Module

Public Wokwi files for the Bedroom ESP32-S3 controller. The checked-in files are authoritative for the portfolio version.

## Features

- indoor/outdoor LDR sensing and adaptive lighting;
- servo blind control;
- PIR presence tracking;
- DHT22 monitoring;
- AC hysteresis with **DHT-invalid fail-safe OFF**;
- Normal, Sleep, Privacy and Eco modes;
- Standard, Elderly and Child profiles;
- Home/Away security with pet-aware escalation;
- optional Blynk dashboard.

[Open Bedroom Wokwi simulation](https://wokwi.com/projects/465661521735358465)

Blynk is disabled by default with public placeholders. The physical outdoor LDR is authoritative until an enabled Blynk V3 interaction explicitly takes control; moving the physical LDR returns control to Wokwi. Dashboard control widgets are periodically resynchronised with local state.

The inside LDR starts at 0.1 lux for a deterministic demo baseline.

The visible PIN and secret word are demonstration values, not production credentials.

Real deployment requires physical hardware validation, sensor calibration, electrical safety checks and secure credential management.
