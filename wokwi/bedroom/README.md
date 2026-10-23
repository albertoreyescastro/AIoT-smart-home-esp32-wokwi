# Bedroom Module

This folder contains the public Wokwi files for the Bedroom ESP32-S3 controller.

## Scope

The module focuses on comfort, privacy, adaptive lighting, profile-sensitive behaviour and Home/Away security logic.

Main features:

- ESP32-S3 Wokwi simulation;
- indoor and outdoor LDR sensing;
- PIR occupancy tracking;
- servo blind control;
- smart ambient light + manual lamp state;
- DHT22 temperature/humidity monitoring;
- AC relay simulation;
- LCD and buzzer feedback;
- Normal, Sleep, Privacy and Eco modes;
- Standard, Elderly and Child profiles;
- Home/Away security and pet-aware escalation.

## Live simulation

[Open Bedroom Wokwi simulation](https://wokwi.com/projects/465661521735358465)

## Offline-first public default

The source contains placeholder Blynk values and keeps cloud connectivity disabled:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
#define ENABLE_BLYNK 0
```

The local simulation therefore starts without waiting for private cloud credentials. To use Blynk, provide your own private credentials and set `ENABLE_BLYNK` to `1`.

## Outside brightness

The physical Wokwi outdoor LDR controls outside brightness by default. If Blynk is enabled, virtual pin V3 can take control; moving the physical outdoor LDR again returns control to Wokwi.

This matches the labels visible in the public diagram and makes the demo usable without Blynk.

## Demonstration authentication

The visible PIN and secret word are simulation values only. They illustrate protected state transitions; they are not production credentials.

## Run

1. Open the Wokwi project.
2. Start the simulation.
3. Move the physical indoor/outdoor light sensors and PIR; use the buttons to change room/profile/house state.
4. Observe blinds, lighting, AC, LCD, buzzer and Serial Monitor behaviour.
5. Optionally configure and enable Blynk for dashboard interaction.

## Limitations

This is a simulation-based prototype. Real deployment would require physical hardware validation, sensor calibration, electrical safety checks and secure credential management.
