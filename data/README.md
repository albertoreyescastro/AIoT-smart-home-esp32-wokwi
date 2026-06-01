# Environmental Safety Dataset

This folder contains the simulated environmental dataset created for the Kitchen/Living Room smart home module.

The dataset was developed for this project and supports the Edge Impulse environmental classification workflow. It includes three input features:

- `gas_score`: simulated MQ2 gas score from 0 to 1000
- `temperature`: simulated DHT22 temperature in degrees Celsius
- `humidity`: simulated DHT22 humidity percentage

The target column is:

- `label`: environmental safety class

The dataset includes five classes:

- `NORMAL`
- `COOKING_FUMES`
- `GAS_DANGER`
- `HEAT_ANOMALY`
- `GAS_HEAT_EMERGENCY`

The dataset is simulated, project-specific and created for demonstration, documentation and portfolio purposes. It does not contain personal data or real household monitoring data.
