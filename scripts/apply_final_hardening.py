#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    out, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 regex match, found {count}")
    return out


# ---------------------------------------------------------------------------
# Kitchen/Living Room sketch: persistence-gated actions + DHT fail-safe +
# advisory-only ML + dashboard state synchronisation.
# ---------------------------------------------------------------------------
kitchen_path = "wokwi/kitchen-living-room/sketch.ino"
k = read(kitchen_path)

k = replace_once(
    k,
    '#define USE_EDGE_IMPULSE_RUNTIME 0\n\n// If you enable the generated runtime, change this to your own exported header.\n#define EDGE_IMPULSE_INFERENCING_HEADER "your_project_inferencing.h"',
    '#ifndef USE_EDGE_IMPULSE_RUNTIME\n#define USE_EDGE_IMPULSE_RUNTIME 0\n#endif\n\n// If you enable the generated runtime, change this to your own exported header.\n#ifndef EDGE_IMPULSE_INFERENCING_HEADER\n#define EDGE_IMPULSE_INFERENCING_HEADER "your_project_inferencing.h"\n#endif',
    "kitchen compile-time EI overrides",
)

k = replace_once(
    k,
    '''bool emergencyCoolingActive() {\n  if (!dhtValid) return false;\n\n  if (currentEnvironmentStatus == ENV_GAS_HEAT_EMERGENCY) {\n    return true;\n  }\n\n  return (currentGasStatus == GAS_DANGER && currentTempC >= emergencyCoolingTempC);\n}''',
    '''bool emergencyCoolingActive() {\n  if (!dhtValid) return false;\n  return currentEnvironmentStatus == ENV_GAS_HEAT_EMERGENCY;\n}''',
    "kitchen emergency cooling",
)

k = regex_once(
    k,
    r'int environmentSeverity\(EnvironmentStatus s\) \{.*?EnvironmentStatus moreSevereEnvironment\(EnvironmentStatus a, EnvironmentStatus b\) \{.*?\n\}',
    '',
    "remove ML severity merge helpers",
)

k = regex_once(
    k,
    r'EnvironmentStatus ruleEnvironmentStatus\(int gasScore\) \{.*?\n\}\n\n// =====================================================\n// EDGE IMPULSE / AI INFERENCE',
    '''EnvironmentStatus ruleEnvironmentStatus() {\n  if (isMq2WarmingUp()) return ENV_UNKNOWN;\n\n  // Gas labels come only from the persistence-gated gas state machine.\n  // A single raw MQ2 sample must never bypass those timers.\n  if (currentGasStatus == GAS_DANGER) {\n    if (dhtValid && currentTempC >= emergencyCoolingTempC) {\n      return ENV_GAS_HEAT_EMERGENCY;\n    }\n    return ENV_GAS_DANGER;\n  }\n\n  if (currentGasStatus == GAS_COOKING_FUMES) {\n    return ENV_COOKING_FUMES;\n  }\n\n  // If the DHT fails, gas monitoring remains available but heat classification\n  // becomes unknown and the AC is forced off separately as a fail-safe.\n  if (!dhtValid) return ENV_UNKNOWN;\n\n  if (currentTempC >= emergencyCoolingTempC) {\n    return ENV_HEAT_ANOMALY;\n  }\n\n  return ENV_NORMAL;\n}\n\n// =====================================================\n// EDGE IMPULSE / AI INFERENCE''',
    "kitchen persisted environment classification",
)

k = regex_once(
    k,
    r'void updateEnvironmentAI\(int gasScore\) \{.*?\n\}\n\n// =====================================================\n// BLYNK SEND DATA',
    '''void updateEnvironmentAI(int gasScore) {\n  // Safety/action state is always deterministic and persistence-gated.\n  // ML is advisory telemetry only and never controls safety actuators.\n  currentEnvironmentStatus = ruleEnvironmentStatus();\n\n  if (isMq2WarmingUp() || !dhtValid) {\n    lastMlEnvironmentStatus = ENV_UNKNOWN;\n    mlValid = false;\n    mlConfidence = 0.0;\n    return;\n  }\n\n#if USE_EDGE_IMPULSE_RUNTIME\n  if (millis() - lastMlTime >= mlEvery) {\n    lastMlTime = millis();\n    EnvironmentStatus predictedStatus;\n    float confidence;\n    mlValid = runEnvironmentClassifier(gasScore, predictedStatus, confidence);\n    mlConfidence = confidence;\n\n    if (mlValid) {\n      lastMlEnvironmentStatus = predictedStatus;\n      Serial.print("ML advisory status: ");\n      Serial.print(environmentStatusStr(predictedStatus));\n      Serial.print(" confidence=");\n      Serial.println(confidence, 3);\n    } else {\n      lastMlEnvironmentStatus = ENV_UNKNOWN;\n      Serial.println("ML advisory status: invalid or low confidence");\n    }\n  }\n#else\n  lastMlEnvironmentStatus = ENV_UNKNOWN;\n  mlValid = false;\n  mlConfidence = 0.0;\n\n  if (millis() - lastMlTime >= mlEvery) {\n    lastMlTime = millis();\n    Serial.print("ML runtime disabled; actionable environmental status is persistence-gated: ");\n    Serial.println(environmentStatusStr(currentEnvironmentStatus));\n  }\n#endif\n}\n\n// =====================================================\n// BLYNK SEND DATA''',
    "kitchen advisory-only ML",
)

k = replace_once(
    k,
    '''  blynkWriteSafe(V0, currentTempC);\n  blynkWriteSafe(V1, currentHumidity);''',
    '''  if (dhtValid) {\n    blynkWriteSafe(V0, currentTempC);\n    blynkWriteSafe(V1, currentHumidity);\n  } else {\n    blynkWriteSafe(V0, "N/A");\n    blynkWriteSafe(V1, "N/A");\n  }''',
    "kitchen Blynk DHT validity",
)

k = replace_once(
    k,
    '  blynkWriteSafe(V16, thermalStateStr(blynkThermalState));',
    '  blynkWriteSafe(V16, dhtValid ? thermalStateStr(blynkThermalState) : "INVALID");',
    "kitchen Blynk thermal validity",
)

k = replace_once(
    k,
    '''#else\n  blynkWriteSafe(V30, "N/A");\n  blynkWriteSafe(V31, "DISABLED");\n#endif\n}''',
    '''#else\n  blynkWriteSafe(V30, "N/A");\n  blynkWriteSafe(V31, "DISABLED");\n#endif\n\n  // Keep dashboard controls aligned with physical/Serial changes.\n  blynkWriteSafe(V20, currentMode == NORMAL_MODE ? 0 : (currentMode == PRIVACY_MODE ? 1 : 2));\n  blynkWriteSafe(V21, currentBaseProfile == PROFILE_ELDERLY ? 1 : 0);\n  blynkWriteSafe(V22, manualLampOn ? 1 : 0);\n  blynkWriteSafe(V23, childMode ? 1 : 0);\n  blynkWriteSafe(V24, currentHouseStatus == HOUSE_AWAY ? 1 : 0);\n  blynkWriteSafe(V25, petAtHome ? 1 : 0);\n}''',
    "kitchen Blynk control state sync",
)

k = replace_once(
    k,
    '''ACState decideAC(\n  float tempC,\n  float humidity,\n  RoomMode mode,\n  HouseStatus houseStatus,\n  bool childModeActive,\n  BaseProfile baseProfile,\n  ACState previousState\n) {\n  if (houseStatus == HOUSE_AWAY) {''',
    '''ACState decideAC(\n  float tempC,\n  float humidity,\n  RoomMode mode,\n  HouseStatus houseStatus,\n  bool childModeActive,\n  BaseProfile baseProfile,\n  ACState previousState\n) {\n  if (!dhtValid) {\n    return AC_OFF;\n  }\n\n  if (houseStatus == HOUSE_AWAY) {''',
    "kitchen DHT AC fail-safe",
)

k = regex_once(
    k,
    r'// -------------------- GAS LOGIC --------------------\nvoid updateGasStatus\(int gasScore\) \{.*?\n\}\n\n// =====================================================\n// BUTTON DEBOUNCE HELPER',
    '''// -------------------- GAS LOGIC --------------------\nvoid updateGasStatus(int gasScore) {\n  unsigned long now = millis();\n\n  if (isMq2WarmingUp()) {\n    resetGasTimers();\n    currentGasStatus = GAS_NORMAL;\n    return;\n  }\n\n  int warningThreshold, dangerThreshold, severeThreshold, clearThreshold;\n  getGasThresholds(warningThreshold, dangerThreshold, severeThreshold, clearThreshold);\n\n  // Clear only after the reading has remained below the hysteresis boundary.\n  if (gasScore <= clearThreshold) {\n    gasWarningSince = 0;\n    gasDangerSince = 0;\n    gasSevereSince = 0;\n\n    if (currentGasStatus != GAS_NORMAL) {\n      if (gasNormalSince == 0) gasNormalSince = now;\n      if (now - gasNormalSince >= gasClearPersistMs) {\n        setGasStatus(GAS_NORMAL);\n      }\n    } else {\n      gasNormalSince = 0;\n      gasFumesSince = 0;\n    }\n    return;\n  }\n\n  gasNormalSince = 0;\n\n  if (gasScore < warningThreshold) {\n    gasWarningSince = 0;\n    gasDangerSince = 0;\n    gasSevereSince = 0;\n    return;\n  }\n\n  // Start persistence timers, but do not change actionable state yet.\n  if (gasWarningSince == 0) gasWarningSince = now;\n\n  if (gasScore >= dangerThreshold) {\n    if (gasDangerSince == 0) gasDangerSince = now;\n    if (gasFumesSince == 0) gasFumesSince = now;\n  } else {\n    gasDangerSince = 0;\n  }\n\n  // Very high readings use a shorter, still persistence-gated emergency path.\n  if (gasScore >= severeThreshold) {\n    if (gasSevereSince == 0) gasSevereSince = now;\n    if (now - gasSevereSince >= gasSeverePersistMs) {\n      setGasStatus(GAS_DANGER);\n    }\n    return;\n  }\n  gasSevereSince = 0;\n\n  // Warning/fumes state requires sustained elevation.\n  if (currentGasStatus == GAS_NORMAL && now - gasWarningSince >= gasWarnPersistMs) {\n    setGasStatus(GAS_COOKING_FUMES);\n  }\n\n  // Normal danger path requires sustained danger and sustained fumes exposure.\n  if (gasScore >= dangerThreshold) {\n    bool dangerPersistent = (now - gasDangerSince >= gasDangerPersistMs);\n    bool fumesLongEnough = (now - gasFumesSince >= gasMinFumesBeforeDangerMs);\n\n    if (currentGasStatus == GAS_COOKING_FUMES && dangerPersistent && fumesLongEnough) {\n      setGasStatus(GAS_DANGER);\n    }\n  }\n}\n\n// =====================================================\n// BUTTON DEBOUNCE HELPER''',
    "kitchen gas persistence state machine",
)

k = replace_once(
    k,
    '''  if (pinAlert) {\n    lcdPrint2("PIN ERROR ALERT", "3 WRONG TRIES");\n    return;\n  }\n\n  if (currentRequest == REQ_CHILD_EXIT_PIN) {''',
    '''  if (pinAlert) {\n    lcdPrint2("PIN ERROR ALERT", "3 WRONG TRIES");\n    return;\n  }\n\n  if (currentRequest == REQ_CHILD_EXIT_PIN) {''',
    "kitchen stable LCD anchor",
)

k = replace_once(
    k,
    '''  if (currentRequest == REQ_AWAY_PET_QUERY) {\n    lcdPrint2("PET AT HOME?", "V25 OR y/n");\n    return;\n  }\n\n  int page = (millis() / 2200) % 4;''',
    '''  if (currentRequest == REQ_AWAY_PET_QUERY) {\n    lcdPrint2("PET AT HOME?", "V25 OR y/n");\n    return;\n  }\n\n  if (!dhtValid && currentGasStatus == GAS_NORMAL) {\n    lcdPrint2("DHT SENSOR ERROR", "AC FAIL-SAFE OFF");\n    return;\n  }\n\n  int page = (millis() / 2200) % 4;''',
    "kitchen LCD DHT fail-safe",
)

k = replace_once(
    k,
    '''  if (pinAlert) return "PIN ERROR ALERT";\n  return "NONE";''',
    '''  if (pinAlert) return "PIN ERROR ALERT";\n  if (!dhtValid) return "DHT SENSOR ERROR";\n  return "NONE";''',
    "kitchen DHT alert text",
)

k = replace_once(
    k,
    '''  // Original rule-based gas state machine.\n  // Kept as deterministic safety fallback.\n  updateGasStatus(gasScore);\n\n  // Deterministic rules are authoritative; optional ML can only add severity when enabled.\n  updateEnvironmentAI(gasScore);''',
    '''  // Persistence-gated deterministic gas state machine.\n  updateGasStatus(gasScore);\n\n  // Actionable status remains deterministic. Optional ML is advisory telemetry only.\n  updateEnvironmentAI(gasScore);''',
    "kitchen loop semantics comment",
)

k = replace_once(
    k,
    '  ThermalState thermalState = classifyThermal(currentTempC, acOnThreshold, acOffThreshold);',
    '  ThermalState thermalState = dhtValid ? classifyThermal(currentTempC, acOnThreshold, acOffThreshold) : THERMAL_COMFORT;',
    "kitchen thermal state invalid handling",
)

write(kitchen_path, k)


# ---------------------------------------------------------------------------
# Bedroom sketch: DHT fail-safe, dashboard state sync, and eliminate a one-loop
# blind/daylight transient by using the target blind position immediately.
# ---------------------------------------------------------------------------
bedroom_path = "wokwi/bedroom/sketch.ino"
b = read(bedroom_path)

b = replace_once(
    b,
    '''  blynkWriteSafe(V0, currentTempC);\n  blynkWriteSafe(V1, currentHumidity);''',
    '''  if (dhtValid) {\n    blynkWriteSafe(V0, currentTempC);\n    blynkWriteSafe(V1, currentHumidity);\n  } else {\n    blynkWriteSafe(V0, "N/A");\n    blynkWriteSafe(V1, "N/A");\n  }''',
    "bedroom Blynk DHT validity",
)

b = replace_once(
    b,
    '  blynkWriteSafe(V16, thermalStateStr(blynkThermalState));',
    '  blynkWriteSafe(V16, dhtValid ? thermalStateStr(blynkThermalState) : "INVALID");',
    "bedroom Blynk thermal validity",
)

b = replace_once(
    b,
    '''  blynkWriteSafe(V17, insideStateStr(blynkInsideState));\n  blynkWriteSafe(V18, outsideStateStr(blynkOutsideState));\n  blynkWriteSafe(V19, presenceLabel(blynkPresence, blynkInsideState));\n}''',
    '''  blynkWriteSafe(V17, insideStateStr(blynkInsideState));\n  blynkWriteSafe(V18, outsideStateStr(blynkOutsideState));\n  blynkWriteSafe(V19, presenceLabel(blynkPresence, blynkInsideState));\n\n  // Keep dashboard controls aligned with physical/Serial changes.\n  int modeValue = 0;\n  if (currentMode == SLEEP_MODE) modeValue = 1;\n  else if (currentMode == PRIVACY_MODE) modeValue = 2;\n  else if (currentMode == ECO_MODE) modeValue = 3;\n  blynkWriteSafe(V20, modeValue);\n  blynkWriteSafe(V21, currentBaseProfile == PROFILE_ELDERLY ? 1 : 0);\n  blynkWriteSafe(V22, manualLampOn ? 1 : 0);\n  blynkWriteSafe(V23, childMode ? 1 : 0);\n  blynkWriteSafe(V24, currentHouseStatus == HOUSE_AWAY ? 1 : 0);\n  blynkWriteSafe(V25, petAtHome ? 1 : 0);\n}''',
    "bedroom Blynk control state sync",
)

b = replace_once(
    b,
    '''ACState decideAC(\n  float tempC,\n  float humidity,\n  RoomMode mode,\n  HouseStatus houseStatus,\n  bool childModeActive,\n  BaseProfile baseProfile,\n  ACState previousState\n) {\n  if (houseStatus == HOUSE_AWAY) {''',
    '''ACState decideAC(\n  float tempC,\n  float humidity,\n  RoomMode mode,\n  HouseStatus houseStatus,\n  bool childModeActive,\n  BaseProfile baseProfile,\n  ACState previousState\n) {\n  if (!dhtValid) {\n    return AC_OFF;\n  }\n\n  if (houseStatus == HOUSE_AWAY) {''',
    "bedroom DHT AC fail-safe",
)

b = replace_once(
    b,
    '''  } else {\n    String line1 = "T:" + String(currentTempC, 1) + "C H:" + String((int)currentHumidity) + "%";\n    String line2 = "AC:" + String(acStateStr(currentACState)) + " " + String(thermalStateStr(thermalState));\n    lcd.setCursor(0, 0);\n    lcd.print(pad16(line1));\n    lcd.setCursor(0, 1);\n    lcd.print(pad16(line2));\n  }\n}''',
    '''  } else {\n    lcd.setCursor(0, 0);\n    lcd.setCursor(0, 1);\n    if (!dhtValid) {\n      lcd.setCursor(0, 0);\n      lcd.print(pad16("DHT SENSOR ERROR"));\n      lcd.setCursor(0, 1);\n      lcd.print(pad16("AC FAIL-SAFE OFF"));\n    } else {\n      String line1 = "T:" + String(currentTempC, 1) + "C H:" + String((int)currentHumidity) + "%";\n      String line2 = "AC:" + String(acStateStr(currentACState)) + " " + String(thermalStateStr(thermalState));\n      lcd.setCursor(0, 0);\n      lcd.print(pad16(line1));\n      lcd.setCursor(0, 1);\n      lcd.print(pad16(line2));\n    }\n  }\n}''',
    "bedroom LCD DHT fail-safe",
)

b = replace_once(
    b,
    '''  BlindState effectiveBlindState = maxOpenBlindState(currentBlindState, blindTarget);\n  int daylightBoost = getBlindDaylightBoost(effectiveBlindState, outsideState, outsideScore);''',
    '''  // Use the target position immediately so daylight estimation and the\n  // commanded servo state describe the same control cycle.\n  BlindState effectiveBlindState = blindTarget;\n  int daylightBoost = getBlindDaylightBoost(effectiveBlindState, outsideState, outsideScore);''',
    "bedroom blind/daylight transient",
)

b = replace_once(
    b,
    '  ThermalState thermalState = classifyThermal(currentTempC, acOnThreshold, acOffThreshold);',
    '  ThermalState thermalState = dhtValid ? classifyThermal(currentTempC, acOnThreshold, acOffThreshold) : THERMAL_COMFORT;',
    "bedroom thermal state invalid handling",
)

b = replace_once(
    b,
    '''  Serial.print("Temperature: ");\n  Serial.print(currentTempC, 1);\n  Serial.println(" C");\n\n  Serial.print("Humidity: ");\n  Serial.print(currentHumidity, 1);\n  Serial.println(" %");\n\n  Serial.print("Thermal state: ");\n  Serial.println(thermalStateStr(thermalState));''',
    '''  if (dhtValid) {\n    Serial.print("Temperature: ");\n    Serial.print(currentTempC, 1);\n    Serial.println(" C");\n\n    Serial.print("Humidity: ");\n    Serial.print(currentHumidity, 1);\n    Serial.println(" %");\n\n    Serial.print("Thermal state: ");\n    Serial.println(thermalStateStr(thermalState));\n  } else {\n    Serial.println("Temperature: INVALID");\n    Serial.println("Humidity: INVALID");\n    Serial.println("Thermal state: INVALID");\n  }''',
    "bedroom serial DHT validity",
)

write(bedroom_path, b)


# ---------------------------------------------------------------------------
# Wokwi diagrams: deterministic initial state + professional labels.
# ---------------------------------------------------------------------------
bed_diagram = read("wokwi/bedroom/diagram.json")
bed_diagram = replace_once(bed_diagram, '"lux": "80"', '"lux": "0.1"', "bedroom inside LDR initial lux")
bed_diagram = replace_once(
    bed_diagram,
    '"text": "LDR2 (Inside) SET AT FIRST TO MINIMUM (0.1) AND DON\'T TOUCH AGAIN, TREAT IT ONLY AS SENSOR\\n"',
    '"text": "LDR2 (Inside) - sensor input; default 0.1 lux for reproducible demo"',
    "bedroom inside LDR label",
)
write("wokwi/bedroom/diagram.json", bed_diagram)

kit_diagram = read("wokwi/kitchen-living-room/diagram.json")
kit_diagram = replace_once(
    kit_diagram,
    '"text": "LDR3 (Inside) SET AT FIRST TO MINIMUM (0.1) AND DON\'T TOUCH AGAIN, TREAT IT ONLY AS SENSOR\\n"',
    '"text": "LDR3 (Inside) - sensor input; default 0.1 lux for reproducible demo"',
    "kitchen inside LDR label",
)
kit_diagram = replace_once(
    kit_diagram,
    '"text": "Emergency cooling system"',
    '"text": "Emergency cooling indicator (simulation)"',
    "kitchen emergency indicator label",
)
write("wokwi/kitchen-living-room/diagram.json", kit_diagram)


# ---------------------------------------------------------------------------
# Pin Wokwi libraries to the same versions used by CI.
# ---------------------------------------------------------------------------
libraries = '''# Wokwi Library List\n# Pinned to match GitHub Actions for reproducible builds.\n\nBlynk@1.4.0\nESP32Servo@3.2.1\nLiquidCrystal_PCF8574@2.3.0\nDHT sensor library@1.4.7\n'''
write("wokwi/bedroom/libraries.txt", libraries)
write(
    "wokwi/kitchen-living-room/libraries.txt",
    libraries
    + '''\n# Optional Edge Impulse inferencing library\n# ----------------------------------------\n# The current public source tree does not include a generated Edge Impulse\n# deployment archive. If USE_EDGE_IMPULSE_RUNTIME is enabled, add a compatible\n# library generated from your own Edge Impulse project and set\n# EDGE_IMPULSE_INFERENCING_HEADER to its generated header.\n''',
)


# ---------------------------------------------------------------------------
# Stronger deterministic scenario tests.
# ---------------------------------------------------------------------------
write(
    "scripts/test_scenarios.py",
    r'''#!/usr/bin/env python3
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
''',
)


# ---------------------------------------------------------------------------
# Repository validator: dataset, diagrams, pin surface, secrets, docs, pinned
# dependencies and hardened semantics.
# ---------------------------------------------------------------------------
write(
    "scripts/validate_repo.py",
    r'''#!/usr/bin/env python3
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
''',
)


# Mock generated Edge Impulse surface used only by CI to compile the optional path.
write(
    "tests/edge_impulse_mock.h",
    r'''#pragma once

#include <stddef.h>

#define EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE 3
#define EI_CLASSIFIER_LABEL_COUNT 5

typedef struct {
  size_t total_length;
} signal_t;

typedef struct {
  const char* label;
  float value;
} ei_classification_t;

typedef struct {
  ei_classification_t classification[EI_CLASSIFIER_LABEL_COUNT];
} ei_impulse_result_t;

enum EI_IMPULSE_ERROR {
  EI_IMPULSE_OK = 0
};

namespace numpy {
inline int signal_from_buffer(float*, size_t length, signal_t* signal) {
  signal->total_length = length;
  return 0;
}
}

inline EI_IMPULSE_ERROR run_classifier(signal_t*, ei_impulse_result_t* result, bool) {
  static const char* labels[EI_CLASSIFIER_LABEL_COUNT] = {
    "NORMAL", "COOKING_FUMES", "GAS_DANGER", "HEAT_ANOMALY", "GAS_HEAT_EMERGENCY"
  };
  for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; ++i) {
    result->classification[i].label = labels[i];
    result->classification[i].value = (i == 0) ? 1.0f : 0.0f;
  }
  return EI_IMPULSE_OK;
}
''',
)


# ---------------------------------------------------------------------------
# CI: public default compile + optional EI integration-surface compile.
# ---------------------------------------------------------------------------
write(
    ".github/workflows/quality.yml",
    '''name: Repository quality\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\npermissions:\n  contents: read\n\njobs:\n  validate:\n    name: Validate public repository\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out repository\n        uses: actions/checkout@v7\n      - name: Set up Python\n        uses: actions/setup-python@v7\n        with:\n          python-version: "3.12"\n      - name: Run repository validation\n        run: python scripts/validate_repo.py\n      - name: Run deterministic scenario contracts\n        run: python scripts/test_scenarios.py\n\n  arduino-compile:\n    name: Compile ESP32-S3 sketches\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out repository\n        uses: actions/checkout@v7\n      - name: Set up Arduino CLI\n        uses: arduino/setup-arduino-cli@v2\n        with:\n          version: "1.5.1"\n      - name: Install pinned ESP32 platform\n        run: |\n          arduino-cli config init\n          arduino-cli core update-index\n          arduino-cli core install esp32:esp32@3.3.12\n      - name: Install pinned Arduino libraries\n        run: |\n          arduino-cli lib install "Blynk@1.4.0"\n          arduino-cli lib install "ESP32Servo@3.2.1"\n          arduino-cli lib install "LiquidCrystal_PCF8574@2.3.0"\n          arduino-cli lib install "DHT sensor library@1.4.7"\n      - name: Prepare sketches for Arduino CLI\n        run: |\n          mkdir -p /tmp/aiot-bedroom /tmp/aiot-kitchen /tmp/aiot-kitchen-ml\n          cp wokwi/bedroom/sketch.ino /tmp/aiot-bedroom/aiot-bedroom.ino\n          cp wokwi/kitchen-living-room/sketch.ino /tmp/aiot-kitchen/aiot-kitchen.ino\n          cp wokwi/kitchen-living-room/sketch.ino /tmp/aiot-kitchen-ml/aiot-kitchen-ml.ino\n          cp tests/edge_impulse_mock.h /tmp/aiot-kitchen-ml/edge_impulse_mock.h\n          python - <<'PY'\n          from pathlib import Path\n          p = Path('/tmp/aiot-kitchen-ml/aiot-kitchen-ml.ino')\n          s = p.read_text()\n          s = s.replace('#define USE_EDGE_IMPULSE_RUNTIME 0', '#define USE_EDGE_IMPULSE_RUNTIME 1', 1)\n          s = s.replace('#define EDGE_IMPULSE_INFERENCING_HEADER "your_project_inferencing.h"', '#define EDGE_IMPULSE_INFERENCING_HEADER "edge_impulse_mock.h"', 1)\n          p.write_text(s)\n          PY\n      - name: Compile bedroom module\n        run: arduino-cli compile --fqbn esp32:esp32:esp32s3 /tmp/aiot-bedroom\n      - name: Compile kitchen/living-room public default\n        run: arduino-cli compile --fqbn esp32:esp32:esp32s3 /tmp/aiot-kitchen\n      - name: Compile optional Edge Impulse integration surface\n        run: arduino-cli compile --fqbn esp32:esp32:esp32s3 /tmp/aiot-kitchen-ml\n''',
)


# ---------------------------------------------------------------------------
# Documentation: one consistent, recruiter-safe public story.
# ---------------------------------------------------------------------------
write(
    "README.md",
    '''<p align="center">\n  <img src="assets/aiot-smart-home-logo.png" alt="AIoT Smart Home ESP32-S3" width="420"/>\n</p>\n\n<h1 align="center">AIoT Smart Home ESP32-S3</h1>\n\n<p align="center">\n  Simulation-based ESP32-S3 smart-home prototype combining deterministic room automation, Wokwi, optional Blynk monitoring and a documented TinyML experimentation path.\n</p>\n\n<p align="center">\n  <a href="https://wokwi.com/projects/465661521735358465">Bedroom Wokwi Demo</a> ·\n  <a href="https://wokwi.com/projects/465661368262601729">Kitchen/Living Room Wokwi Demo</a> ·\n  <a href="report/aiot_smart_home_public_report.pdf">Technical Report</a> ·\n  <a href="docs/REPRODUCIBILITY.md">Reproducibility Notes</a>\n</p>\n\n---\n\n## Overview\n\nThis repository presents a **simulation-based AIoT smart-home prototype** built around two ESP32-S3 room controllers. It demonstrates embedded Arduino/C++ programming, sensor/actuator orchestration, local comfort/privacy/security logic, persistence-gated environmental safety behaviour, optional Blynk integration and a historical Edge Impulse/TinyML experiment.\n\nThe project is an academic/portfolio prototype. It is **not a production safety system**, and the TinyML results are not presented as real-world hazard-detection validation.\n\n### Public defaults are offline-first\n\nBoth sketches keep Blynk disabled by default:\n\n```cpp\n#define ENABLE_BLYNK 0\n```\n\nThe Kitchen/Living Room sketch also keeps the generated Edge Impulse runtime disabled by default:\n\n```cpp\n#define USE_EDGE_IMPULSE_RUNTIME 0\n```\n\nA public clone therefore runs its local Wokwi logic without private cloud credentials or a generated third-party ML package.\n\nWhen ML is disabled, `V29` reports the deterministic persistence-gated environmental state, `V30` reports `N/A`, and `V31` reports `DISABLED`. If a reviewer supplies a compatible Edge Impulse library and explicitly enables it, the model output is **advisory telemetry only**; safety actuators remain controlled by the deterministic state machine.\n\n---\n\n## Recruiter Snapshot\n\n| Area | Evidence |\n|---|---|\n| Embedded systems | Two ESP32-S3 Arduino sketches with room-level state/control logic |\n| IoT simulation | Public Wokwi demos plus checked-in `sketch.ino`, `diagram.json` and pinned `libraries.txt` |\n| Reliability | Persistence-gated gas escalation, DHT fail-safe AC shutdown, deterministic scenario tests |\n| Cloud/dashboard | Optional Blynk virtual-pin monitoring and interaction |\n| TinyML | Synthetic dataset, historical Edge Impulse screenshots/model card, optional advisory inference surface |\n| Reproducibility | Dataset/rule validator, pinned dependencies and ESP32-S3 CI compilation |\n| Documentation | Architecture visuals, module notes, model card and professional technical report |\n\n### What the ML result does - and does not - show\n\nThe environmental dataset is **simulated and rule-labelled**. Labels are generated from demonstration thresholds using the same synthetic variables supplied to the model. Strong classifier performance is therefore expected: it demonstrates an embedded-ML workflow learning designed decision regions, not independent discovery of real household hazards.\n\nReal-world validation would require physical sensors, calibration, independently labelled data, collection-aware train/validation/test separation, hardware measurements and a safety review.\n\nSee [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) and [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md).\n\n---\n\n## Live Demos\n\n| Component | Link | Purpose |\n|---|---|---|\n| Bedroom | [Open in Wokwi](https://wokwi.com/projects/465661521735358465) | Lighting, blinds, comfort, profiles and Home/Away security |\n| Kitchen/Living Room | [Open in Wokwi](https://wokwi.com/projects/465661368262601729) | Persistence-gated gas/heat monitoring, emergency logic and optional Blynk interaction |\n| Technical report | [Open PDF](report/aiot_smart_home_public_report.pdf) | Architecture, implementation, evaluation, evidence and limitations |\n\nThe checked-in Wokwi files are the repository authority. If a hosted Wokwi copy ever differs, refresh it from the matching `wokwi/<module>/` folder.\n\n---\n\n## Architecture\n\n```text\nSmart Home Prototype\n│\n├── Bedroom ESP32-S3\n│   ├── PIR occupancy\n│   ├── indoor/outdoor light sensing\n│   ├── DHT22 temperature/humidity\n│   ├── servo-controlled blinds\n│   ├── PWM ambient + manual lighting\n│   ├── AC relay + LCD\n│   ├── profile/privacy logic\n│   └── Home/Away security state\n│\n└── Kitchen/Living Room ESP32-S3\n    ├── MQ2 gas input\n    ├── DHT22 temperature/humidity\n    ├── persistence-gated gas state machine\n    ├── buzzer + emergency-cooling indicator\n    ├── optional Blynk dashboard\n    ├── deterministic actionable environmental state\n    └── optional advisory Edge Impulse inference\n```\n\n---\n\n## Reliability and Safety Semantics\n\nThe public Kitchen/Living Room runtime deliberately separates **raw observations** from **actionable state**:\n\n- MQ2 warm-up: 15 s;\n- fumes/warning: requires sustained elevation for 2.5 s;\n- normal danger path: requires sustained danger/fumes history for 8 s;\n- severe gas path: requires 1.2 s persistence;\n- clearing a latched gas state: requires 5 s below the clear boundary;\n- optional ML never bypasses these timers;\n- if DHT data is invalid, the AC is forced **OFF** and heat classification becomes unavailable, while gas monitoring remains active.\n\nThese are project-specific demonstration rules, **not calibrated safety limits**.\n\n---\n\n## Bedroom Module\n\nLocation: [`wokwi/bedroom/`](wokwi/bedroom/)\n\n- Normal, Sleep, Privacy and Eco modes;\n- Standard, Elderly and Child profiles;\n- adaptive lighting and servo blind automation;\n- PIR-based occupancy tracking;\n- DHT22 monitoring with AC hysteresis and invalid-sensor fail-safe;\n- Home/Away state, pet-aware motion escalation and demonstration authentication.\n\nThe physical Wokwi outdoor LDR is authoritative by default. If Blynk is enabled, V3 can take control; moving the physical LDR again returns control to Wokwi.\n\n---\n\n## Kitchen / Living Room Module\n\nLocation: [`wokwi/kitchen-living-room/`](wokwi/kitchen-living-room/)\n\n- MQ2 gas-score monitoring with persistence/hysteresis;\n- DHT22 temperature/humidity sensing with fail-safe AC shutdown;\n- heat anomaly and gas+heat emergency states;\n- buzzer, blinds and emergency-cooling indicator;\n- Home/Away security logic;\n- optional Blynk dashboard;\n- optional Edge Impulse classifier used only as advisory telemetry.\n\nNo generated Edge Impulse inferencing archive is present in the **current source tree**.\n\n---\n\n## TinyML / Edge Impulse Experiment\n\n[`data/environmental_training_dataset.csv`](data/environmental_training_dataset.csv) contains simulated `gas_score`, `temperature`, `humidity` and a five-class label. The labels are deterministic demonstration rules: `GAS_HEAT_EMERGENCY`, `GAS_DANGER`, `HEAT_ANOMALY`, `COOKING_FUMES`, or `NORMAL`. Humidity is an input feature but does not generate the synthetic ground-truth label.\n\nHistorical Edge Impulse evidence is retained under [`assets/`](assets/) and summarised in [`edge-impulse/HISTORICAL_MODEL_CARD.md`](edge-impulse/HISTORICAL_MODEL_CARD.md). The exact historical split, random seed and training hyperparameters are not asserted because independently verifiable machine-readable configuration is not preserved.\n\n---\n\n## Repository Quality Checks\n\n```bash\npython scripts/validate_repo.py\npython scripts/test_scenarios.py\n```\n\nGitHub Actions additionally compiles:\n\n1. the Bedroom public sketch;\n2. the Kitchen/Living Room public default;\n3. the **optional Edge Impulse integration surface** against a CI-only mock generated header, so that path cannot silently rot even though the real third-party export is not redistributed.\n\nToolchain/library versions are pinned in [`.github/workflows/quality.yml`](.github/workflows/quality.yml) and mirrored in both Wokwi `libraries.txt` files.\n\n---\n\n## Blynk Configuration\n\nThe public sketches intentionally contain placeholders and keep Blynk off by default. `Wokwi-GUEST` is the simulator network, not a private credential. Any visible PIN or secret word is a demonstration value, not production authentication.\n\n---\n\n## Limitations\n\n- sensors are simulated;\n- gas/heat thresholds are demonstration values;\n- the ML dataset is synthetic and rule-labelled;\n- model metrics are historical platform evidence, not independent real-world validation;\n- no physical ESP32-S3 deployment is claimed;\n- the generated Edge Impulse runtime is not present in the current source tree and is disabled by default;\n- Blynk is disabled by default;\n- emergency-response behaviour requires domain review before real deployment;\n- demo authentication values are not secure production credentials.\n\n---\n\n## Technical Report\n\n[`report/aiot_smart_home_public_report.pdf`](report/aiot_smart_home_public_report.pdf)\n\nThe report is authored from retained LaTeX source. The source package is maintained separately from the public repository so the portfolio tree does not duplicate the report's large figure set.\n\n---\n\n## Licence\n\nOriginal project code and documentation are provided under [`LICENSE`](LICENSE). Third-party tools, libraries and generated deployment components remain subject to their own licence terms.\n\n---\n\n## Author\n\n**Alberto Reyes Castro**  \nPhysics graduate · MSc Artificial Intelligence Technology student\n\nPortfolio focus: applied AI, embedded/IoT systems, TinyML experimentation, scientific computing and reliable automation.\n''',
)

write(
    "docs/REPRODUCIBILITY.md",
    '''# Reproducibility and Evaluation Notes\n\nThis document defines what the hardened public AIoT repository does and does not reproduce.\n\n## Public runtime defaults\n\nBoth sketches keep `ENABLE_BLYNK` at `0`. The Kitchen/Living Room sketch also keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`. A public clone therefore runs local Wokwi logic without private cloud credentials or a generated Edge Impulse package.\n\nWhen ML is disabled, the actionable environmental state is deterministic and persistence-gated. ML confidence is `N/A` and the raw ML prediction is `DISABLED`. If a compatible generated runtime is explicitly supplied and enabled, its prediction is advisory telemetry only and does not drive safety actuators.\n\n## Dataset provenance\n\n`data/environmental_training_dataset.csv` contains simulated gas, temperature and humidity values. Labels are generated deterministically from project-specific demonstration boundaries. Humidity is included as an input but does not determine the synthetic ground-truth label. Strong classifier performance is therefore expected and is not independent real-world predictive validation.\n\n## Runtime reliability contract\n\nKitchen/Living Room gas actions use a persistence-gated state machine: 15 s MQ2 warm-up, 2.5 s fumes persistence, 8 s normal danger persistence, 1.2 s severe-path persistence and 5 s clear persistence. The optional ML path cannot bypass these timers.\n\nIf DHT data becomes invalid, both modules force the AC off. Kitchen gas monitoring remains available independently of DHT validity, while heat-only classification becomes unavailable until valid temperature/humidity data returns.\n\n## What is reproducible from this repository\n\nA reviewer can reproduce or inspect:\n\n1. both checked-in Wokwi ESP32-S3 room configurations;\n2. deterministic room-control and safety logic;\n3. the complete synthetic dataset and labelling contract;\n4. repository validation with `python scripts/validate_repo.py`;\n5. temporal/design scenario contracts with `python scripts/test_scenarios.py`;\n6. both public ESP32-S3 builds with pinned toolchain/library versions;\n7. a CI compile of the optional Edge Impulse integration surface using a mock generated header;\n8. the professional public PDF report;\n9. historical Edge Impulse screenshots and the evidence-based model card.\n\nThe hosted Wokwi projects are convenience demos; the checked-in `sketch.ino`, `diagram.json` and `libraries.txt` files are authoritative.\n\n## Historical Edge Impulse run vs exact reproduction\n\nThe repository preserves historical screenshots and the metrics that those screenshots support. It does **not** preserve independently verifiable machine-readable evidence for the exact historical train/validation/test split, random seed or training hyperparameters, and therefore does not assert them.\n\nThe generated inferencing archive is not present in the current source tree. An equivalent workflow can be recreated from the public dataset and model description, but the exact historical hosted run is not claimed to be bit-for-bit reproducible.\n\n## Enabling optional integrations\n\n### Blynk\n\nSupply your own template/auth values outside public commits, set `ENABLE_BLYNK` to `1`, and validate your own virtual-pin configuration.\n\n### Edge Impulse\n\nCreate your own Edge Impulse project, import equivalent simulated data, train/test a five-class classifier, export a compatible Arduino/C++ library, set `EDGE_IMPULSE_INFERENCING_HEADER` to its generated header, enable `USE_EDGE_IMPULSE_RUNTIME`, and validate on the intended target. The resulting ML output remains advisory unless you deliberately redesign and revalidate the safety architecture.\n\n## Real-world validation still required\n\nA production-oriented follow-up needs calibrated physical sensors, independently labelled real data, collection-aware data splits, sensor-fault/drift tests, false-positive/false-negative analysis, actual target latency/RAM/flash/power measurements, secure credential provisioning and domain safety review.\n''',
)

write(
    "edge-impulse/README.md",
    '''# Edge Impulse / TinyML Integration\n\nThis folder documents the optional Edge Impulse experimentation path used for the Kitchen/Living Room environmental classifier.\n\nThe checked-in public simulation keeps `USE_EDGE_IMPULSE_RUNTIME` at `0`. No ML inference runs by default. The deterministic, persistence-gated state machine controls safety actuators; an explicitly enabled model is advisory telemetry only.\n\n## Generated package\n\nA generated inferencing archive is **not present in the current public source tree**. Generated exports can include Edge Impulse runtime/SDK and other third-party material under licence terms separate from this repository's original MIT-licensed code/documentation. The public tree therefore documents regeneration instead of relying on that binary package.\n\n## Historical evidence\n\n- Training/test screenshots remain under `assets/`.\n- Metrics supported by those screenshots are summarised in [`HISTORICAL_MODEL_CARD.md`](HISTORICAL_MODEL_CARD.md).\n- Exact historical split, seed and training hyperparameters are not asserted because independently verifiable machine-readable configuration is not preserved.\n- The historical hosted project/export is not claimed to be bit-for-bit reproducible from this repository alone.\n\n## Equivalent deployment path\n\n1. Create your own Edge Impulse project.\n2. Import equivalent simulated sensor data.\n3. Train and test the five-class classifier.\n4. Export an Arduino/C++ inferencing library under the applicable terms.\n5. Add the generated library to the build environment.\n6. Set `EDGE_IMPULSE_INFERENCING_HEADER` to the generated header.\n7. Set `USE_EDGE_IMPULSE_RUNTIME` to `1`.\n8. Compile and validate on the intended target.\n\nCI compiles this optional integration surface against `tests/edge_impulse_mock.h` so API drift is caught without redistributing a third-party generated model.\n\nSee [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md).\n''',
)

write(
    "report/README.md",
    '''# Project Report\n\nThis folder contains the public portfolio version of the **AIoT Smart Home ESP32-S3** professional technical report.\n\n- [Open the public technical report](./aiot_smart_home_public_report.pdf)\n\nThe report documents the simulation architecture, Bedroom and Kitchen/Living Room controllers, persistence-gated environmental logic, optional Blynk monitoring, historical Edge Impulse/TinyML experimentation, evaluation evidence, ethics/privacy/security considerations and limitations.\n\nThe public report does not claim physical-hardware deployment, calibrated safety thresholds or independent real-world ML validation. Historical platform screenshots are labelled as such, and current public-runtime semantics distinguish deterministic actionable state from optional advisory ML telemetry.\n\nThe authored LaTeX source package is retained separately from this public repository to avoid duplicating the report's large figure set. Report changes are made from that source and then the reviewed PDF is replaced here.\n\nNo real Blynk tokens, Wi-Fi passwords or private API credentials are intentionally included. Visible PINs/secret words are demonstration values only.\n\n## Author\n\nAlberto Reyes Castro  \nMSc Artificial Intelligence Technology Portfolio Project\n''',
)

write(
    "wokwi/bedroom/README.md",
    '''# Bedroom Module\n\nPublic Wokwi files for the Bedroom ESP32-S3 controller. The checked-in files are authoritative for the portfolio version.\n\n## Features\n\n- indoor/outdoor LDR sensing and adaptive lighting;\n- servo blind control;\n- PIR presence tracking;\n- DHT22 monitoring;\n- AC hysteresis with **DHT-invalid fail-safe OFF**;\n- Normal, Sleep, Privacy and Eco modes;\n- Standard, Elderly and Child profiles;\n- Home/Away security with pet-aware escalation;\n- optional Blynk dashboard.\n\n[Open Bedroom Wokwi simulation](https://wokwi.com/projects/465661521735358465)\n\nBlynk is disabled by default with public placeholders. The physical outdoor LDR is authoritative until an enabled Blynk V3 interaction explicitly takes control; moving the physical LDR returns control to Wokwi. Dashboard control widgets are periodically resynchronised with local state.\n\nThe inside LDR starts at 0.1 lux for a deterministic demo baseline.\n\nThe visible PIN and secret word are demonstration values, not production credentials.\n\nReal deployment requires physical hardware validation, sensor calibration, electrical safety checks and secure credential management.\n''',
)

write(
    "wokwi/kitchen-living-room/README.md",
    '''# Kitchen and Living Room Module\n\nPublic Wokwi files for the Kitchen/Living Room ESP32-S3 controller. The checked-in files are authoritative for the portfolio version.\n\n## Features\n\n- MQ2 gas-score monitoring with persistence/hysteresis;\n- DHT22 temperature/humidity sensing;\n- AC fail-safe OFF when DHT data is invalid;\n- gas warning/danger and heat anomaly states;\n- buzzer, blinds and emergency-cooling indicator;\n- Home/Away security;\n- optional Blynk;\n- optional Edge Impulse inference as **advisory telemetry only**.\n\n[Open Kitchen/Living Room Wokwi simulation](https://wokwi.com/projects/465661368262601729)\n\n## Public defaults\n\n```cpp\n#define ENABLE_BLYNK 0\n#define USE_EDGE_IMPULSE_RUNTIME 0\n```\n\nWith ML disabled, `V29` is the deterministic persistence-gated environmental state, `V30` is `N/A`, and `V31` is `DISABLED`. No fabricated confidence/prediction is emitted.\n\nGas actions cannot be triggered by one isolated raw reading: fumes, danger, severe escalation and clearing all have explicit persistence windows. Optional ML does not bypass those windows or drive safety actuators.\n\nThe current source tree does not include a generated Edge Impulse archive. See [`../../edge-impulse/README.md`](../../edge-impulse/README.md).\n\nThresholds and emergency behaviour are demonstration constructs, not calibrated safety limits.\n''',
)

# Model card: keep evidence wording aligned with advisory-only runtime.
model_card = read("edge-impulse/HISTORICAL_MODEL_CARD.md")
model_card = model_card.replace(
    "The deterministic environmental rules drive the public simulation, while the optional generated runtime can be enabled only by a reviewer who provides their own compatible Edge Impulse library and validates it on the intended target.",
    "The deterministic, persistence-gated environmental rules drive the public simulation and its safety actuators. A reviewer may provide a compatible generated Edge Impulse library, but its prediction is advisory telemetry unless the architecture is deliberately redesigned and revalidated.",
)
write("edge-impulse/HISTORICAL_MODEL_CARD.md", model_card)

print("final hardening patch applied")
