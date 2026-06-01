# Kitchen and Living Room Module

This folder contains the Wokwi simulation files for the Kitchen and Living Room module of the AIoT Smart Home system.

The Kitchen and Living Room module focuses on environmental safety, gas monitoring, emergency response, Blynk interaction and optional Edge Impulse integration. It is designed as a room-level ESP32-S3 controller with local rule-based safety logic and an AI-inspired environmental classification layer.

## Files

```text
kitchen-living-room/
├── README.md
├── sketch.ino
├── diagram.json
└── libraries.txt
```

## Live Simulation

The Kitchen and Living Room module can be opened directly in Wokwi:

[Open Kitchen and Living Room Wokwi simulation](https://wokwi.com/projects/465661368262601729)

## Main Features

- ESP32-S3 based Wokwi simulation
- MQ2 gas sensor monitoring
- DHT22 temperature and humidity sensing
- PIR motion detection
- Indoor and outdoor light sensing
- Servo-based blind control
- Manual main lamp control
- AC relay simulation
- Emergency buzzer alerts
- Sprinkler or emergency-cooling LED simulation
- LCD I2C feedback
- Blynk dashboard interaction
- Normal, Privacy and Eco room modes
- Standard, Elderly and Child profile logic
- Home/Away security state
- Pet-aware Away mode
- Hybrid rule-based and AI-inspired environmental safety classification
- Optional Edge Impulse runtime integration

## Behaviour Overview

The Kitchen and Living Room module monitors environmental conditions and classifies the safety state of the room.

The system can distinguish between:

- Normal conditions
- Cooking fumes
- Dangerous gas levels
- Heat anomaly
- Combined gas and heat emergency

The module uses staged escalation so that safety responses are not based on a single instant reading. This makes the system more realistic for a domestic kitchen/living room environment, where harmless cooking fumes and dangerous gas-related events may appear similar to a low-cost gas sensor.

## Edge Impulse Integration

The public version keeps the Edge Impulse runtime disabled by default:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

This allows the Wokwi simulation to remain understandable and usable even when the exported Edge Impulse library is not installed.

To enable the exported Edge Impulse inference library, add the library to the project and change:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 1
```

The exported inference package is stored in the repository under:

```text
edge-impulse/
```

## Dataset

The environmental dataset used for the classification workflow was created for this project using simulated sensor readings.

Recommended location:

```text
data/environmental_training_dataset.csv
```

The dataset should not include personal data, private credentials or sensitive information.

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

## Safety Notes

This module is a simulation-based prototype. The gas thresholds, emergency logic and AI-inspired classifications are designed for demonstration and portfolio purposes.

For real-world use, the system would require:

- Physical sensor calibration
- Real hardware testing
- Electrical safety validation
- Reliable alarm mechanisms
- Fail-safe design
- Secure credential management
- Validation with real environmental data

## Running the Simulation

To run this module:

1. Open the Kitchen and Living Room Wokwi project.
2. Make sure `sketch.ino`, `diagram.json` and `libraries.txt` are present.
3. Replace Blynk placeholders with your own credentials if dashboard connectivity is required.
4. Start the simulation.
5. Use the Serial Monitor, Blynk dashboard and simulated sensors to test gas, temperature, humidity, motion and safety responses.

## Limitations

The current dataset is simulated and rule-labelled. The Edge Impulse model should therefore be treated as an initial embedded AI prototype, not as a certified safety system. Deterministic rule-based safety logic remains important as a fallback.
