# Edge Impulse Export

This folder contains the Edge Impulse inferencing export used for the Kitchen/Living Room environmental classification module.

The exported model supports the AI-inspired classification layer of the smart home system. It was designed to classify environmental conditions using simulated sensor readings such as gas level, temperature and humidity.

In the public Wokwi sketch, the Edge Impulse runtime is disabled by default to keep the simulation easy to run:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

To enable the real Edge Impulse runtime, the required inferencing library must be available and the value can be changed to:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 1
```

The rule-based safety logic remains available as a fallback for simulation and demonstration purposes.

The Edge Impulse export is included as a compressed file in this repository because GitHub web upload may not preserve the full exported folder structure easily.

## License Note

The exported Edge Impulse inferencing package may include third-party SDK components under their own licences. The repository MIT licence applies to the project code and documentation unless otherwise stated by the included exported library files.
