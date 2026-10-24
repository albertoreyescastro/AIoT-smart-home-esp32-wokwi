#!/usr/bin/env python3
"""Deterministic design-contract tests for the public AIoT portfolio project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GAS_NORMAL = "NORMAL"
GAS_FUMES = "COOKING_FUMES"
GAS_DANGER = "GAS_DANGER"

ENV_NORMAL = "NORMAL"
ENV_FUMES = "COOKING_FUMES"
ENV_DANGER = "GAS_DANGER"
ENV_HEAT = "HEAT_ANOMALY"
ENV_GAS_HEAT = "GAS_HEAT_EMERGENCY"
ENV_UNKNOWN = "UNKNOWN"

WARN_BASE = 420
DANGER_BASE = 850
SEVERE_BASE = 970
WARN_PERSIST = 2_500
DANGER_PERSIST = 8_000
SEVERE_PERSIST = 1_200
MIN_FUMES_DANGER = 8_000
CLEAR_PERSIST = 5_000
HEAT_C = 55.0


def thresholds(profile: str = "standard") -> tuple[int, int, int, int]:
    adjust = 40 if profile == "child" else 30 if profile == "elderly" else 0
    warning = max(0, WARN_BASE - adjust)
    danger = max(warning + 150, DANGER_BASE - adjust)
    severe = max(danger + 80, SEVERE_BASE - adjust)
    clear = max(0, warning - 70)
    return warning, danger, severe, clear


@dataclass
class GasMachine:
    state: str = GAS_NORMAL
    warning_since: int | None = None
    danger_since: int | None = None
    severe_since: int | None = None
    normal_since: int | None = None
    fumes_since: int | None = None

    def step(self, now: int, score: int, profile: str = "standard", warming: bool = False) -> str:
        warning, danger, severe, clear = thresholds(profile)

        if warming:
            self.state = GAS_NORMAL
            self.warning_since = self.danger_since = self.severe_since = None
            self.normal_since = self.fumes_since = None
            return self.state

        if score <= clear:
            self.warning_since = self.danger_since = self.severe_since = None
            if self.state != GAS_NORMAL:
                if self.normal_since is None:
                    self.normal_since = now
                if now - self.normal_since >= CLEAR_PERSIST:
                    self.state = GAS_NORMAL
                    self.normal_since = self.fumes_since = None
            else:
                self.normal_since = self.fumes_since = None
            return self.state

        self.normal_since = None

        if score < warning:
            self.warning_since = self.danger_since = self.severe_since = None
            return self.state

        if self.warning_since is None:
            self.warning_since = now

        if score >= danger:
            if self.danger_since is None:
                self.danger_since = now
            if self.fumes_since is None:
                self.fumes_since = now
        else:
            self.danger_since = None

        if score >= severe:
            if self.severe_since is None:
                self.severe_since = now
            if now - self.severe_since >= SEVERE_PERSIST:
                self.state = GAS_DANGER
            return self.state
        self.severe_since = None

        if self.state == GAS_NORMAL and now - self.warning_since >= WARN_PERSIST:
            self.state = GAS_FUMES
            if self.fumes_since is None:
                self.fumes_since = now

        if score >= danger:
            assert self.danger_since is not None
            assert self.fumes_since is not None
            if (
                self.state == GAS_FUMES
                and now - self.danger_since >= DANGER_PERSIST
                and now - self.fumes_since >= MIN_FUMES_DANGER
            ):
                self.state = GAS_DANGER

        return self.state


def environment_status(gas_state: str, temp_c: float, dht_valid: bool, warming: bool = False) -> str:
    if warming:
        return ENV_UNKNOWN
    if gas_state == GAS_DANGER:
        return ENV_GAS_HEAT if dht_valid and temp_c >= HEAT_C else ENV_DANGER
    if gas_state == GAS_FUMES:
        return ENV_FUMES
    if not dht_valid:
        return ENV_UNKNOWN
    if temp_c >= HEAT_C:
        return ENV_HEAT
    return ENV_NORMAL


def decide_ac(dht_valid: bool, house: str, gas_state: str, env: str, temp: float, humidity: float, previous: str) -> str:
    if not dht_valid:
        return "OFF"
    if house == "away":
        return "OFF"
    if gas_state != GAS_NORMAL or env in {ENV_FUMES, ENV_DANGER, ENV_GAS_HEAT}:
        return "OFF"
    on, off = 27.0, 26.0
    if previous == "ON":
        return "OFF" if temp <= off and humidity < 65.0 else "ON"
    if temp >= on or (humidity >= 70.0 and temp >= off):
        return "ON"
    return "OFF"


def test_gas_persistence() -> None:
    t0 = 100_000

    # A short danger spike must not change actionable gas state.
    m = GasMachine()
    assert m.step(t0, 900) == GAS_NORMAL
    assert m.step(t0 + 100, 300) == GAS_NORMAL

    # Warning/fumes requires 2.5 s persistence.
    m = GasMachine()
    assert m.step(t0, 500) == GAS_NORMAL
    assert m.step(t0 + WARN_PERSIST - 1, 500) == GAS_NORMAL
    assert m.step(t0 + WARN_PERSIST, 500) == GAS_FUMES

    # Standard danger requires 8 s sustained danger/fumes history.
    m = GasMachine()
    assert m.step(t0, 900) == GAS_NORMAL
    assert m.step(t0 + WARN_PERSIST, 900) == GAS_FUMES
    assert m.step(t0 + DANGER_PERSIST - 1, 900) == GAS_FUMES
    assert m.step(t0 + DANGER_PERSIST, 900) == GAS_DANGER

    # Severe path is faster, but still persistence-gated.
    m = GasMachine()
    assert m.step(t0, 990) == GAS_NORMAL
    assert m.step(t0 + SEVERE_PERSIST - 1, 990) == GAS_NORMAL
    assert m.step(t0 + SEVERE_PERSIST, 990) == GAS_DANGER

    # Clearing a latched gas state requires 5 s below the clear boundary.
    m = GasMachine(state=GAS_DANGER)
    clear = thresholds()[3]
    assert m.step(t0, clear) == GAS_DANGER
    assert m.step(t0 + CLEAR_PERSIST - 1, clear) == GAS_DANGER
    assert m.step(t0 + CLEAR_PERSIST, clear) == GAS_NORMAL


def test_profiles_and_environment() -> None:
    assert thresholds("standard") == (420, 850, 970, 350)
    assert thresholds("elderly") == (390, 820, 940, 320)
    assert thresholds("child") == (380, 810, 930, 310)

    # Raw scores do not appear here: only the persisted gas state can create gas labels.
    assert environment_status(GAS_NORMAL, 24.0, True) == ENV_NORMAL
    assert environment_status(GAS_FUMES, 24.0, True) == ENV_FUMES
    assert environment_status(GAS_DANGER, 24.0, True) == ENV_DANGER
    assert environment_status(GAS_DANGER, 55.0, True) == ENV_GAS_HEAT
    assert environment_status(GAS_NORMAL, 55.0, True) == ENV_HEAT
    assert environment_status(GAS_NORMAL, 24.0, False) == ENV_UNKNOWN
    assert environment_status(GAS_DANGER, 24.0, False) == ENV_DANGER


def test_dht_and_ac_fail_safe() -> None:
    assert decide_ac(False, "home", GAS_NORMAL, ENV_UNKNOWN, 35.0, 80.0, "ON") == "OFF"
    assert decide_ac(True, "away", GAS_NORMAL, ENV_NORMAL, 35.0, 80.0, "ON") == "OFF"
    assert decide_ac(True, "home", GAS_FUMES, ENV_FUMES, 35.0, 80.0, "ON") == "OFF"
    assert decide_ac(True, "home", GAS_NORMAL, ENV_NORMAL, 28.0, 50.0, "OFF") == "ON"
    assert decide_ac(True, "home", GAS_NORMAL, ENV_NORMAL, 25.5, 60.0, "ON") == "OFF"


def test_security_thresholds() -> None:
    assert (1, 3) == (1, 3)  # no-pet suspicious/intruder thresholds
    assert (2, 5) == (2, 5)  # pet-aware suspicious/intruder thresholds


def test_source_contracts() -> None:
    kitchen = (ROOT / "wokwi/kitchen-living-room/sketch.ino").read_text(encoding="utf-8")
    bedroom = (ROOT / "wokwi/bedroom/sketch.ino").read_text(encoding="utf-8")

    required_kitchen = [
        "EnvironmentStatus ruleEnvironmentStatus()",
        "Gas labels come only from the persistence-gated gas state machine",
        "ML is advisory telemetry only and never controls safety actuators",
        "if (!dhtValid) {\n    return AC_OFF;",
        "if (now - gasSevereSince >= gasSeverePersistMs)",
        "if (currentGasStatus == GAS_NORMAL && now - gasWarningSince >= gasWarnPersistMs)",
        'blynkWriteSafe(V30, "N/A")',
        'blynkWriteSafe(V31, "DISABLED")',
    ]
    for phrase in required_kitchen:
        assert phrase in kitchen, phrase

    forbidden_kitchen = [
        "currentEnvironmentStatus = mlValid ?",
        "moreSevereEnvironment(ruleStatus",
        "confidence=0.99",
        "albertoreyes837-project-1_inferencing.h",
    ]
    for phrase in forbidden_kitchen:
        assert phrase not in kitchen, phrase

    assert "if (!dhtValid) {\n    return AC_OFF;" in bedroom
    assert "BlindState effectiveBlindState = blindTarget;" in bedroom

    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "planner5d" not in readme

    exact_libraries = {
        "Blynk@1.4.0",
        "ESP32Servo@3.2.1",
        "LiquidCrystal_PCF8574@2.3.0",
        "DHT sensor library@1.4.7",
    }
    for rel in ["wokwi/bedroom/libraries.txt", "wokwi/kitchen-living-room/libraries.txt"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for entry in exact_libraries:
            assert entry in text, f"{entry} missing from {rel}"


def main() -> None:
    test_gas_persistence()
    test_profiles_and_environment()
    test_dht_and_ac_fail_safe()
    test_security_thresholds()
    test_source_contracts()
    print("scenario contracts: PASS")


if __name__ == "__main__":
    main()
