#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = '''template <typename T>\nvoid blynkWriteSafe(int pin, const T &value) {\n#if ENABLE_BLYNK\n  Blynk.virtualWrite(pin, value);\n#else\n  (void)pin;\n  (void)value;\n#endif\n}\n'''
NEW = '''// Compile-time wrapper: avoids cloud writes when Blynk is disabled without\n// introducing a function before the custom enum declarations (important for\n// Arduino's automatic prototype generation).\n#if ENABLE_BLYNK\n#define blynkWriteSafe(pin, value) Blynk.virtualWrite((pin), (value))\n#else\n#define blynkWriteSafe(pin, value) do { (void)(pin); } while (0)\n#endif\n'''

for rel in ("wokwi/bedroom/sketch.ino", "wokwi/kitchen-living-room/sketch.ino"):
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit(f"{rel}: expected exactly one templated helper")
    p.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"patched {rel}")

for rel in ("scripts/fix_blynk_helper_macro.py", ".github/workflows/apply-blynk-macro-fix.yml"):
    p = ROOT / rel
    if p.exists():
        p.unlink()
        print(f"removed helper {rel}")
