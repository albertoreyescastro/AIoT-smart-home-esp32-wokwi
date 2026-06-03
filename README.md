<p align="center">
  <img src="assets/aiot-smart-home-logo.png" alt="AIoT Smart Home ESP32-S3" width="420"/>
</p>

<h1 align="center">AIoT Smart Home ESP32-S3</h1>

<p align="center">
  Edge-AI smart home simulation using ESP32-S3, Wokwi, Blynk, sensors and an Edge Impulse-inspired environmental safety layer.
</p>

<p align="center">
  <a href="https://wokwi.com/projects/465661521735358465">Bedroom Wokwi Demo</a> ·
  <a href="https://wokwi.com/projects/465661368262601729">Kitchen/Living Room Wokwi Demo</a> ·
  <a href="report/aiot_smart_home_public_report.pdf">Technical Report</a> ·
  <a href="https://planner5d.onelink.me/stDT/wjmc3u8i">2D/3D House Model</a>
</p>

---

## Overview

This repository presents a modular AIoT smart home simulation based on ESP32-S3 room controllers. The project combines embedded systems, sensor-based automation, rule-based decision logic, Blynk dashboard interaction and an optional Edge Impulse-inspired environmental classification layer.

The system is divided into two main room-level modules:

- **Bedroom Module**: adaptive lighting, privacy-aware blind control, motion detection, sleep/privacy/eco modes, user profiles and Home/Away security logic.
- **Kitchen and Living Room Module**: gas safety monitoring, temperature and humidity sensing, emergency response, Blynk dashboard interaction and optional Edge Impulse integration.

The project was developed as a simulation-based prototype using **Wokwi**, **Arduino/C++**, **Blynk IoT** and an **Edge Impulse / TinyML workflow**.

---

## Quick Demo

| Module | Live Simulation | Main Features |
|---|---|---|
| Bedroom | [Open in Wokwi](https://wokwi.com/projects/465661521735358465) | Adaptive lighting, privacy-aware blinds, thermal logic, user profiles and Away-mode security |
| Kitchen/Living Room | [Open in Wokwi](https://wokwi.com/projects/465661368262601729) | Gas monitoring, emergency response, thermal control and AI-inspired environmental classification |
| 2D/3D House Model | [Open Planner 5D model](https://planner5d.onelink.me/stDT/wjmc3u8i) | Visual layout of the smart home architecture |
| Technical Report | [Open PDF report](report/aiot_smart_home_public_report.pdf) | Public portfolio report with design, implementation, evaluation and limitations |

> The Planner 5D model is best opened on a laptop or desktop browser. On mobile devices, Planner 5D may ask the user to download the app.

---

## What Makes This Project Different?

This project is more than a basic smart home simulation. It combines room-specific embedded logic, privacy-aware automation, safety escalation and an Edge-AI workflow in a modular ESP32-S3 architecture.

- **Room-level intelligence:** each room has its own ESP32-S3 controller, sensors, actuators and decision logic.
- **Hybrid AI + rule-based safety:** deterministic safety rules remain active, while the Edge Impulse-inspired layer adds environmental classification.
- **User-aware behaviour:** the system adapts to Standard, Elderly and Child profiles.
- **Privacy-first design:** most decisions are handled locally instead of depending entirely on cloud processing.
- **Security-oriented states:** Away mode, child-mode protection and intruder-alert clearing require controlled interactions.
- **Complete portfolio package:** the repository includes code, dataset, Wokwi simulations, Edge Impulse export material, visual assets and a public technical report.

---

## Visual Overview

### System Layout

<p align="center">
  <img src="assets/system-layout.png" alt="AIoT smart home system layout" width="100%"/>
</p>

### Simulation and AI Results

| Kitchen/Living Room Simulation |Bedroom Simulation |
|---|---|
| <img src="assets/kitchen-wokwi-serial.png" alt="Kitchen and living room Wokwi simulation and Serial Monitor"/> | <img src="assets/intruder-alert-demo.png" alt="Intruder alert scenario in Wokwi"/> |

| Edge Impulse Test Results | Edge Impulse On-Device Performance |
|---|---|
| <img src="assets/edge-impulse-test-results.png" alt="Edge Impulse test results and confusion matrix"/> | <img src="assets/edge-impulse-on-device-performance.png" alt="Edge Impulse on-device performance"/> |

<details>
<summary>Additional Edge Impulse training results</summary>

<p align="center">
  <img src="assets/edge-impulse-training-results.png" alt="Edge Impulse training performance" width="70%"/>
</p>

</details>

---

## Project Objectives

The main objective of this project is to design a smart home prototype that can respond to environmental conditions, user preferences and safety risks in real time.

The system focuses on:

- Adaptive lighting control
- Privacy-aware automation
- Energy-conscious behaviour
- Gas and environmental safety monitoring
- User-profile based decision logic
- Home/Away security behaviour
- Remote monitoring and interaction through Blynk
- Modular room-level smart home design
- Embedded AI/TinyML workflow for environmental safety classification

---

## Repository Structure

```text
aiot-smart-home-esp32-wokwi/
├── README.md
├── LICENSE
├── .gitignore
├── assets/
│   ├── aiot-smart-home-logo.png
│   ├── system-layout.png
│   ├── kitchen-wokwi-serial.png
│   ├── intruder-alert-demo.png
│   ├── edge-impulse-test-results.png
│   ├── edge-impulse-on-device-performance.png
│   └── edge-impulse-training-results.png
├── data/
│   ├── README.md
│   └── environmental_training_dataset.csv
├── edge-impulse/
│   ├── README.md
│   └── edge_impulse_kitchen_living_room_inferencing.zip
├── report/
│   ├── README.md
│   └── aiot_smart_home_public_report.pdf
└── wokwi/
    ├── bedroom/
    │   ├── README.md
    │   ├── sketch.ino
    │   ├── diagram.json
    │   └── libraries.txt
    └── kitchen-living-room/
        ├── README.md
        ├── sketch.ino
        ├── diagram.json
        └── libraries.txt
```

---

## Technologies Used

| Area | Tools / Components |
|---|---|
| Microcontroller | ESP32-S3 |
| Simulation | Wokwi |
| Programming | Arduino/C++ |
| IoT dashboard | Blynk IoT |
| AI workflow | Edge Impulse, TinyML / embedded AI |
| Sensors | DHT22, MQ2, PIR, LDR |
| Actuators / outputs | Servo motor, AC relay, LCD I2C display, buzzer, LEDs |

---

## Modules

### Bedroom Module

The Bedroom module focuses on comfort, privacy and user-centred automation. It includes adaptive lighting, blind control, motion-based presence detection, temperature monitoring, AC control, child mode, elderly profile logic and Away-mode security behaviour.

Folder:

```text
wokwi/bedroom/
```

Main behaviours:

- Normal, Sleep, Privacy and Eco room modes
- Standard, Elderly and Child user profiles
- Adaptive blinds based on light, room state and privacy needs
- PIR-based occupancy detection with profile-dependent hold times
- Thermal comfort logic using DHT22 readings
- Away-mode intrusion escalation and authenticated recovery

### Kitchen and Living Room Module

The Kitchen and Living Room module focuses on environmental safety and emergency response. It includes gas detection, temperature and humidity monitoring, buzzer alerts, sprinkler/emergency-cooling indication, Blynk dashboard interaction and an optional Edge Impulse runtime integration.

Folder:

```text
wokwi/kitchen-living-room/
```

Main behaviours:

- Normal, Privacy and Eco room modes
- Gas safety monitoring using MQ2 readings
- Thermal monitoring using DHT22 readings
- Emergency cooling indicator for gas + heat events
- Blynk dashboard outputs for monitoring and remote interaction
- Optional Edge Impulse-inspired environmental safety classification

---

## Blynk Configuration

The public version of the code uses placeholder credentials:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
```

To run the project with Blynk, replace these placeholders with your own Blynk template ID and authentication token.

Do not publish real Blynk tokens, Wi-Fi credentials or private API keys in a public repository.

The public report and screenshots may include Blynk dashboard views and virtual-pin mapping figures where they help explain the system architecture. These materials are retained only when they do not expose private tokens, credentials or personal data.

---

## Security and Demo Authentication Notes

The project includes child-mode protection, Away-to-Home authentication and intruder-alert clearing logic.

Any authentication PINs, secret words or command values visible in the public code are **demonstration values for simulation purposes only**. They should not be reused in a real deployment.

For a real device, these values should be moved to secure configuration files, environment variables or a private secrets manager, and the repository should keep only placeholders.

---

## Edge Impulse Integration

The Kitchen and Living Room module includes an optional Edge Impulse integration point.

By default, the public version keeps the runtime disabled:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

This allows the Wokwi simulation and rule-based safety logic to remain understandable even when the Edge Impulse library is not installed.

To enable the exported Edge Impulse inference library, add the exported library to the project and change:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 1
```

The exported Edge Impulse package is stored in:

```text
edge-impulse/edge_impulse_kitchen_living_room_inferencing.zip
```

The current AI workflow should be understood as an embedded-AI prototype. The dataset is simulated and rule-labelled, so real-world validation would still be required before using the model in a safety-critical context.

---

## Dataset

The environmental training dataset was created for this project using simulated sensor readings from the Kitchen and Living Room module.

Dataset location:

```text
data/environmental_training_dataset.csv
```

The dataset contains simulated environmental readings and labels for the following safety states:

- NORMAL
- COOKING_FUMES
- GAS_DANGER
- HEAT_ANOMALY
- GAS_HEAT_EMERGENCY

The dataset does not contain personal data, private credentials or sensitive information.

---

## Project Report

The public portfolio report is available at:

```text
report/aiot_smart_home_public_report.pdf
```

This version has been sanitised for GitHub and portfolio publication. Academic submission material, personal identifiers, private credentials and sensitive submission-only content have been removed. Public Blynk screenshots and virtual-pin mapping figures are included where they help explain the system architecture and do not expose private tokens or personal data.

---

## Notes and Limitations

This is a simulation-based prototype. The gas detection thresholds, environmental classification logic and emergency responses are designed for demonstration and educational purposes.

Before any real-world deployment, the system would require:

- Real sensor calibration
- Hardware testing
- Electrical safety checks
- Secure credential management
- Reliability testing under real environmental conditions
- Validation using real sensor data
- Review of the emergency-response logic by qualified professionals

---

## Author

**Alberto Reyes Castro**  
Physics graduate and MSc Artificial Intelligence Technology student.
