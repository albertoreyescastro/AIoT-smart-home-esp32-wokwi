# Edge Impulse / TinyML Integration

This folder documents the optional Edge Impulse experimentation path used for the Kitchen/Living Room environmental classifier.

The public simulation is intentionally runnable without a generated inferencing package:

```cpp
#define USE_EDGE_IMPULSE_RUNTIME 0
```

With that default, **no ML inference is executed**. Environmental state is deterministic, ML confidence is unavailable, and the raw ML prediction is reported as disabled.

## Why the generated inferencing ZIP is not committed

Generated deployment archives can contain Edge Impulse runtime/SDK components and other third-party material under licence terms separate from this repository's original MIT-licensed code and documentation. The hardened public tree therefore documents regeneration instead of redistributing the historical generated ZIP.

## Historical evidence

- Training/test screenshots remain under `assets/`.
- The recorded historical configuration and metrics are summarised in [`HISTORICAL_MODEL_CARD.md`](HISTORICAL_MODEL_CARD.md).
- The historical hosted project/export is **not** claimed to be bit-for-bit reproducible from this repository alone.

## Reproducing an equivalent deployment path

1. Create or clone your own Edge Impulse project.
2. Import equivalent simulated sensor data.
3. Train and test the five-class classifier.
4. Export an Arduino/C++ inferencing library under the terms applicable to your project.
5. Add the generated library to your build environment.
6. In `wokwi/kitchen-living-room/sketch.ino`, change the generic `EDGE_IMPULSE_INFERENCING_HEADER` to the generated header name.
7. Set `USE_EDGE_IMPULSE_RUNTIME` to `1`.
8. Compile and validate on the intended target.

The deterministic rules remain the fallback if the model is unavailable, invalid or below the configured confidence threshold.

See [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md) for the full scope and caveats.
