#!/usr/bin/env python3
"""Repository-level integrity checks for the public AIoT portfolio project."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def validate_dataset() -> None:
    path = ROOT / "data/environmental_training_dataset.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if len(rows) != 616:
        fail(f"dataset row count changed: {len(rows)} != 616")
    expected_cols = {"gas_score", "temperature", "humidity", "label"}
    if set(rows[0]) != expected_cols:
        fail(f"dataset columns changed: {set(rows[0])}")

    counts = Counter(row["label"] for row in rows)
    expected_labels = {"NORMAL", "COOKING_FUMES", "GAS_DANGER", "HEAT_ANOMALY", "GAS_HEAT_EMERGENCY"}
    if set(counts) != expected_labels:
        fail(f"dataset labels changed: {set(counts)}")

    for row in rows:
        gas = int(float(row["gas_score"]))
        temp = float(row["temperature"])
        expected = (
            "GAS_HEAT_EMERGENCY" if gas >= 850 and temp >= 55
            else "GAS_DANGER" if gas >= 850
            else "HEAT_ANOMALY" if temp >= 55
            else "COOKING_FUMES" if gas >= 420
            else "NORMAL"
        )
        if row["label"] != expected:
            fail(f"dataset label contract mismatch: {row}")
    print(f"dataset: PASS ({len(rows)} rows; class counts={dict(counts)})")


def validate_diagram(rel: str, required_esp_pins: set[int]) -> None:
    data = json.loads(text(rel))
    ids = [part.get("id") for part in data.get("parts", [])]
    if len(ids) != len(set(ids)):
        fail(f"duplicate part id in {rel}")

    connected_pins: set[int] = set()
    for conn in data.get("connections", []):
        if len(conn) < 2:
            fail(f"malformed connection in {rel}: {conn}")
        for endpoint in conn[:2]:
            m = re.fullmatch(r"esp:(\d+)", endpoint)
            if m:
                connected_pins.add(int(m.group(1)))

    missing = required_esp_pins - connected_pins
    if missing:
        fail(f"{rel}: code pins missing from diagram connections: {sorted(missing)}")
    print(f"diagram: PASS ({rel})")


def validate_public_sketches() -> None:
    paths = [ROOT / "wokwi/bedroom/sketch.ino", ROOT / "wokwi/kitchen-living-room/sketch.ino"]
    suspicious = [
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"BLYNK_AUTH_TOKEN\s+\"(?!YOUR_BLYNK_AUTH_TOKEN)[^\"]+\""),
        re.compile(r"BLYNK_TEMPLATE_ID\s+\"(?!YOUR_TEMPLATE_ID)[^\"]+\""),
    ]

    for path in paths:
        src = path.read_text(encoding="utf-8")
        for required in ['"YOUR_TEMPLATE_ID"', '"YOUR_BLYNK_AUTH_TOKEN"', '"Wokwi-GUEST"', "#define ENABLE_BLYNK 0"]:
            if required not in src:
                fail(f"{path}: required public placeholder/default missing: {required}")
        for pattern in suspicious:
            if pattern.search(src):
                fail(f"{path}: suspicious credential pattern: {pattern.pattern}")

    kitchen = paths[1].read_text(encoding="utf-8")
    for required in [
        "#define USE_EDGE_IMPULSE_RUNTIME 0",
        'blynkWriteSafe(V30, "N/A")',
        'blynkWriteSafe(V31, "DISABLED")',
        "EnvironmentStatus ruleEnvironmentStatus()",
        "ML is advisory telemetry only and never controls safety actuators",
        "if (!dhtValid) {\n    return AC_OFF;",
    ]:
        if required not in kitchen:
            fail(f"kitchen hardened semantic missing: {required}")

    for forbidden in ["confidence=0.99", "albertoreyes837-project-1_inferencing.h", "currentEnvironmentStatus = mlValid ?"]:
        if forbidden in kitchen:
            fail(f"kitchen stale/unsafe semantic present: {forbidden}")

    bedroom = paths[0].read_text(encoding="utf-8")
    if "if (!dhtValid) {\n    return AC_OFF;" not in bedroom:
        fail("bedroom DHT fail-safe missing")
    if "BlindState effectiveBlindState = blindTarget;" not in bedroom:
        fail("bedroom blind/daylight state is not cycle-consistent")

    print("public sketches: PASS")


def validate_dependencies_and_ci() -> None:
    exact = ["Blynk@1.4.0", "ESP32Servo@3.2.1", "LiquidCrystal_PCF8574@2.3.0", "DHT sensor library@1.4.7"]
    for rel in ["wokwi/bedroom/libraries.txt", "wokwi/kitchen-living-room/libraries.txt"]:
        lib = text(rel)
        for dep in exact:
            if dep not in lib:
                fail(f"{rel}: dependency is not pinned to CI version: {dep}")

    workflow = text(".github/workflows/quality.yml")
    required = [
        'version: "1.5.1"',
        "esp32:esp32@3.3.12",
        '"Blynk@1.4.0"',
        '"ESP32Servo@3.2.1"',
        '"LiquidCrystal_PCF8574@2.3.0"',
        '"DHT sensor library@1.4.7"',
        "Compile optional Edge Impulse integration surface",
    ]
    for item in required:
        if item not in workflow:
            fail(f"CI pin/coverage missing: {item}")
    if "hardening-v2-aiot-20261023" in workflow:
        fail("stale CI branch trigger remains")
    print("dependencies/CI: PASS")


def validate_public_surface() -> None:
    markdown_files = list(ROOT.rglob("*.md"))
    joined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in markdown_files)
    lower = joined.lower()

    if "planner5d" in lower:
        fail("Planner 5D link/reference remains in public markdown")

    stale_claims = [
        "historical training configuration and results",
        "documented dataset/configuration",
        "100 training cycles",
        "learning rate: `0.0005`",
        "training accuracy | ~93.4%",
    ]
    for phrase in stale_claims:
        if phrase.lower() in lower:
            fail(f"stale historical-ML claim remains: {phrase}")

    if (ROOT / "edge-impulse/edge_impulse_kitchen_living_room_inferencing.zip").exists():
        fail("generated Edge Impulse ZIP must not be present in the current source tree")

    if not (ROOT / "report/aiot_smart_home_public_report.pdf").exists():
        fail("public report missing")

    print("public surface: PASS")


def main() -> None:
    validate_dataset()
    validate_diagram("wokwi/bedroom/diagram.json", {2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18})
    validate_diagram("wokwi/kitchen-living-room/diagram.json", {1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18})
    validate_public_sketches()
    validate_dependencies_and_ci()
    validate_public_surface()
    print("all repository checks: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise
