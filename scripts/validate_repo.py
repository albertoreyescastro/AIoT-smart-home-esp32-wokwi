#!/usr/bin/env python3
"""Repository-level integrity checks for the public AIoT portfolio project."""
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
QUALITY = ROOT / ".github" / "workflows" / "quality.yml"
REPORT = ROOT / "report" / "aiot_smart_home_public_report.pdf"

EXPECTED_COLUMNS = ["gas_score", "temperature", "humidity", "label"]
EXPECTED_CLASSES = {
    "NORMAL", "COOKING_FUMES", "GAS_DANGER", "HEAT_ANOMALY", "GAS_HEAT_EMERGENCY"
}

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
        preview = ", ".join(f"line {line}: {actual}->{expected}" for line, actual, expected in mismatches[:8])
        fail(f"Synthetic labels no longer match documented rules ({len(mismatches)} mismatch(es)): {preview}")
    print(f"dataset: PASS ({rows} rows; class counts={dict(sorted(counts.items()))})")


def validate_diagrams() -> None:
    for path in sorted((ROOT / "wokwi").glob("*/diagram.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict) or not payload.get("parts"):
            fail(f"Invalid/no Wokwi parts in {path.relative_to(ROOT)}")
        dht_parts = [p for p in payload["parts"] if p.get("type") == "wokwi-dht22"]
        if len(dht_parts) != 1:
            fail(f"Expected exactly one DHT22 in {path.relative_to(ROOT)}")
        attrs = dht_parts[0].get("attrs", {})
        temp = float(attrs.get("temperature", 24))
        humidity = float(attrs.get("humidity", 50))
        if not 18 <= temp <= 30 or not 20 <= humidity <= 80:
            fail(f"Public demo should start in a plausible room state: {path.relative_to(ROOT)}")
        text = json.dumps(payload)
        if "kitchen-living-room" in str(path) and "Sleep" in text:
            fail("Kitchen/Living diagram still advertises Sleep mode")
        print(f"diagram: PASS ({path.relative_to(ROOT)})")


def validate_public_sketches() -> None:
    required_placeholders = {'"YOUR_TEMPLATE_ID"', '"YOUR_BLYNK_AUTH_TOKEN"', '"Wokwi-GUEST"'}
    suspicious_patterns = [
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    ]
    for path in (BEDROOM, KITCHEN):
        text = path.read_text(encoding="utf-8")
        for placeholder in required_placeholders:
            if placeholder not in text:
                fail(f"Expected public placeholder {placeholder} missing from {path.relative_to(ROOT)}")
        if "#define ENABLE_BLYNK 0" not in text:
            fail(f"Public Blynk connection must be disabled by default in {path.relative_to(ROOT)}")
        if "LiquidCrystal_PCF8574" not in text or "LiquidCrystal_I2C" in text:
            fail(f"Expected ESP32-compatible PCF8574 LCD dependency in {path.relative_to(ROOT)}")
        for pattern in suspicious_patterns:
            if pattern.search(text):
                fail(f"Potential credential found in {path.relative_to(ROOT)}")

    kitchen = KITCHEN.read_text(encoding="utf-8")
    bedroom = BEDROOM.read_text(encoding="utf-8")
    if "#define USE_EDGE_IMPULSE_RUNTIME 0" not in kitchen:
        fail("Public kitchen sketch must keep Edge Impulse runtime disabled by default")
    if "albertoreyes837-project-1" in kitchen:
        fail("Personal Edge Impulse project identifier leaked into public sketch")
    if "0.99" in kitchen and "mlConfidence" in kitchen:
        fail("Public sketch must not fabricate ML confidence when runtime is disabled")
    for phrase in ("ML runtime disabled", 'blynkWriteSafe(V30, "N/A")', 'blynkWriteSafe(V31, "DISABLED")'):
        if phrase not in kitchen:
            fail(f"ML-disabled semantics missing from kitchen sketch: {phrase}")
    for phrase in ("OUTSIDE_SRC_WOKWI", "getUnifiedOutsideScore", "currentOutsideSource"):
        if phrase not in bedroom:
            fail(f"Bedroom outside-light source hardening missing: {phrase}")
    print("public sketches: PASS")


def validate_dependencies_and_ci() -> None:
    for path in (ROOT / "wokwi" / "bedroom" / "libraries.txt", ROOT / "wokwi" / "kitchen-living-room" / "libraries.txt"):
        text = path.read_text(encoding="utf-8")
        if "LiquidCrystal_PCF8574" not in text or "LiquidCrystal I2C" in text:
            fail(f"LCD library list not hardened: {path.relative_to(ROOT)}")
    quality = QUALITY.read_text(encoding="utf-8")
    required = [
        'version: "1.5.1"', "esp32:esp32@3.3.12", '"Blynk@1.4.0"',
        '"ESP32Servo@3.2.1"', '"LiquidCrystal_PCF8574@2.3.0"',
        '"DHT sensor library@1.4.7"', "python scripts/test_scenarios.py",
        "reportlab==5.1.0", "git diff --exit-code -- report/aiot_smart_home_public_report.pdf",
    ]
    for token in required:
        if token not in quality:
            fail(f"Pinned/reproducible CI token missing: {token}")
    print("dependencies/CI: PASS")


def validate_public_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for phrase in ["simulation-based", "rule-labelled", "not a production", "real-world validation", "disabled by default"]:
        if phrase not in readme:
            fail(f"README public-scope phrase missing: {phrase!r}")
    kitchen_readme = (ROOT / "wokwi" / "kitchen-living-room" / "README.md").read_text(encoding="utf-8")
    if "exported inference package is stored in the repository" in kitchen_readme:
        fail("Kitchen README still claims the generated inference package is checked in")
    if not (ROOT / "edge-impulse" / "HISTORICAL_MODEL_CARD.md").exists():
        fail("Historical Edge Impulse model card missing")
    binary_export = ROOT / "edge-impulse" / "edge_impulse_kitchen_living_room_inferencing.zip"
    if binary_export.exists():
        fail("Generated Edge Impulse ZIP must stay out of the public source tree")
    if not REPORT.exists() or REPORT.stat().st_size > 1_000_000:
        fail("Public report missing or unexpectedly large; regenerate the concise hardened report")
    print("public surface: PASS")


def main() -> int:
    try:
        validate_dataset()
        validate_diagrams()
        validate_public_sketches()
        validate_dependencies_and_ci()
        validate_public_surface()
    except (AssertionError, csv.Error, json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    print("all repository checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
