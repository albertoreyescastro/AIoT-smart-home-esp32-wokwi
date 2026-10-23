#!/usr/bin/env python3
"""Deterministic design-contract tests for the public AIoT prototype.

These tests complement, rather than replace, ESP32 compilation and real runtime/
hardware testing. They lock the documented synthetic environmental boundaries,
severity ordering and profile-sensitive gas-threshold contract used by the demo.
"""
from __future__ import annotations


def label(gas: float, temp: float) -> str:
    if gas >= 850 and temp >= 55:
        return "GAS_HEAT_EMERGENCY"
    if gas >= 850:
        return "GAS_DANGER"
    if temp >= 55:
        return "HEAT_ANOMALY"
    if gas >= 420:
        return "COOKING_FUMES"
    return "NORMAL"


def gas_thresholds(profile: str) -> tuple[int, int, int, int]:
    adjust = {"standard": 0, "elderly": 30, "child": 40}[profile]
    warning = max(0, 420 - adjust)
    danger = max(warning + 150, 850 - adjust)
    severe = max(danger + 80, 970 - adjust)
    clear = max(0, warning - 70)
    return clear, warning, danger, severe


def main() -> int:
    cases = [
        (0, 24, "NORMAL"),
        (419.99, 54.99, "NORMAL"),
        (420, 24, "COOKING_FUMES"),
        (849.99, 54.99, "COOKING_FUMES"),
        (850, 24, "GAS_DANGER"),
        (0, 55, "HEAT_ANOMALY"),
        (849.99, 55, "HEAT_ANOMALY"),
        (850, 55, "GAS_HEAT_EMERGENCY"),
        (1000, 125, "GAS_HEAT_EMERGENCY"),
    ]
    for gas, temp, expected in cases:
        actual = label(gas, temp)
        assert actual == expected, (gas, temp, actual, expected)

    severity = {
        "NORMAL": 1,
        "COOKING_FUMES": 2,
        "HEAT_ANOMALY": 3,
        "GAS_DANGER": 4,
        "GAS_HEAT_EMERGENCY": 5,
    }
    assert all(severity[a] < severity[b] for a, b in zip(
        ["NORMAL", "COOKING_FUMES", "HEAT_ANOMALY", "GAS_DANGER"],
        ["COOKING_FUMES", "HEAT_ANOMALY", "GAS_DANGER", "GAS_HEAT_EMERGENCY"],
    ))

    standard = gas_thresholds("standard")
    elderly = gas_thresholds("elderly")
    child = gas_thresholds("child")
    assert standard == (350, 420, 850, 970)
    assert elderly == (320, 390, 820, 940)
    assert child == (310, 380, 810, 930)
    assert child[1] < elderly[1] < standard[1]

    print("scenario contracts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
