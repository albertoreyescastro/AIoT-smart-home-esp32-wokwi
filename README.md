# AIoT Smart Home Simulation with ESP32-S3, Wokwi and Blynk

This repository presents a modular AIoT smart home simulation based on ESP32-S3 room controllers. The project combines embedded systems, sensor-based automation, rule-based decision logic, Blynk dashboard interaction and an optional Edge Impulse-inspired environmental classification layer.

The system is divided into two main room-level modules:

- **Bedroom Module**: adaptive lighting, privacy-aware blind control, motion detection, sleep/privacy/eco modes, user profiles and home security logic.
- **Kitchen and Living Room Module**: gas safety monitoring, temperature and humidity sensing, emergency response, Blynk dashboard interaction and optional Edge Impulse integration.

The project was developed as a simulation-based prototype using Wokwi and Arduino/C++.

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

## Repository Structure

```text
aiot-smart-home-esp32-wokwi/
├── README.md
├── LICENSE
├── .gitignore
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

## Technologies Used

- ESP32-S3
- Wokwi
- Arduino/C++
- Blynk IoT
- Edge Impulse
- TinyML / embedded AI workflow
- DHT22 temperature and humidity sensor
- MQ2 gas sensor
- PIR motion sensor
- LDR light sensors
- Servo motor
- LCD I2C display
- Buzzer and LED indicators

## Modules

### Bedroom Module

The Bedroom module focuses on comfort, privacy and user-centred automation. It includes adaptive lighting, blind control, motion-based presence detection, temperature monitoring, AC control, child mode, elderly profile logic and Away mode security behaviour.

Folder:

```text
wokwi/bedroom/
```

### Kitchen and Living Room Module

The Kitchen and Living Room module focuses on environmental safety and emergency response. It includes gas detection, temperature and humidity monitoring, buzzer alerts, sprinkler/emergency-cooling indication, Blynk dashboard interaction and an optional Edge Impulse runtime integration.

Folder:

```text
wokwi/kitchen-living-room/
```

## Blynk Configuration

The public version of the code uses placeholder credentials:

```cpp
#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"
```

To run the project with Blynk, replace these placeholders with your own Blynk template ID and authentication token.

Do not publish real Blynk tokens or private credentials in a public repository.

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

## Project Report

The public portfolio report is available at:

```text
report/aiot_smart_home_public_report.pdf
```

This version has been sanitised for GitHub and portfolio publication. Academic submission material, personal identifiers, private links, dashboard screenshots and detailed virtual-pin mapping figures have been removed.

## Notes and Limitations

This is a simulation-based prototype. The gas detection thresholds, environmental classification logic and emergency responses are designed for demonstration and educational purposes.

Before any real-world deployment, the system would require:

- Real sensor calibration
- Hardware testing
- Electrical safety checks
- Secure credential management
- Reliability testing under real environmental conditions
- Validation using real sensor data

## Author

Alberto Reyes Castro  
Physics graduate and MSc Artificial Intelligence Technology candidate.
