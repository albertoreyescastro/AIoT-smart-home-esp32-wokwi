#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_TEMPLATE_NAME "Kitchen and Living Room"
#define BLYNK_AUTH_TOKEN "YOUR_BLYNK_AUTH_TOKEN"

// Public portfolio default: local Wokwi logic must not depend on cloud credentials.
#define ENABLE_BLYNK 0

#define BLYNK_PRINT Serial

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>

#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>
#include <DHT.h>

// Edge Impulse runtime is optional in the public version.
// Keep it disabled for Wokwi unless the exported Edge Impulse Arduino library
// is installed and tested in the simulation/hardware environment.
#ifndef USE_EDGE_IMPULSE_RUNTIME
#define USE_EDGE_IMPULSE_RUNTIME 0
#endif

// If you enable the generated runtime, change this to your own exported header.
#ifndef EDGE_IMPULSE_INFERENCING_HEADER
#define EDGE_IMPULSE_INFERENCING_HEADER "your_project_inferencing.h"
#endif

#if USE_EDGE_IMPULSE_RUNTIME
#include EDGE_IMPULSE_INFERENCING_HEADER
#endif

#include <string.h>

// -------------------- WIFI --------------------
// Wokwi simulation Wi-Fi credentials.
// For deployment on real hardware, replace these with a real network.
char ssid[] = "Wokwi-GUEST";
char pass[] = "";

BlynkTimer timer;

// Compile-time wrapper: avoids cloud writes when Blynk is disabled without
// introducing a function before the custom enum declarations (important for
// Arduino's automatic prototype generation).
#if ENABLE_BLYNK
#define blynkWriteSafe(pin, value) Blynk.virtualWrite((pin), (value))
#else
#define blynkWriteSafe(pin, value) do { (void)(pin); } while (0)
#endif

// =====================================================
// KITCHEN / LIVING ROOM MODULE - BLYNK + EDGE IMPULSE
// Smart Home for Adaptive Lighting, Safety, Privacy
// and Energy Management
//
// AI model input:
//   gas_score, temperature, humidity
//
// AI model output:
//   NORMAL
//   COOKING_FUMES
//   GAS_DANGER
//   HEAT_ANOMALY
//   GAS_HEAT_EMERGENCY
//
// Important:
// The old rule-based safety logic is NOT removed.
// Edge Impulse is added as a hybrid AI layer.
// If AI is invalid or low confidence, rule-based logic remains active.
// =====================================================

// -------------------- PINS --------------------
#define PIR_PIN               5
#define LDR_INSIDE_PIN        4
#define LDR_OUTSIDE_PIN       6
#define MANUAL_BUTTON_PIN     7
#define MAIN_LAMP_PIN         8

#define ROOM_MODE_BTN_PIN     9
#define PROFILE_BTN_PIN       10
#define HOUSE_BTN_PIN         11
#define CHILD_BTN_PIN         12
#define BUZZER_PIN            13

#define AC_RELAY_PIN          14
#define DHT_PIN               15
#define DHTTYPE               DHT22

#define LCD_SDA_PIN           16
#define LCD_SCL_PIN           17
#define SERVO_PIN             18

#define MQ2_PIN               1

#define SPRINKLER_LED_PIN     2

const bool AC_RELAY_ACTIVE_LOW = false;

// Wokwi MQ2 analog output increases when gas concentration increases.
// Keep this false unless your exact wiring/sensor behaves inverted.
const bool MQ2_INVERT_READING = false;

// -------------------- LIGHT THRESHOLDS --------------------
int insideDarkMax   = 60;
int insideMediumMax = 180;

int outsideNightMax = 120;
int outsideDayMin   = 500;

int manualLampBoost = 260;

// -------------------- GAS THRESHOLDS --------------------
int gasWarnThresholdBase   = 420;
int gasDangerThresholdBase = 850;
int gasSevereThresholdBase = 970;

unsigned long mq2WarmupMs               = 15000;
unsigned long gasWarnPersistMs          = 2500;
unsigned long gasDangerPersistMs        = 8000;
unsigned long gasSeverePersistMs        = 1200;
unsigned long gasMinFumesBeforeDangerMs = 8000;
unsigned long gasClearPersistMs         = 5000;

// -------------------- EMERGENCY COOLING / SPRINKLER --------------------
float emergencyCoolingTempC = 55.0;
unsigned long sprinklerBlinkPeriodMs = 160;

// -------------------- TIMING --------------------
unsigned long motionHoldMsStandard = 20000;
unsigned long serialEvery          = 5000;
unsigned long lcdEvery             = 700;
unsigned long dhtEvery             = 2000;

unsigned long awayMotionWindowMs   = 15000;

// -------------------- EDGE IMPULSE TIMING --------------------
unsigned long mlEvery = 3000;
const float ML_MIN_CONFIDENCE = 0.60;

// Wokwi can crash when running the full Edge Impulse runtime/TFLite/EON code
// inside the simulator. The compile-time flag USE_EDGE_IMPULSE_RUNTIME is set
// near the include section at the top of this file.

// -------------------- SERVO ANGLES --------------------
int blindClosedAngle = 0;
int blindHalfAngle   = 90;
int blindOpenAngle   = 180;

// -------------------- LCD / DHT --------------------
LiquidCrystal_PCF8574 lcd(0x27);
DHT dht(DHT_PIN, DHTTYPE);

// -------------------- STATES --------------------
enum InsideState {
  INSIDE_DARK,
  INSIDE_MEDIUM,
  INSIDE_BRIGHT
};

enum OutsideState {
  OUTSIDE_NIGHT,
  OUTSIDE_TRANSITION,
  OUTSIDE_DAY
};

enum BlindState {
  BLINDS_CLOSED,
  BLINDS_HALF,
  BLINDS_OPEN
};

enum ACState {
  AC_OFF,
  AC_ON
};

enum ThermalState {
  THERMAL_COOL,
  THERMAL_COMFORT,
  THERMAL_WARM
};

enum GasStatus {
  GAS_NORMAL,
  GAS_COOKING_FUMES,
  GAS_DANGER
};

enum EnvironmentStatus {
  ENV_NORMAL,
  ENV_COOKING_FUMES,
  ENV_GAS_DANGER,
  ENV_HEAT_ANOMALY,
  ENV_GAS_HEAT_EMERGENCY,
  ENV_UNKNOWN
};

enum RoomMode {
  NORMAL_MODE,
  PRIVACY_MODE,
  ECO_MODE
};

enum BaseProfile {
  PROFILE_STANDARD,
  PROFILE_ELDERLY
};

enum HouseStatus {
  HOUSE_HOME,
  HOUSE_AWAY
};

enum RequestState {
  REQ_NONE,
  REQ_CHILD_EXIT_PIN,
  REQ_AWAY_DISARM_PIN,
  REQ_INTRUDER_CLEAR_WORD,
  REQ_AWAY_PET_QUERY
};

enum OutsideSource {
  OUTSIDE_SRC_WOKWI,
  OUTSIDE_SRC_BLYNK
};

// -------------------- ACTIVE STATES --------------------
RoomMode currentMode = NORMAL_MODE;
BaseProfile currentBaseProfile = PROFILE_STANDARD;
HouseStatus currentHouseStatus = HOUSE_HOME;
RequestState currentRequest = REQ_NONE;

bool childMode = false;
bool petAtHome = false;

bool suspiciousMotion = false;
bool intruderAlert = false;
bool pinAlert = false;

// -------------------- GLOBALS --------------------
Servo blindsServo;

unsigned long systemStartTime = 0;
unsigned long lastMotionTime = 0;
bool motionSeenOnce = false;
unsigned long lastSerialTime = 0;
unsigned long lastLcdTime = 0;
unsigned long lastDhtTime = 0;

int awayMotionCount = 0;
unsigned long awayWindowStart = 0;
bool lastPirState = false;

bool manualLampOn = false;

float currentTempC = 24.0;
float currentHumidity = 50.0;
bool dhtValid = false;

// Gas state + timers
GasStatus currentGasStatus = GAS_NORMAL;
unsigned long gasWarningSince = 0;
unsigned long gasDangerSince  = 0;
unsigned long gasSevereSince  = 0;
unsigned long gasNormalSince  = 0;
unsigned long gasFumesSince   = 0;

// Edge Impulse / AI state
EnvironmentStatus currentEnvironmentStatus = ENV_UNKNOWN;
EnvironmentStatus lastMlEnvironmentStatus = ENV_UNKNOWN;
bool mlValid = false;
float mlConfidence = 0.0;
unsigned long lastMlTime = 0;

// Debounce states
bool manualLastReading = HIGH;
bool manualStableState = HIGH;
unsigned long manualLastDebounce = 0;

bool roomLastReading = HIGH;
bool roomStableState = HIGH;
unsigned long roomLastDebounce = 0;

bool profileLastReading = HIGH;
bool profileStableState = HIGH;
unsigned long profileLastDebounce = 0;

bool houseLastReading = HIGH;
bool houseStableState = HIGH;
unsigned long houseLastDebounce = 0;

bool childLastReading = HIGH;
bool childStableState = HIGH;
unsigned long childLastDebounce = 0;

const unsigned long debounceDelay = 50;

BlindState currentBlindState = BLINDS_CLOSED;
ACState currentACState = AC_OFF;

// Auth system
String serialBuffer = "";
const unsigned int SERIAL_BUFFER_MAX = 24;
const String SYSTEM_PIN  = "1234";        // Demo PIN for simulation
const String SECRET_WORD = "OKAY";        // Demo secret word for simulation
int wrongPinAttempts = 0;

// LCD cache
String lastLcdLine1 = "";
String lastLcdLine2 = "";

// -------------------- BLYNK CACHED VALUES --------------------
int blynkInsideScore = 0;
int blynkOutsideScore = 0;
int blynkGasScore = 0;
int blynkPirRaw = 0;
bool blynkPresence = false;

InsideState blynkInsideState = INSIDE_DARK;
OutsideState blynkOutsideState = OUTSIDE_NIGHT;
ThermalState blynkThermalState = THERMAL_COMFORT;

// -------------------- OUTSIDE LIGHT SOURCE CONTROL --------------------
OutsideSource currentOutsideSource = OUTSIDE_SRC_WOKWI;
int lastPhysicalOutsideScore = -1;
const int outsideChangeThreshold = 20;
bool blynkOutsideInitialized = false;

// =====================================================
// HELPERS
// =====================================================
bool isMq2WarmingUp() {
  if (mq2WarmupMs == 0) return false;
  return (millis() - systemStartTime) < mq2WarmupMs;
}

int rawToBrightnessScore(int raw) {
  raw = constrain(raw, 0, 4095);
  int inverted = 4095 - raw;
  return map(inverted, 0, 4095, 0, 1000);
}

int getUnifiedOutsideScore(int rawOutside) {
  int physicalOutsideScore = rawToBrightnessScore(rawOutside);

  if (lastPhysicalOutsideScore < 0) {
    lastPhysicalOutsideScore = physicalOutsideScore;
  }

  // If the physical outside LDR changed noticeably, return control to Wokwi
  if (abs(physicalOutsideScore - lastPhysicalOutsideScore) > outsideChangeThreshold) {
    currentOutsideSource = OUTSIDE_SRC_WOKWI;
  }

  lastPhysicalOutsideScore = physicalOutsideScore;

  if (currentOutsideSource == OUTSIDE_SRC_BLYNK) {
    return constrain(blynkOutsideScore, 0, 1000);
  }

  return physicalOutsideScore;
}

int rawToGasScore(int raw) {
  raw = constrain(raw, 0, 4095);
  int score = map(raw, 0, 4095, 0, 1000);

  if (MQ2_INVERT_READING) {
    score = 1000 - score;
  }

  return constrain(score, 0, 1000);
}

bool environmentHasGasIssue(EnvironmentStatus s) {
  return (
    s == ENV_COOKING_FUMES ||
    s == ENV_GAS_DANGER ||
    s == ENV_GAS_HEAT_EMERGENCY
  );
}

bool emergencyCoolingActive() {
  if (!dhtValid) return false;
  return currentEnvironmentStatus == ENV_GAS_HEAT_EMERGENCY;
}

InsideState classifyInside(int score) {
  if (score < insideDarkMax) return INSIDE_DARK;
  if (score < insideMediumMax) return INSIDE_MEDIUM;
  return INSIDE_BRIGHT;
}

OutsideState classifyOutside(int score) {
  if (score < outsideNightMax) return OUTSIDE_NIGHT;
  if (score < outsideDayMin)   return OUTSIDE_TRANSITION;
  return OUTSIDE_DAY;
}

unsigned long getEffectiveMotionHoldMs() {
  if (childMode) return 45000;
  if (currentBaseProfile == PROFILE_ELDERLY) return 60000;
  return motionHoldMsStandard;
}

bool presenceActive() {
  if (!motionSeenOnce) return false;
  return (millis() - lastMotionTime) < getEffectiveMotionHoldMs();
}

int getBlindDaylightBoost(BlindState blindState, OutsideState outsideState, int outsideScore) {
  if (outsideState == OUTSIDE_NIGHT) return 0;

  if (blindState == BLINDS_OPEN) return outsideScore / 2;
  if (blindState == BLINDS_HALF) return outsideScore / 4;
  return 0;
}

String pad16(String s) {
  if (s.length() > 16) return s.substring(0, 16);
  while (s.length() < 16) s += " ";
  return s;
}

void lcdPrint2(String line1, String line2) {
  line1 = pad16(line1);
  line2 = pad16(line2);

  if (line1 != lastLcdLine1) {
    lcd.setCursor(0, 0);
    lcd.print(line1);
    lastLcdLine1 = line1;
  }

  if (line2 != lastLcdLine2) {
    lcd.setCursor(0, 1);
    lcd.print(line2);
    lastLcdLine2 = line2;
  }
}

const char* insideStateStr(InsideState s) {
  if (s == INSIDE_DARK) return "DARK";
  if (s == INSIDE_MEDIUM) return "MEDIUM";
  return "BRIGHT";
}

const char* outsideStateStr(OutsideState s) {
  if (s == OUTSIDE_NIGHT) return "NIGHT";
  if (s == OUTSIDE_TRANSITION) return "TRANSITION";
  return "DAY";
}

const char* blindStateStr(BlindState s) {
  if (s == BLINDS_CLOSED) return "CLOSED";
  if (s == BLINDS_HALF) return "HALF";
  return "OPEN";
}

const char* acStateStr(ACState s) {
  return (s == AC_ON) ? "ON" : "OFF";
}

const char* thermalStateStr(ThermalState s) {
  if (s == THERMAL_COOL) return "COOL";
  if (s == THERMAL_WARM) return "WARM";
  return "COMFORT";
}

const char* gasStatusStr(GasStatus s) {
  if (s == GAS_NORMAL) return "NORMAL";
  if (s == GAS_COOKING_FUMES) return "COOKING_FUMES";
  return "GAS_DANGER";
}

const char* gasStatusShort(GasStatus s) {
  if (s == GAS_NORMAL) return "OK";
  if (s == GAS_COOKING_FUMES) return "FUMES";
  return "DANGER";
}

const char* environmentStatusStr(EnvironmentStatus s) {
  if (s == ENV_NORMAL) return "NORMAL";
  if (s == ENV_COOKING_FUMES) return "COOKING_FUMES";
  if (s == ENV_GAS_DANGER) return "GAS_DANGER";
  if (s == ENV_HEAT_ANOMALY) return "HEAT_ANOMALY";
  if (s == ENV_GAS_HEAT_EMERGENCY) return "GAS_HEAT_EMERGENCY";
  return "UNKNOWN";
}

const char* environmentStatusShort(EnvironmentStatus s) {
  if (s == ENV_NORMAL) return "OK";
  if (s == ENV_COOKING_FUMES) return "FUMES";
  if (s == ENV_GAS_DANGER) return "GAS";
  if (s == ENV_HEAT_ANOMALY) return "HEAT";
  if (s == ENV_GAS_HEAT_EMERGENCY) return "GAS+HEAT";
  return "UNK";
}

EnvironmentStatus labelToEnvironmentStatus(const char* label) {
  if (strcmp(label, "NORMAL") == 0) return ENV_NORMAL;
  if (strcmp(label, "COOKING_FUMES") == 0) return ENV_COOKING_FUMES;
  if (strcmp(label, "GAS_DANGER") == 0) return ENV_GAS_DANGER;
  if (strcmp(label, "HEAT_ANOMALY") == 0) return ENV_HEAT_ANOMALY;
  if (strcmp(label, "GAS_HEAT_EMERGENCY") == 0) return ENV_GAS_HEAT_EMERGENCY;
  return ENV_UNKNOWN;
}



const char* modeStr(RoomMode m) {
  if (m == NORMAL_MODE) return "NORMAL";
  if (m == PRIVACY_MODE) return "PRIVACY";
  return "ECO";
}

const char* modeShort(RoomMode m) {
  if (m == NORMAL_MODE) return "NORM";
  if (m == PRIVACY_MODE) return "PRIV";
  return "ECO";
}

const char* houseStr(HouseStatus h) {
  return (h == HOUSE_HOME) ? "HOME" : "AWAY";
}

const char* houseShort(HouseStatus h) {
  return (h == HOUSE_HOME) ? "HOME" : "AWAY";
}

const char* baseProfileStr(BaseProfile p) {
  return (p == PROFILE_STANDARD) ? "STANDARD" : "ELDERLY";
}

const char* effectiveProfileStr() {
  if (childMode) return "CHILD";
  return baseProfileStr(currentBaseProfile);
}

const char* effectiveProfileShort() {
  if (childMode) return "CHLD";
  return (currentBaseProfile == PROFILE_STANDARD) ? "STD" : "ELDR";
}

String presenceLabel(bool presence, InsideState insideState) {
  if (!presence) return "NO";
  if (insideState == INSIDE_DARK) return "YES (dark)";
  return "YES";
}

String activeAlertText() {
  if (emergencyCoolingActive()) return "GAS + HIGH TEMP";
  if (currentEnvironmentStatus == ENV_HEAT_ANOMALY) return "HEAT ANOMALY";
  if (currentGasStatus == GAS_DANGER || currentEnvironmentStatus == ENV_GAS_DANGER) return "GAS DANGER";
  if (intruderAlert) return "INTRUDER ALERT";
  if (currentGasStatus == GAS_COOKING_FUMES || currentEnvironmentStatus == ENV_COOKING_FUMES) return "COOKING FUMES";
  if (suspiciousMotion) return "SUSPICIOUS MOTION";
  if (pinAlert) return "PIN ERROR ALERT";
  if (!dhtValid) return "DHT SENSOR ERROR";
  return "NONE";
}

void resetAwaySecurity() {
  suspiciousMotion = false;
  intruderAlert = false;
  awayMotionCount = 0;
  awayWindowStart = 0;
}

int getSuspiciousThreshold() {
  return petAtHome ? 2 : 1;
}

int getIntruderThreshold() {
  return petAtHome ? 5 : 3;
}

int getGasSensitivityAdjust() {
  if (childMode) return 40;
  if (currentBaseProfile == PROFILE_ELDERLY) return 30;
  return 0;
}

void resetGasTimers() {
  gasWarningSince = 0;
  gasDangerSince = 0;
  gasSevereSince = 0;
  gasNormalSince = 0;
  gasFumesSince = 0;
}

void setGasStatus(GasStatus newStatus) {
  if (newStatus == currentGasStatus) return;

  currentGasStatus = newStatus;
  Serial.print("Gas status changed to: ");
  Serial.println(gasStatusStr(currentGasStatus));

  if (currentGasStatus == GAS_COOKING_FUMES) {
    if (gasFumesSince == 0) gasFumesSince = millis();
    Serial.println("Cooking fumes / mild gas detected. Monitoring...");
  } else if (currentGasStatus == GAS_DANGER) {
    Serial.println("GAS DANGER ALERT");
  } else {
    resetGasTimers();
    Serial.println("Gas levels returned to normal.");
  }
}

void getGasThresholds(int &warningThreshold, int &dangerThreshold, int &severeThreshold, int &clearThreshold) {
  int adjust = getGasSensitivityAdjust();

  warningThreshold = max(0, gasWarnThresholdBase - adjust);
  dangerThreshold  = max(warningThreshold + 150, gasDangerThresholdBase - adjust);
  severeThreshold  = max(dangerThreshold + 80, gasSevereThresholdBase - adjust);
  clearThreshold   = max(0, warningThreshold - 70);
}

EnvironmentStatus ruleEnvironmentStatus() {
  if (isMq2WarmingUp()) return ENV_UNKNOWN;

  // Gas labels come only from the persistence-gated gas state machine.
  // A single raw MQ2 sample must never bypass those timers.
  if (currentGasStatus == GAS_DANGER) {
    if (dhtValid && currentTempC >= emergencyCoolingTempC) {
      return ENV_GAS_HEAT_EMERGENCY;
    }
    return ENV_GAS_DANGER;
  }

  if (currentGasStatus == GAS_COOKING_FUMES) {
    return ENV_COOKING_FUMES;
  }

  // If the DHT fails, gas monitoring remains available but heat classification
  // becomes unknown and the AC is forced off separately as a fail-safe.
  if (!dhtValid) return ENV_UNKNOWN;

  if (currentTempC >= emergencyCoolingTempC) {
    return ENV_HEAT_ANOMALY;
  }

  return ENV_NORMAL;
}

// =====================================================
// EDGE IMPULSE / AI INFERENCE
// =====================================================
#if USE_EDGE_IMPULSE_RUNTIME
bool runEnvironmentClassifier(int gasScore, EnvironmentStatus &statusOut, float &confidenceOut) {
  statusOut = ENV_UNKNOWN;
  confidenceOut = 0.0;

  if (isMq2WarmingUp()) return false;
  if (!dhtValid) return false;

  if (EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE != 3) {
    Serial.println("Edge Impulse input size mismatch. Expected 3 features.");
    return false;
  }

  float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE] = {
    (float)gasScore,
    currentTempC,
    currentHumidity
  };

  signal_t signal;

  int err = numpy::signal_from_buffer(
    features,
    EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE,
    &signal
  );

  if (err != 0) {
    Serial.print("Edge Impulse signal error: ");
    Serial.println(err);
    return false;
  }

  ei_impulse_result_t result = { 0 };

  EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

  if (res != EI_IMPULSE_OK) {
    Serial.print("Edge Impulse classifier error: ");
    Serial.println((int)res);
    return false;
  }

  float bestScore = 0.0;
  const char* bestLabel = "UNKNOWN";

  for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
    float value = result.classification[ix].value;

    if (value > bestScore) {
      bestScore = value;
      bestLabel = result.classification[ix].label;
    }
  }

  EnvironmentStatus predictedStatus = labelToEnvironmentStatus(bestLabel);

  statusOut = predictedStatus;
  confidenceOut = bestScore;

  if (predictedStatus == ENV_UNKNOWN) return false;
  if (bestScore < ML_MIN_CONFIDENCE) return false;

  return true;
}
#else
bool runEnvironmentClassifier(int gasScore, EnvironmentStatus &statusOut, float &confidenceOut) {
  (void)gasScore;
  statusOut = ENV_UNKNOWN;
  confidenceOut = 0.0;
  return false;
}
#endif

void updateEnvironmentAI(int gasScore) {
  // Safety/action state is always deterministic and persistence-gated.
  // ML is advisory telemetry only and never controls safety actuators.
  currentEnvironmentStatus = ruleEnvironmentStatus();

  if (isMq2WarmingUp() || !dhtValid) {
    lastMlEnvironmentStatus = ENV_UNKNOWN;
    mlValid = false;
    mlConfidence = 0.0;
    return;
  }

#if USE_EDGE_IMPULSE_RUNTIME
  if (millis() - lastMlTime >= mlEvery) {
    lastMlTime = millis();
    EnvironmentStatus predictedStatus;
    float confidence;
    mlValid = runEnvironmentClassifier(gasScore, predictedStatus, confidence);
    mlConfidence = confidence;

    if (mlValid) {
      lastMlEnvironmentStatus = predictedStatus;
      Serial.print("ML advisory status: ");
      Serial.print(environmentStatusStr(predictedStatus));
      Serial.print(" confidence=");
      Serial.println(confidence, 3);
    } else {
      lastMlEnvironmentStatus = ENV_UNKNOWN;
      Serial.println("ML advisory status: invalid or low confidence");
    }
  }
#else
  lastMlEnvironmentStatus = ENV_UNKNOWN;
  mlValid = false;
  mlConfidence = 0.0;

  if (millis() - lastMlTime >= mlEvery) {
    lastMlTime = millis();
    Serial.print("ML runtime disabled; actionable environmental status is persistence-gated: ");
    Serial.println(environmentStatusStr(currentEnvironmentStatus));
  }
#endif
}

// =====================================================
// BLYNK SEND DATA
// =====================================================
void sendToBlynk() {
  if (dhtValid) {
    blynkWriteSafe(V0, currentTempC);
    blynkWriteSafe(V1, currentHumidity);
  } else {
    blynkWriteSafe(V0, "N/A");
    blynkWriteSafe(V1, "N/A");
  }

  blynkWriteSafe(V2, blynkInsideScore);

  // V3 is not written here.
  // V3 can be used to override outside brightness from Blynk,
  // but the physical Wokwi outside LDR can also take control again.

  blynkWriteSafe(V4, blynkGasScore);
  blynkWriteSafe(V5, blynkPirRaw);
  blynkWriteSafe(V6, blynkPresence ? 1 : 0);

  blynkWriteSafe(V7, blindStateStr(currentBlindState));
  blynkWriteSafe(V8, manualLampOn ? "ON" : "OFF");
  blynkWriteSafe(V9, acStateStr(currentACState));
  blynkWriteSafe(V10, modeStr(currentMode));
  blynkWriteSafe(V11, effectiveProfileStr());
  blynkWriteSafe(V12, houseStr(currentHouseStatus));
  blynkWriteSafe(V13, activeAlertText());

  if (isMq2WarmingUp()) {
    blynkWriteSafe(V14, "WARMING");
  } else {
    blynkWriteSafe(V14, gasStatusStr(currentGasStatus));
  }

  blynkWriteSafe(V15, emergencyCoolingActive() ? "ON" : "OFF");
  blynkWriteSafe(V16, dhtValid ? thermalStateStr(blynkThermalState) : "INVALID");
  blynkWriteSafe(V17, insideStateStr(blynkInsideState));
  blynkWriteSafe(V18, outsideStateStr(blynkOutsideState));
  blynkWriteSafe(V19, presenceLabel(blynkPresence, blynkInsideState));

  blynkWriteSafe(V27, petAtHome ? "YES" : "NO");
  blynkWriteSafe(V28, awayMotionCount);

  // Environmental state is always available. ML fields only represent real inference.
  blynkWriteSafe(V29, environmentStatusStr(currentEnvironmentStatus));
#if USE_EDGE_IMPULSE_RUNTIME
  if (mlValid) {
    blynkWriteSafe(V30, String(mlConfidence, 3));
    blynkWriteSafe(V31, environmentStatusStr(lastMlEnvironmentStatus));
  } else {
    blynkWriteSafe(V30, "INVALID");
    blynkWriteSafe(V31, "INVALID");
  }
#else
  blynkWriteSafe(V30, "N/A");
  blynkWriteSafe(V31, "DISABLED");
#endif

  // Keep dashboard controls aligned with physical/Serial changes.
  blynkWriteSafe(V20, currentMode == NORMAL_MODE ? 0 : (currentMode == PRIVACY_MODE ? 1 : 2));
  blynkWriteSafe(V21, currentBaseProfile == PROFILE_ELDERLY ? 1 : 0);
  blynkWriteSafe(V22, manualLampOn ? 1 : 0);
  blynkWriteSafe(V23, childMode ? 1 : 0);
  blynkWriteSafe(V24, currentHouseStatus == HOUSE_AWAY ? 1 : 0);
  blynkWriteSafe(V25, petAtHome ? 1 : 0);
}

// -------------------- THERMAL HELPERS --------------------
void updateDHT() {
  if (millis() - lastDhtTime < dhtEvery) return;
  lastDhtTime = millis();

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    dhtValid = false;
    Serial.println("DHT read failed!");
    return;
  }

  currentTempC = temperature;
  currentHumidity = humidity;
  dhtValid = true;
}

float getACOnTempThreshold(RoomMode mode, bool childModeActive, BaseProfile baseProfile) {
  float t;

  if (mode == ECO_MODE) t = 28.5;
  else t = 27.0;

  if (childModeActive || baseProfile == PROFILE_ELDERLY) {
    t -= 1.0;
  }

  return t;
}

float getACOffTempThreshold(float onThreshold) {
  return onThreshold - 1.0;
}

ThermalState classifyThermal(float tempC, float onThreshold, float offThreshold) {
  if (tempC >= onThreshold) return THERMAL_WARM;
  if (tempC <= offThreshold - 1.0) return THERMAL_COOL;
  return THERMAL_COMFORT;
}

ACState decideAC(
  float tempC,
  float humidity,
  RoomMode mode,
  HouseStatus houseStatus,
  bool childModeActive,
  BaseProfile baseProfile,
  ACState previousState
) {
  if (!dhtValid) {
    return AC_OFF;
  }

  if (houseStatus == HOUSE_AWAY) {
    return AC_OFF;
  }

  // AC is disabled for gas/fumes states so it does not circulate contaminated air.
  // HEAT_ANOMALY alone is not treated as a gas issue, so the AC can still cool.
  if (currentGasStatus != GAS_NORMAL || environmentHasGasIssue(currentEnvironmentStatus)) {
    return AC_OFF;
  }

  float onThreshold  = getACOnTempThreshold(mode, childModeActive, baseProfile);
  float offThreshold = getACOffTempThreshold(onThreshold);

  bool highHumidity = humidity >= 70.0;
  bool humidityReleased = humidity < 65.0;

  if (previousState == AC_ON) {
    if (tempC <= offThreshold && humidityReleased) return AC_OFF;
    return AC_ON;
  }

  if (tempC >= onThreshold) return AC_ON;
  if (highHumidity && tempC >= offThreshold) return AC_ON;

  return AC_OFF;
}

// -------------------- GAS LOGIC --------------------
void updateGasStatus(int gasScore) {
  unsigned long now = millis();

  if (isMq2WarmingUp()) {
    resetGasTimers();
    currentGasStatus = GAS_NORMAL;
    return;
  }

  int warningThreshold, dangerThreshold, severeThreshold, clearThreshold;
  getGasThresholds(warningThreshold, dangerThreshold, severeThreshold, clearThreshold);

  // Clear only after the reading has remained below the hysteresis boundary.
  if (gasScore <= clearThreshold) {
    gasWarningSince = 0;
    gasDangerSince = 0;
    gasSevereSince = 0;

    if (currentGasStatus != GAS_NORMAL) {
      if (gasNormalSince == 0) gasNormalSince = now;
      if (now - gasNormalSince >= gasClearPersistMs) {
        setGasStatus(GAS_NORMAL);
      }
    } else {
      gasNormalSince = 0;
      gasFumesSince = 0;
    }
    return;
  }

  gasNormalSince = 0;

  if (gasScore < warningThreshold) {
    gasWarningSince = 0;
    gasDangerSince = 0;
    gasSevereSince = 0;
    return;
  }

  // Start persistence timers, but do not change actionable state yet.
  if (gasWarningSince == 0) gasWarningSince = now;

  if (gasScore >= dangerThreshold) {
    if (gasDangerSince == 0) gasDangerSince = now;
    if (gasFumesSince == 0) gasFumesSince = now;
  } else {
    gasDangerSince = 0;
  }

  // Very high readings use a shorter, still persistence-gated emergency path.
  if (gasScore >= severeThreshold) {
    if (gasSevereSince == 0) gasSevereSince = now;
    if (now - gasSevereSince >= gasSeverePersistMs) {
      setGasStatus(GAS_DANGER);
    }
    return;
  }
  gasSevereSince = 0;

  // Warning/fumes state requires sustained elevation.
  if (currentGasStatus == GAS_NORMAL && now - gasWarningSince >= gasWarnPersistMs) {
    setGasStatus(GAS_COOKING_FUMES);
  }

  // Normal danger path requires sustained danger and sustained fumes exposure.
  if (gasScore >= dangerThreshold) {
    bool dangerPersistent = (now - gasDangerSince >= gasDangerPersistMs);
    bool fumesLongEnough = (now - gasFumesSince >= gasMinFumesBeforeDangerMs);

    if (currentGasStatus == GAS_COOKING_FUMES && dangerPersistent && fumesLongEnough) {
      setGasStatus(GAS_DANGER);
    }
  }
}

// =====================================================
// BUTTON DEBOUNCE HELPER
// =====================================================
bool buttonJustPressed(int pin, bool &lastReading, bool &stableState, unsigned long &lastDebounceTime) {
  bool reading = digitalRead(pin);
  bool pressed = false;

  if (reading != lastReading) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != stableState) {
      stableState = reading;
      if (stableState == LOW) {
        pressed = true;
      }
    }
  }

  lastReading = reading;
  return pressed;
}

// =====================================================
// REQUEST / AUTH SYSTEM
// =====================================================
void requestState(RequestState req) {
  currentRequest = req;

  if (req == REQ_CHILD_EXIT_PIN || req == REQ_AWAY_DISARM_PIN) {
    wrongPinAttempts = 0;
    pinAlert = false;
  }

  if (req == REQ_CHILD_EXIT_PIN) {
    Serial.println("PIN required to deactivate CHILD mode.");
    Serial.println("Type PIN in Serial Monitor or Blynk V26:");
  } else if (req == REQ_AWAY_DISARM_PIN) {
    Serial.println("PIN required to switch AWAY -> HOME.");
    Serial.println("Type PIN in Serial Monitor or Blynk V26:");
  } else if (req == REQ_INTRUDER_CLEAR_WORD) {
    Serial.println("INTRUDER ALERT ACTIVE.");
    Serial.println("System locked.");
    Serial.println("Type the secret word in Serial Monitor or Blynk V26:");
  } else if (req == REQ_AWAY_PET_QUERY) {
    Serial.println("Activating AWAY mode...");
    Serial.println("Pet at home? (y/n)");
  }
}

void processRequestEntry(String text) {
  text.trim();

  if (currentRequest == REQ_NONE) {
    Serial.println("No request active.");
    return;
  }

  if (currentRequest == REQ_AWAY_PET_QUERY) {
    String ans = text;
    ans.toLowerCase();

    if (ans == "y") {
      petAtHome = true;
      currentHouseStatus = HOUSE_AWAY;
      resetAwaySecurity();
      currentRequest = REQ_NONE;
      Serial.println("AWAY mode armed. Pet mode: ON.");
      blynkWriteSafe(V24, 1);
      blynkWriteSafe(V25, 1);
    } else if (ans == "n") {
      petAtHome = false;
      currentHouseStatus = HOUSE_AWAY;
      resetAwaySecurity();
      currentRequest = REQ_NONE;
      Serial.println("AWAY mode armed. Pet mode: OFF.");
      blynkWriteSafe(V24, 1);
      blynkWriteSafe(V25, 0);
    } else {
      Serial.println("Invalid answer. Please type y or n.");
    }
    return;
  }

  if (currentRequest == REQ_INTRUDER_CLEAR_WORD) {
    String word = text;
    word.toUpperCase();

    if (word == SECRET_WORD) {
      resetAwaySecurity();
      petAtHome = false;
      currentHouseStatus = HOUSE_HOME;
      currentRequest = REQ_NONE;
      Serial.println("Correct secret word. INTRUDER ALERT cleared.");
      Serial.println("System returned to HOME mode.");
      blynkWriteSafe(V24, 0);
      blynkWriteSafe(V25, 0);
    } else {
      Serial.println("Wrong secret word. INTRUDER ALERT remains active.");
    }
    return;
  }

  if (text == SYSTEM_PIN) {
    if (currentRequest == REQ_CHILD_EXIT_PIN) {
      childMode = false;
      Serial.println("Correct PIN. CHILD mode deactivated.");
      blynkWriteSafe(V23, 0);
    } else if (currentRequest == REQ_AWAY_DISARM_PIN) {
      currentHouseStatus = HOUSE_HOME;
      petAtHome = false;
      resetAwaySecurity();
      Serial.println("Correct PIN. House disarmed -> HOME.");
      blynkWriteSafe(V24, 0);
      blynkWriteSafe(V25, 0);
    }

    currentRequest = REQ_NONE;
    wrongPinAttempts = 0;
    pinAlert = false;
  } else {
    wrongPinAttempts++;
    Serial.print("Wrong PIN. Attempt ");
    Serial.print(wrongPinAttempts);
    Serial.println(".");

    if (wrongPinAttempts >= 3) {
      pinAlert = true;
      Serial.println("PIN ERROR ALERT");
    }
  }
}

void handleSerialInput() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processRequestEntry(serialBuffer);
        serialBuffer = "";
      }
    } else {
      if (serialBuffer.length() < SERIAL_BUFFER_MAX) {
        serialBuffer += c;
      }
    }
  }
}

// =====================================================
// BLYNK CONTROLS
// =====================================================
bool blynkControlsBlocked() {
  return intruderAlert || currentRequest != REQ_NONE;
}

BLYNK_CONNECTED() {
#if ENABLE_BLYNK
  Blynk.syncVirtual(V3);
#endif
}

BLYNK_WRITE(V3) {
  blynkOutsideScore = constrain(param.asInt(), 0, 1000);

  // First sync from Blynk: cache value, but do not steal control yet
  if (!blynkOutsideInitialized) {
    blynkOutsideInitialized = true;
    Serial.print("Blynk V3 synced (cached only): ");
    Serial.println(blynkOutsideScore);
    return;
  }

  currentOutsideSource = OUTSIDE_SRC_BLYNK;

  Serial.print("Outside brightness set from Blynk V3: ");
  Serial.println(blynkOutsideScore);
}

BLYNK_WRITE(V20) {
  if (blynkControlsBlocked()) return;

  int value = param.asInt();

  if (value == 0) currentMode = NORMAL_MODE;
  else if (value == 1) currentMode = PRIVACY_MODE;
  else if (value == 2) currentMode = ECO_MODE;

  Serial.print("Room mode changed from Blynk to: ");
  Serial.println(modeStr(currentMode));
}

BLYNK_WRITE(V21) {
  if (blynkControlsBlocked()) return;

  if (childMode) {
    Serial.println("Profile control ignored while CHILD mode is active.");
    return;
  }

  int value = param.asInt();
  currentBaseProfile = value == 1 ? PROFILE_ELDERLY : PROFILE_STANDARD;

  Serial.print("Profile changed from Blynk to: ");
  Serial.println(baseProfileStr(currentBaseProfile));
}

BLYNK_WRITE(V22) {
  if (blynkControlsBlocked()) return;

  manualLampOn = param.asInt() == 1;

  Serial.print("Main lamp changed from Blynk to: ");
  Serial.println(manualLampOn ? "ON" : "OFF");
}

BLYNK_WRITE(V23) {
  int value = param.asInt();

  if (intruderAlert) return;

  if (value == 1) {
    if (currentRequest == REQ_NONE) {
      childMode = true;
      Serial.println("CHILD mode activated from Blynk.");
    }
  } else {
    if (childMode && currentRequest == REQ_NONE) {
      requestState(REQ_CHILD_EXIT_PIN);
    }
  }
}

BLYNK_WRITE(V24) {
  int value = param.asInt();

  if (intruderAlert) return;

  if (value == 1) {
    if (currentRequest != REQ_NONE) return;

    if (currentHouseStatus == HOUSE_HOME) {
      if (childMode) {
        Serial.println("AWAY mode cannot be activated while CHILD mode is ON.");
        blynkWriteSafe(V24, 0);
        return;
      }

      // Keep Blynk behaviour consistent with the physical house button.
      // AWAY mode is armed only after confirming whether a pet is at home.
      requestState(REQ_AWAY_PET_QUERY);
    }
  } else {
    if (currentHouseStatus == HOUSE_AWAY && currentRequest == REQ_NONE) {
      requestState(REQ_AWAY_DISARM_PIN);
    }
  }
}

BLYNK_WRITE(V25) {
  if (intruderAlert) return;

  petAtHome = param.asInt() == 1;

  Serial.print("Pet at home changed from Blynk to: ");
  Serial.println(petAtHome ? "YES" : "NO");

  if (currentRequest == REQ_AWAY_PET_QUERY) {
    currentHouseStatus = HOUSE_AWAY;
    resetAwaySecurity();
    currentRequest = REQ_NONE;

    blynkWriteSafe(V24, 1);
    blynkWriteSafe(V25, petAtHome ? 1 : 0);

    Serial.print("AWAY mode armed from Blynk. Pet mode: ");
    Serial.println(petAtHome ? "ON." : "OFF.");
  }
}

BLYNK_WRITE(V26) {
  String text = param.asString();
  text.trim();

  if (text.length() > 0) {
    processRequestEntry(text);
    blynkWriteSafe(V26, "");
  }
}

// =====================================================
// INPUT HANDLING
// =====================================================
void updateManualButton() {
  if (buttonJustPressed(MANUAL_BUTTON_PIN, manualLastReading, manualStableState, manualLastDebounce)) {
    manualLampOn = !manualLampOn;
    Serial.print("Manual main lamp toggled: ");
    Serial.println(manualLampOn ? "ON" : "OFF");
  }
}

void updateRoomModeButton() {
  if (buttonJustPressed(ROOM_MODE_BTN_PIN, roomLastReading, roomStableState, roomLastDebounce)) {
    if (currentMode == NORMAL_MODE) currentMode = PRIVACY_MODE;
    else if (currentMode == PRIVACY_MODE) currentMode = ECO_MODE;
    else currentMode = NORMAL_MODE;

    Serial.print("Room mode changed to: ");
    Serial.println(modeStr(currentMode));
  }
}

void updateProfileButton() {
  if (buttonJustPressed(PROFILE_BTN_PIN, profileLastReading, profileStableState, profileLastDebounce)) {
    if (childMode) {
      Serial.println("Profile button ignored while CHILD mode is active.");
      return;
    }

    currentBaseProfile = (currentBaseProfile == PROFILE_STANDARD) ? PROFILE_ELDERLY : PROFILE_STANDARD;
    Serial.print("Base profile changed to: ");
    Serial.println(baseProfileStr(currentBaseProfile));
  }
}

void updateHouseButton() {
  if (buttonJustPressed(HOUSE_BTN_PIN, houseLastReading, houseStableState, houseLastDebounce)) {
    if (currentHouseStatus == HOUSE_HOME) {
      if (childMode) {
        Serial.println("AWAY mode cannot be activated while CHILD mode is ON.");
        return;
      }
      requestState(REQ_AWAY_PET_QUERY);
    } else {
      requestState(REQ_AWAY_DISARM_PIN);
    }
  }
}

void updateChildButton() {
  if (buttonJustPressed(CHILD_BTN_PIN, childLastReading, childStableState, childLastDebounce)) {
    if (!childMode) {
      childMode = true;
      Serial.println("CHILD mode activated.");
    } else {
      requestState(REQ_CHILD_EXIT_PIN);
    }
  }
}

void applyMainLampState() {
  digitalWrite(MAIN_LAMP_PIN, manualLampOn ? HIGH : LOW);
}

// =====================================================
// DECISION LOGIC
// =====================================================
BlindState decideBlinds(
  OutsideState outsideState,
  InsideState insideState,
  RoomMode mode,
  bool manualLampState
) {
  if (outsideState == OUTSIDE_NIGHT) {
    return BLINDS_CLOSED;
  }

  if (manualLampState) {
    if (mode == PRIVACY_MODE) return BLINDS_CLOSED;
    return BLINDS_HALF;
  }

  if (mode == PRIVACY_MODE) {
    if (insideState == INSIDE_DARK)   return BLINDS_HALF;
    if (insideState == INSIDE_MEDIUM) return BLINDS_HALF;
    return BLINDS_CLOSED;
  }

  if (insideState == INSIDE_DARK)   return BLINDS_OPEN;
  if (insideState == INSIDE_MEDIUM) return BLINDS_HALF;
  return BLINDS_CLOSED;
}

// =====================================================
// APPLY OUTPUTS
// =====================================================
void applyBlinds(BlindState state) {
  if (state == BLINDS_CLOSED) {
    blindsServo.write(blindClosedAngle);
  } else if (state == BLINDS_HALF) {
    blindsServo.write(blindHalfAngle);
  } else {
    blindsServo.write(blindOpenAngle);
  }

  currentBlindState = state;
}

void applyAC(ACState state) {
  bool turnOn = (state == AC_ON);

  if (AC_RELAY_ACTIVE_LOW) {
    digitalWrite(AC_RELAY_PIN, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(AC_RELAY_PIN, turnOn ? HIGH : LOW);
  }

  currentACState = state;
}

void updateBuzzer() {
  bool gasDanger = (currentGasStatus == GAS_DANGER || currentEnvironmentStatus == ENV_GAS_DANGER);
  bool gasHeatEmergency = emergencyCoolingActive();
  bool heatAnomaly = (currentEnvironmentStatus == ENV_HEAT_ANOMALY);

  bool active = gasDanger || gasHeatEmergency || heatAnomaly || intruderAlert || pinAlert;

  if (!active) {
    digitalWrite(BUZZER_PIN, LOW);
    return;
  }

  unsigned long period = 450;

  if (gasHeatEmergency) period = 80;
  else if (gasDanger) period = 120;
  else if (intruderAlert) period = 180;
  else if (heatAnomaly) period = 300;
  else period = 450;

  bool on = ((millis() / period) % 2 == 0);
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

void updateSprinklerLed() {
  if (!emergencyCoolingActive()) {
    digitalWrite(SPRINKLER_LED_PIN, LOW);
    return;
  }

  bool on = ((millis() / sprinklerBlinkPeriodMs) % 2 == 0);
  digitalWrite(SPRINKLER_LED_PIN, on ? HIGH : LOW);
}

// =====================================================
// LCD
// =====================================================
void updateLCD(
  InsideState insideState,
  OutsideState outsideState,
  bool presence,
  ThermalState thermalState,
  int gasScore
) {
  if (millis() - lastLcdTime < lcdEvery) return;
  lastLcdTime = millis();

  if (isMq2WarmingUp()) {
    unsigned long remaining = (mq2WarmupMs - (millis() - systemStartTime)) / 1000;
    lcdPrint2("MQ2 WARMING...", "Wait " + String(remaining) + "s");
    return;
  }

  if (emergencyCoolingActive()) {
    lcdPrint2("GAS+HEAT ALERT", "SPRINKLER ON");
    return;
  }

  if (currentEnvironmentStatus == ENV_HEAT_ANOMALY) {
    lcdPrint2("HEAT ANOMALY", "T:" + String(currentTempC, 1) + "C");
    return;
  }

  if (currentGasStatus == GAS_DANGER || currentEnvironmentStatus == ENV_GAS_DANGER) {
    lcdPrint2("GAS DANGER!", "CHECK KITCHEN");
    return;
  }

  if (intruderAlert) {
    lcdPrint2("INTRUDER ALERT", "TYPE OKAY");
    return;
  }

  if (currentGasStatus == GAS_COOKING_FUMES || currentEnvironmentStatus == ENV_COOKING_FUMES) {
    lcdPrint2("COOKING FUMES", "G:" + String(gasScore) + " MONITOR");
    return;
  }

  if (suspiciousMotion) {
    lcdPrint2("SUSPICIOUS MOTN", "AWAY MONITORING");
    return;
  }

  if (pinAlert) {
    lcdPrint2("PIN ERROR ALERT", "3 WRONG TRIES");
    return;
  }

  if (currentRequest == REQ_CHILD_EXIT_PIN) {
    lcdPrint2("PIN TO EXIT", "CHILD MODE");
    return;
  }

  if (currentRequest == REQ_AWAY_DISARM_PIN) {
    lcdPrint2("PIN TO DISARM", "AWAY -> HOME");
    return;
  }

  if (currentRequest == REQ_AWAY_PET_QUERY) {
    lcdPrint2("PET AT HOME?", "V25 OR y/n");
    return;
  }

  if (!dhtValid && currentGasStatus == GAS_NORMAL) {
    lcdPrint2("DHT SENSOR ERROR", "AC FAIL-SAFE OFF");
    return;
  }

  int page = (millis() / 2200) % 4;

  if (page == 0) {
    String line1 = "M:" + String(modeShort(currentMode)) + " P:" + String(effectiveProfileShort());
    String line2 = "H:" + String(houseShort(currentHouseStatus)) + " Pt:" + String(petAtHome ? "Y" : "N");
    lcdPrint2(line1, line2);
  } else if (page == 1) {
    String line1 = "In:" + String(insideStateStr(insideState)) + " Out:" + String(outsideStateStr(outsideState));
    String line2 = "B:" + String(blindStateStr(currentBlindState)) + " L:" + String(manualLampOn ? "ON" : "OFF");
    lcdPrint2(line1, line2);
  } else if (page == 2) {
    String line1 = "T:" + String(currentTempC, 1) + " H:" + String((int)currentHumidity) + "%";
    String line2 = "AC:" + String(acStateStr(currentACState)) + " " + String(thermalStateStr(thermalState));
    lcdPrint2(line1, line2);
  } else {
    String p = presence ? "Y" : "N";
    String line1 = "Env:" + String(environmentStatusShort(currentEnvironmentStatus));
    String line2 = "G:" + String(gasScore) + " P:" + p;
    lcdPrint2(line1, line2);
  }
}

// =====================================================
// SERIAL DEBUG OUTPUT
// =====================================================
void printStatus(
  int rawInside,
  int rawOutside,
  int gasRaw,
  int insideScore,
  int outsideScore,
  int gasScore,
  int pirRaw,
  InsideState insideState,
  OutsideState outsideState,
  bool presence,
  ThermalState thermalState
) {
  int warningThreshold, dangerThreshold, severeThreshold, clearThreshold;
  getGasThresholds(warningThreshold, dangerThreshold, severeThreshold, clearThreshold);

  Serial.println("\n======== KITCHEN/LIVING STATUS (refresh every 5 seconds) =========");

  Serial.print("Room mode: ");
  Serial.println(modeStr(currentMode));

  Serial.print("Profile: ");
  Serial.println(effectiveProfileStr());

  Serial.print("House status: ");
  Serial.println(houseStr(currentHouseStatus));

  Serial.print("Pet at home: ");
  Serial.println(petAtHome ? "YES" : "NO");

  Serial.print("Alert: ");
  Serial.println(activeAlertText());

  Serial.print("AWAY motion count: ");
  Serial.println(awayMotionCount);

  Serial.print("LDR inside raw: ");
  Serial.print(rawInside);
  Serial.print(" | inside effective brightness score: ");
  Serial.println(insideScore);

  Serial.print("LDR outside raw: ");
  Serial.print(rawOutside);
  Serial.print(" | active outside score: ");
  Serial.print(outsideScore);
  Serial.print(" | source: ");
  Serial.println(currentOutsideSource == OUTSIDE_SRC_BLYNK ? "BLYNK_V3" : "WOKWI_LDR");

  Serial.print("Inside state: ");
  Serial.println(insideStateStr(insideState));

  Serial.print("Outside state: ");
  Serial.println(outsideStateStr(outsideState));

  Serial.print("PIR raw: ");
  Serial.println(pirRaw);

  Serial.print("Presence active: ");
  Serial.println(presenceLabel(presence, insideState));

  Serial.print("Manual main lamp: ");
  Serial.println(manualLampOn ? "ON" : "OFF");

  Serial.print("Blinds: ");
  Serial.println(blindStateStr(currentBlindState));

  Serial.print("MQ2 raw: ");
  Serial.print(gasRaw);
  Serial.print(" | gas score: ");
  Serial.println(gasScore);

  Serial.print("MQ2 warming up: ");
  Serial.println(isMq2WarmingUp() ? "YES" : "NO");

  Serial.print("Gas thresholds - clear/warn/danger/severe: ");
  Serial.print(clearThreshold);
  Serial.print(" / ");
  Serial.print(warningThreshold);
  Serial.print(" / ");
  Serial.print(dangerThreshold);
  Serial.print(" / ");
  Serial.println(severeThreshold);

  Serial.print("Gas status: ");
  Serial.println(gasStatusStr(currentGasStatus));

  Serial.print("Environmental status: ");
  Serial.println(environmentStatusStr(currentEnvironmentStatus));

#if USE_EDGE_IMPULSE_RUNTIME
  Serial.print("Last ML prediction: ");
  Serial.println(mlValid ? environmentStatusStr(lastMlEnvironmentStatus) : "INVALID");
  Serial.print("ML valid: ");
  Serial.println(mlValid ? "YES" : "NO");
  Serial.print("ML confidence: ");
  if (mlValid) Serial.println(mlConfidence, 3);
  else Serial.println("INVALID");
#else
  Serial.println("Last ML prediction: DISABLED");
  Serial.println("ML valid: NO (runtime disabled)");
  Serial.println("ML confidence: N/A");
#endif

  Serial.print("Emergency cooling threshold: ");
  Serial.print(emergencyCoolingTempC, 1);
  Serial.println(" C");

  Serial.print("Emergency cooling active: ");
  Serial.println(emergencyCoolingActive() ? "YES" : "NO");

  if (dhtValid) {
    Serial.print("Temperature: ");
    Serial.print(currentTempC, 1);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(currentHumidity, 1);
    Serial.println(" %");
  } else {
    Serial.println("Temperature: INVALID");
    Serial.println("Humidity: INVALID");
  }

  Serial.print("Thermal state: ");
  Serial.println(thermalStateStr(thermalState));

  Serial.print("AC: ");
  Serial.println(acStateStr(currentACState));

  if (currentRequest == REQ_CHILD_EXIT_PIN) {
    Serial.println("Request active: CHILD EXIT PIN");
  } else if (currentRequest == REQ_AWAY_DISARM_PIN) {
    Serial.println("Request active: AWAY DISARM PIN");
  } else if (currentRequest == REQ_INTRUDER_CLEAR_WORD) {
    Serial.println("Request active: INTRUDER CLEAR WORD");
  } else if (currentRequest == REQ_AWAY_PET_QUERY) {
    Serial.println("Request active: AWAY PET QUERY");
  } else {
    Serial.println("Request active: NONE");
  }
}

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);

#if ENABLE_BLYNK
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  timer.setInterval(3000L, sendToBlynk);
#else
  Serial.println("Blynk disabled (public default); local Wokwi logic remains active.");
#endif

  systemStartTime = millis();

  pinMode(PIR_PIN, INPUT);

  pinMode(LDR_INSIDE_PIN, INPUT);
  pinMode(LDR_OUTSIDE_PIN, INPUT);
  pinMode(MQ2_PIN, INPUT);

  pinMode(MANUAL_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ROOM_MODE_BTN_PIN, INPUT_PULLUP);
  pinMode(PROFILE_BTN_PIN, INPUT_PULLUP);
  pinMode(HOUSE_BTN_PIN, INPUT_PULLUP);
  pinMode(CHILD_BTN_PIN, INPUT_PULLUP);

  pinMode(MAIN_LAMP_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(AC_RELAY_PIN, OUTPUT);
  pinMode(SPRINKLER_LED_PIN, OUTPUT);

  analogReadResolution(12);
  analogSetPinAttenuation(LDR_INSIDE_PIN, ADC_11db);
  analogSetPinAttenuation(LDR_OUTSIDE_PIN, ADC_11db);
  analogSetPinAttenuation(MQ2_PIN, ADC_11db);

  Wire.begin(LCD_SDA_PIN, LCD_SCL_PIN);
  lcd.begin(16, 2, Wire);
  lcd.setBacklight(255);
  lcd.clear();

  dht.begin();

  blindsServo.attach(SERVO_PIN, 500, 2400);

  applyBlinds(BLINDS_CLOSED);
  applyMainLampState();
  applyAC(AC_OFF);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(SPRINKLER_LED_PIN, LOW);

  lcdPrint2("Kitchen/Living", "Starting...");

  Serial.println("Kitchen / Living Room Module Started");
  Serial.println(ENABLE_BLYNK ? "Blynk enabled." : "Blynk disabled (public default).");
  Serial.println(USE_EDGE_IMPULSE_RUNTIME ? "Edge Impulse runtime enabled." : "Edge Impulse runtime disabled; rules are authoritative.");
  Serial.println("Outside brightness can be controlled by:");
  Serial.println("- Wokwi outside LDR");
  Serial.println("- Blynk V3 slider");
  Serial.println("The last source moved takes control.");
  Serial.println("0-119 NIGHT | 120-499 TRANSITION | 500-1000 DAY");
  Serial.println("V2 is inside brightness read-only.");
  Serial.println("V4 is MQ2 gas score read-only.");
  Serial.println("V29 environmental status | V30 ML confidence | V31 raw ML prediction");
  Serial.println("PIN required to exit CHILD and to disarm AWAY->HOME");
  Serial.println("Secret word required to clear INTRUDER ALERT");
}

// =====================================================
// LOOP
// =====================================================
void loop() {
#if ENABLE_BLYNK
  Blynk.run();
  timer.run();
#endif

  handleSerialInput();
  updateDHT();

  // -------------------- PIR / PRESENCE --------------------
  int pirRaw = digitalRead(PIR_PIN);
  bool risingMotion = (pirRaw == HIGH && lastPirState == LOW);
  lastPirState = (pirRaw == HIGH);

  if (pirRaw == HIGH) {
    lastMotionTime = millis();
    motionSeenOnce = true;
  }

  if (currentHouseStatus == HOUSE_AWAY && !intruderAlert) {
    if (awayWindowStart != 0 && (millis() - awayWindowStart > awayMotionWindowMs)) {
      awayMotionCount = 0;
      awayWindowStart = 0;
      suspiciousMotion = false;
    }
  }

  if (currentHouseStatus == HOUSE_AWAY && risingMotion && !intruderAlert) {
    if (awayWindowStart == 0 || (millis() - awayWindowStart > awayMotionWindowMs)) {
      awayWindowStart = millis();
      awayMotionCount = 1;
    } else {
      awayMotionCount++;
    }

    if (awayMotionCount >= getSuspiciousThreshold()) {
      suspiciousMotion = true;
    }

    if (awayMotionCount >= getIntruderThreshold()) {
      intruderAlert = true;
      suspiciousMotion = false;
      requestState(REQ_INTRUDER_CLEAR_WORD);
      Serial.println("INTRUDER ALERT triggered by repeated motion in AWAY mode.");
    } else {
      Serial.print("AWAY motion detected. Count = ");
      Serial.println(awayMotionCount);
    }
  }

  if (!intruderAlert && currentRequest == REQ_NONE) {
    updateRoomModeButton();
    updateProfileButton();
    updateHouseButton();
    updateChildButton();
    updateManualButton();
  }

  applyMainLampState();

  // -------------------- SENSOR READINGS --------------------
  int rawInside  = analogRead(LDR_INSIDE_PIN);
  int rawOutside = analogRead(LDR_OUTSIDE_PIN);
  int gasRaw     = analogRead(MQ2_PIN);

  int insideScoreBase = rawToBrightnessScore(rawInside);

  // Unified outside brightness:
  // - Wokwi outside LDR controls it by default
  // - Blynk V3 can take control
  // - moving the physical outside LDR again gives control back to Wokwi
  int outsideScore = getUnifiedOutsideScore(rawOutside);

  int gasScore = rawToGasScore(gasRaw);

  if (manualLampOn) {
    insideScoreBase += manualLampBoost;
    if (insideScoreBase > 1000) insideScoreBase = 1000;
  }

  // Persistence-gated deterministic gas state machine.
  updateGasStatus(gasScore);

  // Actionable status remains deterministic. Optional ML is advisory telemetry only.
  updateEnvironmentAI(gasScore);

  OutsideState outsideState = classifyOutside(outsideScore);
  bool presence = presenceActive();

  InsideState insideStatePre = classifyInside(insideScoreBase);

  // -------------------- BLINDS --------------------
  BlindState blindTarget;

  if (currentGasStatus != GAS_NORMAL || environmentHasGasIssue(currentEnvironmentStatus)) {
    blindTarget = BLINDS_OPEN;
  } else if (currentHouseStatus == HOUSE_AWAY || intruderAlert || suspiciousMotion) {
    blindTarget = BLINDS_CLOSED;
  } else {
    blindTarget = decideBlinds(
      outsideState,
      insideStatePre,
      currentMode,
      manualLampOn
    );
  }

  int daylightBoost = getBlindDaylightBoost(blindTarget, outsideState, outsideScore);

  int insideScore = insideScoreBase + daylightBoost;
  if (insideScore > 1000) insideScore = 1000;

  InsideState insideState = classifyInside(insideScore);

  if (outsideState == OUTSIDE_NIGHT &&
      blindTarget == BLINDS_CLOSED &&
      !manualLampOn) {
    if (insideScore >= insideDarkMax) {
      insideScore = insideDarkMax - 1;
    }
    insideState = classifyInside(insideScore);
  }

  // -------------------- AC --------------------
  float acOnThreshold  = getACOnTempThreshold(currentMode, childMode, currentBaseProfile);
  float acOffThreshold = getACOffTempThreshold(acOnThreshold);
  ThermalState thermalState = dhtValid ? classifyThermal(currentTempC, acOnThreshold, acOffThreshold) : THERMAL_COMFORT;

  ACState acTarget = decideAC(
    currentTempC,
    currentHumidity,
    currentMode,
    currentHouseStatus,
    childMode,
    currentBaseProfile,
    currentACState
  );

  // -------------------- APPLY OUTPUTS --------------------
  applyBlinds(blindTarget);
  applyAC(acTarget);
  updateBuzzer();
  updateSprinklerLed();
  updateLCD(insideState, outsideState, presence, thermalState, gasScore);

  // -------------------- SAVE VALUES FOR BLYNK --------------------
  blynkInsideScore = insideScore;
  blynkGasScore = gasScore;
  blynkPirRaw = pirRaw;
  blynkPresence = presence;

  blynkInsideState = insideState;
  blynkOutsideState = outsideState;
  blynkThermalState = thermalState;

  if (millis() - lastSerialTime >= serialEvery) {
    lastSerialTime = millis();
    printStatus(
      rawInside,
      rawOutside,
      gasRaw,
      insideScore,
      outsideScore,
      gasScore,
      pirRaw,
      insideState,
      outsideState,
      presence,
      thermalState
    );
  }

  delay(50);
}
