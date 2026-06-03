<p align="center">
  <img src="assets/aiot-smart-home-logo.png" alt="AIoT Smart Home ESP32-S3" width="420"/>
</p>

<h1 align="center">AIoT Smart Home ESP32-S3</h1>

<p align="center">
  ESP32-S3 smart home simulation combining Wokwi, Blynk, rule-based automation and an Edge Impulse / TinyML environmental safety workflow.
</p>

<p align="center">
  <a href="https://wokwi.com/projects/465661521735358465">Bedroom Wokwi Demo</a> ·
  <a href="https://wokwi.com/projects/465661368262601729">Kitchen/Living Room Wokwi Demo</a> ·
  <a href="report/aiot_smart_home_public_report.pdf">Technical Report</a> ·
  <a href="https://planner5d.onelink.me/stDT/wjmc3u8i">2D/3D House Model</a>
</p>

---

## Overview

This repository presents a simulation-based **AIoT smart home prototype** built around ESP32-S3 room controllers.

The project combines:

- Embedded systems programming with Arduino/C++
- Sensor-based automation using simulated hardware
- Local rule-based decision logic
- Blynk IoT dashboard interaction
- Environmental safety monitoring
- A simulated Edge Impulse / TinyML workflow
- Technical documentation, visual assets and a public project report

The system is divided into two main room-level modules:

| Module | Purpose |
|---|---|
| **Bedroom** | Adaptive lighting, privacy-aware blind control, user profiles, comfort logic and Home/Away security behaviour |
| **Kitchen/Living Room** | Gas detection, environmental monitoring, emergency response, Blynk interaction and AI-inspired classification |

This project was developed as an academic and portfolio prototype to demonstrate how embedded IoT, automation logic and AI-assisted environmental classification can be combined in a modular smart home architecture.

---

## Recruiter Snapshot

This project demonstrates practical work across embedded systems, IoT simulation, software architecture and AI workflow design.

Key points:

- Built two separate ESP32-S3 Wokwi simulations with complete room-level logic.
- Implemented sensor-driven automation using PIR, LDR, DHT22 and MQ2 inputs.
- Designed comfort, privacy, security and safety behaviours using deterministic control logic.
- Integrated Blynk virtual pins for dashboard monitoring and remote interaction.
- Created a simulated environmental dataset for Edge Impulse classification.
- Exported an Edge Impulse inference package for embedded-AI experimentation.
- Documented the full design through diagrams, screenshots, datasets and a public technical report.
- Kept public credentials sanitised using placeholders instead of real tokens.

---

## Quick Demo

| Component | Link | Description |
|---|---|---|
| Bedroom Simulation | [Open in Wokwi](https://wokwi.com/projects/465661521735358465) | Adaptive lighting, privacy-aware blinds, user profiles and Away-mode security |
| Kitchen/Living Room Simulation | [Open in Wokwi](https://wokwi.com/projects/465661368262601729) | Gas monitoring, thermal logic, emergency response and Blynk interaction |
| 2D/3D House Model | [Open Planner 5D model](https://planner5d.onelink.me/stDT/wjmc3u8i) | Visual smart home layout and room distribution |
| Technical Report | [Open PDF report](report/aiot_smart_home_public_report.pdf) | Public project report with design, implementation, evaluation and limitations |

> The Planner 5D model is best opened on a laptop or desktop browser. On mobile devices, Planner 5D may request the app.

---

## What Makes This Project Different?

This is not only a basic sensor demo. The project combines multiple layers of smart home behaviour into a single AIoT simulation:

- **Room-level intelligence:** each room has its own ESP32-S3 controller, sensor set and local decision logic.
- **Hybrid automation:** deterministic rules handle safety-critical behaviours, while the AI workflow supports environmental classification.
- **User-aware control:** the system adapts to Standard, Elderly and Child profiles.
- **Privacy-aware behaviour:** blind control and lighting decisions consider privacy, sleep and occupancy states.
- **Safety escalation:** gas, heat and intrusion scenarios trigger different alert and emergency responses.
- **Cloud-assisted monitoring:** Blynk is used for dashboard interaction while core logic remains local.
- **Portfolio-ready documentation:** the repository includes code, diagrams, datasets, Wokwi simulations, AI export material and a technical report.

---

## Visual Overview

### System Layout

<p align="center">
  <img src="assets/system-layout.png" alt="AIoT smart home system layout" width="100%"/>
</p>

### Simulation Screenshots

| Kitchen/Living Room Simulation | Bedroom Intruder Alert Demo |
|---|---|
| <img src="assets/kitchen-wokwi-serial.png" alt="Kitchen and living room Wokwi simulation and Serial Monitor"/> | <img src="assets/intruder-alert-demo.png" alt="Bedroom intruder alert scenario in Wokwi"/> |

### Edge Impulse Results

| Test Results | On-Device Performance |
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

The objective of this project is to design and simulate a smart home prototype capable of responding to environmental conditions, user preferences and safety risks in real time.

The system focuses on:

- Adaptive lighting control
- Privacy-aware blind automation
- Energy-conscious behaviour
- Gas and environmental safety monitoring
- Profile-based user adaptation
- Home/Away security behaviour
- Remote dashboard monitoring through Blynk
- Modular room-level smart home design
- Embedded AI / TinyML workflow experimentation

---

## System Architecture

The project follows a modular room-controller architecture.

```text
Smart Home System
│
├── Bedroom Controller
│   ├── LDR sensors
│   ├── PIR motion sensor
│   ├── DHT22 temperature/humidity sensor
│   ├── Servo-controlled blinds
│   ├── PWM lighting
│   ├── LCD display
│   └── Security and profile logic
│
└── Kitchen/Living Room Controller
    ├── MQ2 gas sensor
    ├── DHT22 temperature/humidity sensor
    ├── PIR motion sensor
    ├── Buzzer and alert outputs
    ├── Emergency cooling indicator
    ├── Blynk dashboard integration
    └── Edge Impulse / TinyML workflow
```

The system separates comfort automation, privacy behaviour, security logic and environmental safety into different functional areas. This makes the project easier to extend with real hardware or additional rooms in the future.

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
| Documentation | Markdown, PDF report, diagrams and screenshots |

---

## Modules

### Bedroom Module

Folder:

```text
wokwi/bedroom/
```

The Bedroom module focuses on comfort, privacy and user-centred automation.

Main behaviours:

- Normal, Sleep, Privacy and Eco room modes
- Standard, Elderly and Child user profiles
- Adaptive lighting based on indoor and outdoor brightness
- Servo-controlled blinds for light and privacy management
- PIR-based occupancy detection
- Temperature and humidity monitoring
- AC relay control for thermal comfort
- Home/Away security state
- Intruder-alert escalation and authenticated recovery

Example scenarios:

- If the room is dark and motion is detected, the light can turn on automatically.
- If Privacy mode is active, blinds are prioritised even when natural light is available.
- If Away mode is active and motion is detected, the system escalates to a security alert.
- If Child mode is active, deactivation requires controlled user input.

---

### Kitchen and Living Room Module

Folder:

```text
wokwi/kitchen-living-room/
```

The Kitchen and Living Room module focuses on environmental safety, gas monitoring and emergency response.

Main behaviours:

- Normal, Privacy and Eco room modes
- MQ2-based gas monitoring
- DHT22 temperature and humidity sensing
- Gas warning and danger states
- Emergency response for gas and heat events
- Buzzer and visual alert outputs
- Blynk dashboard monitoring
- Optional Edge Impulse-inspired environmental classification

Example scenarios:

- If gas levels rise slightly, the system classifies the situation as a warning.
- If gas levels remain high, the system escalates to a danger state.
- If high gas and high temperature occur together, the system triggers an emergency response.
- Blynk virtual pins allow the simulated environment to be monitored remotely.

---

## Blynk Configuration

The public version of the code uses placeholder credentials:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_TEMPLATE_NAME "YOUR_TEMPLATE_NAME"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
```

To run the project with Blynk:

1. Create a Blynk account.
2. Create a new Blynk template.
3. Copy your template ID, template name and authentication token.
4. Replace the placeholder values in the relevant sketch.
5. Run the simulation in Wokwi.

Do not publish real Blynk tokens, Wi-Fi credentials or private API keys in a public repository.

The public report and screenshots may include dashboard views or virtual-pin mapping where they help explain the system architecture. These materials are only included when they do not expose private tokens, credentials or personal data.

---

## Security and Demo Authentication Notes

The project includes child-mode protection, Away-to-Home authentication and intruder-alert clearing logic.

Any authentication PINs, secret words or command values visible in the public code are **demonstration values for simulation purposes only**. They should not be reused in a real deployment.

For a real system, these values should be moved to:

- secure configuration files,
- environment variables,
- a private secrets manager,
- or a hardware-backed secure storage solution.

Only placeholders should remain in a public repository.

---

## Edge Impulse / TinyML Workflow

The Kitchen and Living Room module includes an optional Edge Impulse integration point.

By default, the public version keeps the Edge Impulse runtime disabled:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

This allows the Wokwi simulation and rule-based safety logic to remain understandable and runnable even when the exported Edge Impulse library is not installed.

To enable the exported Edge Impulse inference library:

1. Download or extract the exported Edge Impulse Arduino library.
2. Add it to the Arduino/Wokwi project.
3. Change the runtime flag:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 1
```

The exported Edge Impulse package is stored in:

```text
edge-impulse/edge_impulse_kitchen_living_room_inferencing.zip
```

Important note:

The current AI workflow should be understood as an **embedded-AI prototype**. The dataset is simulated and rule-labelled, so real-world validation would still be required before using the model in any safety-critical application.

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

## How to Run the Simulations

### Bedroom

1. Open the Bedroom Wokwi demo:

   [Bedroom Wokwi Demo](https://wokwi.com/projects/465661521735358465)

2. Start the simulation.

3. Use the simulated sensors and Serial Monitor commands to test:

   - room modes,
   - occupancy,
   - lighting behaviour,
   - blind control,
   - child mode,
   - Away mode,
   - intruder-alert recovery.

---

### Kitchen/Living Room

1. Open the Kitchen/Living Room Wokwi demo:

   [Kitchen/Living Room Wokwi Demo](https://wokwi.com/projects/465661368262601729)

2. Start the simulation.

3. Adjust the simulated gas, temperature and motion inputs.

4. Observe:

   - gas state classification,
   - buzzer behaviour,
   - emergency cooling indicator,
   - LCD output,
   - Blynk dashboard values,
   - Serial Monitor logs.

---

## Project Report

The public portfolio report is available at:

```text
report/aiot_smart_home_public_report.pdf
```

This version has been sanitised for GitHub and portfolio publication.

Removed or sanitised content includes:

- academic submission-only material,
- private credentials,
- personal identifiers,
- sensitive configuration values,
- non-public tokens or API keys.

The report keeps the design explanation, architecture, implementation details, evaluation, screenshots and limitations required to understand the project.

---

## Skills Demonstrated

This project demonstrates experience with:

- Embedded C++ / Arduino programming
- ESP32-S3 simulation
- IoT sensor and actuator logic
- Wokwi project design
- Blynk dashboard integration
- Local rule-based automation
- Safety-state modelling
- Edge Impulse / TinyML workflow experimentation
- Dataset creation for simulated sensor data
- Technical documentation
- GitHub portfolio presentation

---

## Limitations

This project is a simulation-based prototype. It should not be treated as a production-ready smart home safety system.

Current limitations:

- Sensor readings are simulated.
- The gas detection thresholds are demonstration values.
- The Edge Impulse dataset is simulated and rule-labelled.
- The AI workflow demonstrates methodology, not real-world safety validation.
- Real hardware testing has not been included in this public version.
- Emergency-response logic would require professional review before deployment.
- Authentication values in the demo are not suitable for real devices.

---

## Future Improvements

Possible next steps:

- Refactor the large Arduino sketches into smaller C++ modules.
- Add real ESP32-S3 hardware testing.
- Calibrate MQ2, DHT22, PIR and LDR sensors using real measurements.
- Replace simulated data with real environmental sensor logs.
- Add automated build checks for Arduino sketches.
- Add a more complete Blynk setup guide with virtual-pin mapping.
- Improve authentication using secure configuration handling.
- Extend the system with more rooms and shared home-level coordination.
- Compare rule-based classification with a validated TinyML model trained on real data.

---

## License

This repository is provided for educational and portfolio purposes.

See the `LICENSE` file for details.

---

## Author

**Alberto Reyes Castro**  
Physics graduate and MSc Artificial Intelligence Technology student.

Portfolio focus:

- Artificial Intelligence
- IoT and AIoT systems
- Embedded AI / TinyML
- Scientific computing
- Data-driven automation
- Technical documentation
