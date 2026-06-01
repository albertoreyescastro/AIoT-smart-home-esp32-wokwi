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
- Clear dashboard feedback through Blynk
- Modular room-level smart home design

## Repository Structure

```text
aiot-smart-home-esp32-wokwi/
├── README.md
├── wokwi/
│   ├── bedroom/
│   │   ├── README.md
│   │   ├── sketch.ino
│   │   ├── diagram.json
│   │   └── libraries.txt
│   └── kitchen-living-room/
│       ├── README.md
│       ├── sketch.ino
│       ├── diagram.json
│       └── libraries.txt
├── edge-impulse/
├── data/
├── figures/
└── report/
```

## Technologies Used

- ESP32-S3
- Wokwi
- Arduino/C++
- Blynk IoT
- Edge Impulse-inspired classification workflow
- DHT22 temperature and humidity sensor
- MQ2 gas sensor
- PIR motion sensor
- LDR light sensors
- Servo motor
- LCD I2C display
- Buzzer and LED indicators

## Modules

### Bedroom Module

The bedroom module focuses on comfort, privacy and user-centred automation. It includes adaptive lighting, blind control, motion-based presence detection, temperature monitoring, AC control, child mode, elderly profile logic and Away mode security behaviour.

Folder:

```text
wokwi/bedroom/
```

### Kitchen and Living Room Module

The kitchen and living room module focuses on environmental safety and emergency response. It includes gas detection, temperature and humidity monitoring, buzzer alerts, sprinkler indication, Blynk dashboard interaction and an optional Edge Impulse runtime integration.

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

The kitchen and living room module includes an optional Edge Impulse integration point.

By default, the public version keeps the runtime disabled:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

This allows the Wokwi simulation and rule-based safety logic to remain understandable even when the Edge Impulse library is not installed.

To enable the exported Edge Impulse inference library, place the exported library in the appropriate folder and change:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 1
```

## Data

The environmental training dataset was created for this project using simulated sensor readings. It can be stored in:

```text
data/environmental_training_dataset.csv
```

The dataset should not contain personal data, private credentials or sensitive information.

## Project Report

A technical report can be added in the following folder:

```text
report/
```

Recommended file name:

```text
aiot_smart_home_project_summary.pdf
```

## Notes and Limitations

This is a simulation-based prototype. The gas detection thresholds, environmental classification logic and emergency responses are designed for demonstration and educational purposes.

Before any real-world deployment, the system would require:

- Real sensor calibration
- Hardware testing
- Electrical safety checks
- Secure credential management
- Reliability testing under real environmental conditions

## Author

Alberto Reyes Castro  
Physics graduate and MSc Artificial Intelligence Technology candidate.
