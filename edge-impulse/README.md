# Edge Impulse / TinyML Integration

This folder documents the optional Edge Impulse experimentation path used for the Kitchen/Living Room environmental classifier.

The checked-in public simulation keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`. No ML inference runs by default. The deterministic, persistence-gated state machine controls safety actuators; an explicitly enabled model is advisory telemetry only.

## Generated package

A generated inferencing archive is **not present in the current public source tree**. Generated exports can include Edge Impulse runtime/SDK and other third-party material under licence terms separate from this repository's original MIT-licensed code/documentation. The public tree therefore documents regeneration instead of relying on that binary package.

## Historical evidence

- Training/test screenshots remain under `assets/`.
- Metrics supported by those screenshots are summarised in [`HISTORICAL_MODEL_CARD.md`](HISTORICAL_MODEL_CARD.md).
- Exact historical split, seed and training hyperparameters are not asserted because independently verifiable machine-readable configuration is not preserved.
- The historical hosted project/export is not claimed to be bit-for-bit reproducible from this repository alone.

## Equivalent deployment path

1. Create your own Edge Impulse project.
2. Import equivalent simulated sensor data.
3. Train and test the five-class classifier.
4. Export an Arduino/C++ inferencing library under the applicable terms.
5. Add the generated library to the build environment.
6. Set `EDGE_IMPULSE_INFERENCING_HEADER` to the generated header.
7. Set `USE_EDGE_IMPULSE_RUNTIME` to `1`.
8. Compile and validate on the intended target.

CI compiles this optional integration surface against `tests/edge_impulse_mock.h` so API drift is caught without redistributing a third-party generated model.

See [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md).
