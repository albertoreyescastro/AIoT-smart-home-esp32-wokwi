#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def die(msg: str) -> None:
    raise RuntimeError(msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, repl: str, label: str) -> str:
    out, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count != 1:
        die(f"{label}: expected exactly one regex match, found {count}")
    return out


def patch_bedroom() -> None:
    path = ROOT / "wokwi/bedroom/sketch.ino"
    s = path.read_text(encoding="utf-8")

    s = replace_once(s, '#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"\n', '#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"\n\n// Public portfolio default: local Wokwi logic must not depend on cloud credentials.\n#define ENABLE_BLYNK 0\n', "bedroom ENABLE_BLYNK")
    s = replace_once(s, '#include <LiquidCrystal_I2C.h>', '#include <LiquidCrystal_PCF8574.h>', "bedroom LCD include")
    s = replace_once(s, 'LiquidCrystal_I2C lcd(0x27, 16, 2);', 'LiquidCrystal_PCF8574 lcd(0x27);', "bedroom LCD object")
    s = replace_once(s, 'BlynkTimer timer;\n', '''BlynkTimer timer;\n\ntemplate <typename T>\nvoid blynkWriteSafe(int pin, const T &value) {\n#if ENABLE_BLYNK\n  Blynk.virtualWrite(pin, value);\n#else\n  (void)pin;\n  (void)value;\n#endif\n}\n''', "bedroom Blynk helper")
    s = s.replace('Blynk.virtualWrite(', 'blynkWriteSafe(')
    s = s.replace('  blynkWriteSafe(pin, value);', '  Blynk.virtualWrite(pin, value);')

    s = replace_once(s, '''enum HouseStatus {\n  HOUSE_HOME,\n  HOUSE_AWAY\n};\n\nenum RequestState {''', '''enum HouseStatus {\n  HOUSE_HOME,\n  HOUSE_AWAY\n};\n\nenum OutsideSource {\n  OUTSIDE_SRC_WOKWI,\n  OUTSIDE_SRC_BLYNK\n};\n\nenum RequestState {''', "bedroom OutsideSource enum")
    s = replace_once(s, '''ThermalState blynkThermalState = THERMAL_COMFORT;\n\n// =====================================================\n// HELPERS''', '''ThermalState blynkThermalState = THERMAL_COMFORT;\n\nOutsideSource currentOutsideSource = OUTSIDE_SRC_WOKWI;\nint lastPhysicalOutsideScore = -1;\nconst int outsideChangeThreshold = 20;\nbool blynkOutsideInitialized = false;\n\n// =====================================================\n// HELPERS''', "bedroom outside globals")
    s = regex_once(s, r'''int rawToBrightnessScore\(int raw\) \{.*?\n\}\n\nInsideState classifyInside''', '''int rawToBrightnessScore(int raw) {\n  raw = constrain(raw, 0, 4095);\n  int inverted = 4095 - raw;\n  return map(inverted, 0, 4095, 0, 1000);\n}\n\nint getUnifiedOutsideScore(int rawOutside) {\n  int physicalOutsideScore = rawToBrightnessScore(rawOutside);\n  if (lastPhysicalOutsideScore < 0) lastPhysicalOutsideScore = physicalOutsideScore;\n  if (abs(physicalOutsideScore - lastPhysicalOutsideScore) > outsideChangeThreshold) currentOutsideSource = OUTSIDE_SRC_WOKWI;\n  lastPhysicalOutsideScore = physicalOutsideScore;\n  if (currentOutsideSource == OUTSIDE_SRC_BLYNK) return constrain(blynkOutsideScore, 0, 1000);\n  return physicalOutsideScore;\n}\n\nInsideState classifyInside''', "bedroom unified outside helper")
    s = replace_once(s, 'String serialBuffer = "";\nconst String SYSTEM_PIN', 'String serialBuffer = "";\nconst unsigned int SERIAL_BUFFER_MAX = 24;\nconst String SYSTEM_PIN', "bedroom serial bound constant")
    s = replace_once(s, '''    } else {\n      serialBuffer += c;\n    }\n''', '''    } else {\n      if (serialBuffer.length() < SERIAL_BUFFER_MAX) {\n        serialBuffer += c;\n      }\n    }\n''', "bedroom serial bound")
    s = regex_once(s, r'''BLYNK_CONNECTED\(\) \{\n  Blynk\.syncVirtual\(V3\);\n\}\n\nBLYNK_WRITE\(V3\) \{\n  blynkOutsideScore = constrain\(param\.asInt\(\), 0, 1000\);\n\}''', '''BLYNK_CONNECTED() {\n#if ENABLE_BLYNK\n  Blynk.syncVirtual(V3);\n#endif\n}\n\nBLYNK_WRITE(V3) {\n  blynkOutsideScore = constrain(param.asInt(), 0, 1000);\n  if (!blynkOutsideInitialized) {\n    blynkOutsideInitialized = true;\n    Serial.print("Blynk V3 synced (cached only): ");\n    Serial.println(blynkOutsideScore);\n    return;\n  }\n  currentOutsideSource = OUTSIDE_SRC_BLYNK;\n  Serial.print("Outside brightness set from Blynk V3: ");\n  Serial.println(blynkOutsideScore);\n}''', "bedroom Blynk V3")
    s = replace_once(s, '''  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);\n  timer.setInterval(3000L, sendToBlynk);\n''', '''#if ENABLE_BLYNK\n  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);\n  timer.setInterval(3000L, sendToBlynk);\n#else\n  Serial.println("Blynk disabled (public default); local Wokwi logic remains active.");\n#endif\n''', "bedroom setup Blynk")
    s = replace_once(s, '''  lcd.init();\n  lcd.backlight();\n''', '''  lcd.begin(16, 2, Wire);\n  lcd.setBacklight(255);\n''', "bedroom LCD init")
    s = replace_once(s, '  Serial.println("Blynk connected.");\n', '  Serial.println(ENABLE_BLYNK ? "Blynk enabled." : "Blynk disabled (public default).");\n', "bedroom startup Blynk message")
    s = replace_once(s, '''  Blynk.run();\n  timer.run();\n''', '''#if ENABLE_BLYNK\n  Blynk.run();\n  timer.run();\n#endif\n''', "bedroom loop Blynk")
    s = replace_once(s, '''  // IMPORTANT:\n  // Outside brightness is controlled by Blynk slider V3.\n  // The real outside LDR raw value is only kept for Serial debug.\n  int outsideScore = constrain(blynkOutsideScore, 0, 1000);\n''', '''  // Outside brightness is physical-Wokwi first. If Blynk is enabled,\n  // V3 may take control until the physical outside LDR moves again.\n  int outsideScore = getUnifiedOutsideScore(rawOutside);\n''', "bedroom outside score")
    s = replace_once(s, '''  Serial.print("LDR1 outside raw debug: ");\n  Serial.print(rawOutside);\n  Serial.print(" | outside Blynk simulated score: ");\n  Serial.println(outsideScore);\n''', '''  Serial.print("LDR1 outside raw: ");\n  Serial.print(rawOutside);\n  Serial.print(" | active outside score: ");\n  Serial.print(outsideScore);\n  Serial.print(" | source: ");\n  Serial.println(currentOutsideSource == OUTSIDE_SRC_BLYNK ? "BLYNK_V3" : "WOKWI_LDR");\n''', "bedroom outside status")
    s = replace_once(s, '  lcd.clear();\n\n  if (intruderAlert) {', '  if (intruderAlert) {', "bedroom LCD clear")
    path.write_text(s, encoding="utf-8")
    print("patched bedroom sketch")


def patch_kitchen() -> None:
    path = ROOT / "wokwi/kitchen-living-room/sketch.ino"
    s = path.read_text(encoding="utf-8")
    s = replace_once(s, '#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"\n', '#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"\n\n// Public portfolio default: local Wokwi logic must not depend on cloud credentials.\n#define ENABLE_BLYNK 0\n', "kitchen ENABLE_BLYNK")
    s = replace_once(s, '#include <LiquidCrystal_I2C.h>', '#include <LiquidCrystal_PCF8574.h>', "kitchen LCD include")
    s = replace_once(s, 'LiquidCrystal_I2C lcd(0x27, 16, 2);', 'LiquidCrystal_PCF8574 lcd(0x27);', "kitchen LCD object")
    s = replace_once(s, '''#define USE_EDGE_IMPULSE_RUNTIME 0\n\n#if USE_EDGE_IMPULSE_RUNTIME\n#include <albertoreyes837-project-1_inferencing.h>\n#endif''', '''#define USE_EDGE_IMPULSE_RUNTIME 0\n\n// If you enable the generated runtime, change this to your own exported header.\n#define EDGE_IMPULSE_INFERENCING_HEADER "your_project_inferencing.h"\n\n#if USE_EDGE_IMPULSE_RUNTIME\n#include EDGE_IMPULSE_INFERENCING_HEADER\n#endif''', "kitchen generic EI header")
    s = replace_once(s, 'BlynkTimer timer;\n', '''BlynkTimer timer;\n\ntemplate <typename T>\nvoid blynkWriteSafe(int pin, const T &value) {\n#if ENABLE_BLYNK\n  Blynk.virtualWrite(pin, value);\n#else\n  (void)pin;\n  (void)value;\n#endif\n}\n''', "kitchen Blynk helper")
    s = s.replace('Blynk.virtualWrite(', 'blynkWriteSafe(')
    s = s.replace('  blynkWriteSafe(pin, value);', '  Blynk.virtualWrite(pin, value);')
    s = regex_once(s, r'''void updateEnvironmentAI\(int gasScore\) \{.*?\n\}\n\n// =====================================================\n// BLYNK SEND DATA''', '''void updateEnvironmentAI(int gasScore) {\n  EnvironmentStatus ruleStatus = ruleEnvironmentStatus(gasScore);\n  if (isMq2WarmingUp() || !dhtValid) {\n    currentEnvironmentStatus = ruleStatus;\n    lastMlEnvironmentStatus = ENV_UNKNOWN;\n    mlValid = false;\n    mlConfidence = 0.0;\n    return;\n  }\n#if USE_EDGE_IMPULSE_RUNTIME\n  if (millis() - lastMlTime >= mlEvery) {\n    lastMlTime = millis();\n    EnvironmentStatus predictedStatus;\n    float confidence;\n    mlValid = runEnvironmentClassifier(gasScore, predictedStatus, confidence);\n    mlConfidence = confidence;\n    if (mlValid) {\n      lastMlEnvironmentStatus = predictedStatus;\n      Serial.print("ML environmental status: ");\n      Serial.print(environmentStatusStr(predictedStatus));\n      Serial.print(" confidence=");\n      Serial.println(confidence, 3);\n    } else {\n      lastMlEnvironmentStatus = ENV_UNKNOWN;\n      Serial.println("ML environmental status: invalid or low confidence");\n    }\n  }\n  currentEnvironmentStatus = mlValid ? moreSevereEnvironment(ruleStatus, lastMlEnvironmentStatus) : ruleStatus;\n#else\n  currentEnvironmentStatus = ruleStatus;\n  lastMlEnvironmentStatus = ENV_UNKNOWN;\n  mlValid = false;\n  mlConfidence = 0.0;\n  if (millis() - lastMlTime >= mlEvery) {\n    lastMlTime = millis();\n    Serial.print("ML runtime disabled; environmental status is rule-derived: ");\n    Serial.println(environmentStatusStr(ruleStatus));\n  }\n#endif\n}\n\n// =====================================================\n// BLYNK SEND DATA''', "kitchen updateEnvironmentAI")
    s = replace_once(s, '''  // Optional Blynk datastreams for AI status\n  blynkWriteSafe(V29, environmentStatusStr(currentEnvironmentStatus));\n  blynkWriteSafe(V30, mlConfidence);\n  blynkWriteSafe(V31, mlValid ? environmentStatusStr(lastMlEnvironmentStatus) : "INVALID");\n''', '''  // Environmental state is always available. ML fields only represent real inference.\n  blynkWriteSafe(V29, environmentStatusStr(currentEnvironmentStatus));\n#if USE_EDGE_IMPULSE_RUNTIME\n  if (mlValid) {\n    blynkWriteSafe(V30, String(mlConfidence, 3));\n    blynkWriteSafe(V31, environmentStatusStr(lastMlEnvironmentStatus));\n  } else {\n    blynkWriteSafe(V30, "INVALID");\n    blynkWriteSafe(V31, "INVALID");\n  }\n#else\n  blynkWriteSafe(V30, "N/A");\n  blynkWriteSafe(V31, "DISABLED");\n#endif\n''', "kitchen Blynk ML fields")
    s = replace_once(s, '''  Serial.print("AI/environment status: ");\n  Serial.println(environmentStatusStr(currentEnvironmentStatus));\n\n  Serial.print("Last ML prediction: ");\n  Serial.println(environmentStatusStr(lastMlEnvironmentStatus));\n\n  Serial.print("ML valid: ");\n  Serial.println(mlValid ? "YES" : "NO");\n\n  Serial.print("ML confidence: ");\n  Serial.println(mlConfidence, 3);\n''', '''  Serial.print("Environmental status: ");\n  Serial.println(environmentStatusStr(currentEnvironmentStatus));\n\n#if USE_EDGE_IMPULSE_RUNTIME\n  Serial.print("Last ML prediction: ");\n  Serial.println(mlValid ? environmentStatusStr(lastMlEnvironmentStatus) : "INVALID");\n  Serial.print("ML valid: ");\n  Serial.println(mlValid ? "YES" : "NO");\n  Serial.print("ML confidence: ");\n  if (mlValid) Serial.println(mlConfidence, 3);\n  else Serial.println("INVALID");\n#else\n  Serial.println("Last ML prediction: DISABLED");\n  Serial.println("ML valid: NO (runtime disabled)");\n  Serial.println("ML confidence: N/A");\n#endif\n''', "kitchen serial ML fields")
    s = regex_once(s, r'''BLYNK_CONNECTED\(\) \{\n  Blynk\.syncVirtual\(V3\);\n\}''', '''BLYNK_CONNECTED() {\n#if ENABLE_BLYNK\n  Blynk.syncVirtual(V3);\n#endif\n}''', "kitchen Blynk connected")
    s = replace_once(s, '''  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);\n  timer.setInterval(3000L, sendToBlynk);\n''', '''#if ENABLE_BLYNK\n  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);\n  timer.setInterval(3000L, sendToBlynk);\n#else\n  Serial.println("Blynk disabled (public default); local Wokwi logic remains active.");\n#endif\n''', "kitchen setup Blynk")
    s = replace_once(s, '''  lcd.init();\n  lcd.backlight();\n  lcd.clear();\n''', '''  lcd.begin(16, 2, Wire);\n  lcd.setBacklight(255);\n  lcd.clear();\n''', "kitchen LCD init")
    s = replace_once(s, '  lcdPrint2("Kitchen/Living", "AI Starting...");\n', '  lcdPrint2("Kitchen/Living", "Starting...");\n', "kitchen LCD startup")
    s = replace_once(s, '  Serial.println("Kitchen / Living Room Module Started - Blynk + Edge Impulse Version");\n', '  Serial.println("Kitchen / Living Room Module Started");\n  Serial.println(ENABLE_BLYNK ? "Blynk enabled." : "Blynk disabled (public default).");\n  Serial.println(USE_EDGE_IMPULSE_RUNTIME ? "Edge Impulse runtime enabled." : "Edge Impulse runtime disabled; rules are authoritative.");\n', "kitchen startup text")
    s = replace_once(s, '  Serial.println("V29 AI/environment status | V30 ML confidence | V31 raw ML prediction");\n', '  Serial.println("V29 environmental status | V30 ML confidence | V31 raw ML prediction");\n', "kitchen V29 message")
    s = replace_once(s, '''  Blynk.run();\n  timer.run();\n''', '''#if ENABLE_BLYNK\n  Blynk.run();\n  timer.run();\n#endif\n''', "kitchen loop Blynk")
    s = replace_once(s, '  // Edge Impulse environmental safety classifier.\n  updateEnvironmentAI(gasScore);\n', '  // Deterministic rules are authoritative; optional ML can only add severity when enabled.\n  updateEnvironmentAI(gasScore);\n', "kitchen loop comment")
    path.write_text(s, encoding="utf-8")
    print("patched kitchen sketch")


def patch_diagrams() -> None:
    bedroom_path = ROOT / "wokwi/bedroom/diagram.json"
    bedroom = json.loads(bedroom_path.read_text(encoding="utf-8"))
    for part in bedroom["parts"]:
        if part.get("type") == "wokwi-dht22":
            part.setdefault("attrs", {})["temperature"] = "24"
            part["attrs"]["humidity"] = "50"
    bedroom_path.write_text(json.dumps(bedroom, indent=2) + "\n", encoding="utf-8")

    kitchen_path = ROOT / "wokwi/kitchen-living-room/diagram.json"
    kitchen = json.loads(kitchen_path.read_text(encoding="utf-8"))
    for part in kitchen["parts"]:
        if part.get("type") == "wokwi-dht22":
            part.setdefault("attrs", {})["temperature"] = "24"
            part["attrs"]["humidity"] = "50"
        if part.get("type") == "wokwi-text" and part.get("id") == "text6":
            part.setdefault("attrs", {})["text"] = "Room Modes\n(Normal, Privacy, ECO)"
    kitchen_path.write_text(json.dumps(kitchen, indent=2) + "\n", encoding="utf-8")
    print("patched Wokwi diagrams")


def cleanup_helper() -> None:
    for rel in ("scripts/apply_hardening_v2.py", ".github/workflows/apply-hardening-v2.yml"):
        p = ROOT / rel
        if p.exists():
            p.unlink()
            print(f"removed helper {rel}")


def main() -> int:
    patch_bedroom()
    patch_kitchen()
    patch_diagrams()
    cleanup_helper()
    print("hardening V2 patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
