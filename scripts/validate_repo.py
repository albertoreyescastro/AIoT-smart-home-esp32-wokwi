#!/usr/bin/env python3
"""Repository-level integrity checks for the public AIoT portfolio project.

The checks intentionally use only the Python standard library so they can run
locally and in GitHub Actions without extra dependencies.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "environmental_training_dataset.csv"
BEDROOM = ROOT / "wokwi" / "bedroom" / "sketch.ino"
KITCHEN = ROOT / "wokwi" / "kitchen-living-room" / "sketch.ino"

EXPECTED_COLUMNS = ["gas_score", "temperature", "humidity", "label"]
EXPECTED_CLASSES = {
    "NORMAL",
    "COOKING_FUMES",
    "GAS_DANGER",
    "HEAT_ANOMALY",
    "GAS_HEAT_EMERGENCY",
}

# These are the deterministic labelling boundaries used to create the
# synthetic demonstration dataset. They are not real-world safety limits.
GAS_FUMES_THRESHOLD = 420.0
GAS_DANGER_THRESHOLD = 850.0
HEAT_THRESHOLD_C = 55.0


def fail(message: str) -> None:
    raise AssertionError(message)


def expected_label(gas_score: float, temperature_c: float) -> str:
    if gas_score >= GAS_DANGER_THRESHOLD and temperature_c >= HEAT_THRESHOLD_C:
        return "GAS_HEAT_EMERGENCY"
    if gas_score >= GAS_DANGER_THRESHOLD:
        return "GAS_DANGER"
    if temperature_c >= HEAT_THRESHOLD_C:
        return "HEAT_ANOMALY"
    if gas_score >= GAS_FUMES_THRESHOLD:
        return "COOKING_FUMES"
    return "NORMAL"


def validate_dataset() -> None:
    if not DATASET.exists():
        fail(f"Missing dataset: {DATASET.relative_to(ROOT)}")

    counts: Counter[str] = Counter()
    mismatches: list[tuple[int, str, str]] = []

    with DATASET.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_COLUMNS:
            fail(f"Unexpected CSV columns: {reader.fieldnames!r}")

        rows = 0
        for line_number, row in enumerate(reader, start=2):
            rows += 1
            try:
                gas = float(row["gas_score"])
                temperature = float(row["temperature"])
                humidity = float(row["humidity"])
            except (TypeError, ValueError) as exc:
                fail(f"Non-numeric sensor value on CSV line {line_number}: {exc}")

            if not all(math.isfinite(v) for v in (gas, temperature, humidity)):
                fail(f"Non-finite value on CSV line {line_number}")
            if not 0 <= gas <= 1000:
                fail(f"gas_score out of range on CSV line {line_number}: {gas}")
            if not -40 <= temperature <= 125:
                fail(f"temperature out of DHT22 range on CSV line {line_number}: {temperature}")
            if not 0 <= humidity <= 100:
                fail(f"humidity out of range on CSV line {line_number}: {humidity}")

            label = row["label"].strip()
            if label not in EXPECTED_CLASSES:
                fail(f"Unexpected label on CSV line {line_number}: {label!r}")
            counts[label] += 1

            expected = expected_label(gas, temperature)
            if label != expected:
                mismatches.append((line_number, label, expected))

    if rows < 100:
        fail(f"Dataset unexpectedly small: {rows} rows")
    missing = EXPECTED_CLASSES - set(counts)
    if missing:
        fail(f"Dataset is missing classes: {sorted(missing)}")
    if mismatches:
        preview = ", ".join(
            f"line {line}: {actual}->{expected}"
            for line, actual, expected in mismatches[:8]
        )
        fail(
            "Synthetic labels no longer match the documented deterministic "
            f"generation rules ({len(mismatches)} mismatch(es)): {preview}"
        )

    print(f"dataset: PASS ({rows} rows; class counts={dict(sorted(counts.items()))})")


def validate_diagrams() -> None:
    for path in sorted((ROOT / "wokwi").glob("*/diagram.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            fail(f"Expected JSON object in {path.relative_to(ROOT)}")
        if not payload.get("parts"):
            fail(f"No Wokwi parts found in {path.relative_to(ROOT)}")
        print(f"diagram: PASS ({path.relative_to(ROOT)})")


def validate_public_sketches() -> None:
    required_placeholders = {
        '"YOUR_TEMPLATE_ID"',
        '"YOUR_BLYNK_AUTH_TOKEN"',
        '"Wokwi-GUEST"',
    }

    for path in (BEDROOM, KITCHEN):
        text = path.read_text(encoding="utf-8")
        for placeholder in required_placeholders:
            if placeholder not in text:
                fail(f"Expected public placeholder {placeholder} missing from {path.relative_to(ROOT)}")

        # Do not let obvious production-style secrets slip into the public code.
        suspicious_patterns = [
            re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
            re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
            re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
            re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
        ]
        for pattern in suspicious_patterns:
            if pattern.search(text):
                fail(f"Potential credential found in {path.relative_to(ROOT)}")

    kitchen_text = KITCHEN.read_text(encoding="utf-8")
    if "#define USE_EDGE_IMPULSE_RUNTIME 0" not in kitchen_text:
        fail("Public kitchen sketch must keep Edge Impulse runtime disabled by default")

    print("public sketches: PASS (placeholders present; no obvious token patterns)")


def validate_public_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    required_phrases = [
        "simulation-based",
        "rule-labelled",
        "not a production",
        "real-world validation",
    ]
    for phrase in required_phrases:
        if phrase not in readme:
            fail(f"README safety/limitations statement missing phrase: {phrase!r}")

    # The generated Edge Impulse archive contains third-party code and is not
    # needed to demonstrate the project. Keep the public repo source-focused.
    binary_export = ROOT / "edge-impulse" / "edge_impulse_kitchen_living_room_inferencing.zip"
    if binary_export.exists():
        fail(
            "Generated Edge Impulse ZIP is present. Keep third-party generated "
            "binaries out of the public source repository; document regeneration instead."
        )

    print("public surface: PASS")


def main() -> int:
    try:
        validate_dataset()
        validate_diagrams()
        validate_public_sketches()
        validate_public_surface()
    except (AssertionError, csv.Error, json.JSONDecodeError, OSError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1

    print("all repository checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
