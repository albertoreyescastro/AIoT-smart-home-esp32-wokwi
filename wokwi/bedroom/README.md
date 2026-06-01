# Bedroom Module

This folder contains the Wokwi simulation files for the Bedroom module of the AIoT Smart Home system.

The Bedroom module focuses on comfort, privacy, adaptive lighting, profile-based behaviour and Away mode security logic. It is designed as a room-level ESP32-S3 controller with its own sensors, actuators, local rules and Blynk interaction.

## Files

```text
bedroom/
├── README.md
├── sketch.ino
├── diagram.json
└── libraries.txt
```

## Main Features

- ESP32-S3 based Wokwi simulation
- Indoor and outdoor light sensing using LDR sensors
- Adaptive smart ambient lighting
- Servo-based blind control
- PIR motion detection
- Manual lamp state
- DHT22 temperature and humidity monitoring
- AC relay simulation
- LCD I2C feedback
- Buzzer alerts
- Blynk dashboard interaction
- Normal, Sleep, Privacy and Eco room modes
- Standard, Elderly and Child profile logic
- Home/Away security state
- Pet-aware Away mode
- PIN and secret-word based protected actions

## Behaviour Overview

The Bedroom module combines sensor readings, selected room mode, active user profile and house status to decide how the room should respond.

Examples of behaviour include:

- In Normal mode, the system balances comfort, lighting support and natural light.
- In Sleep mode, blinds remain closed and lighting behaviour becomes more restrictive.
- In Privacy mode, blind control prioritises privacy over natural light.
- In Eco mode, unnecessary lighting and cooling are reduced.
- In Elderly and Child profiles, timing and support behaviour become more cautious.
- In Away mode, repeated motion can escalate from suspicious motion to intruder alert.

## Blynk Configuration

The public version of the code uses placeholder Blynk credentials:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
```

Replace these placeholders with your own Blynk credentials before running the dashboard.

The Wokwi Wi-Fi credentials are used only for simulation:

```cpp
char ssid[] = "Wokwi-GUEST";
char pass[] = "";
```

## Security Notes

The public version uses demo authentication values for simulation purposes only.

```cpp
const String SYSTEM_PIN = "1234";
```

These values should not be treated as real security credentials.

## Running the Simulation

To run this module:

1. Open the Bedroom Wokwi project.
2. Make sure `sketch.ino`, `diagram.json` and `libraries.txt` are present.
3. Replace Blynk placeholders with your own credentials if dashboard connectivity is required.
4. Start the simulation.
5. Use the simulated sensors, buttons, Serial Monitor and Blynk dashboard to test the behaviour.

## Limitations

This module is a simulation-based prototype. Real-world deployment would require hardware validation, sensor calibration, electrical safety checks and secure credential management.
