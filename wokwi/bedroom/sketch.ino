#define BLYNK_TEMPLATE_ID "YOUR_TEMPLATE_ID"
#define BLYNK_TEMPLATE_NAME "Bedroom"
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
// BEDROOM - FIRST MODULE
// AI-Enhanced Smart Home for Adaptive Lighting,
// Privacy and Energy Management
// =====================================================

// -------------------- PINS --------------------
#define PIR_PIN               5
#define LDR_INSIDE_PIN        4
#define LDR_OUTSIDE_PIN       6
#define SMART_LIGHT_PIN       2
#define SERVO_PIN             18
#define MANUAL_BUTTON_PIN     7
#define MANUAL_LAMP_LED_PIN   8

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

// -------------------- PWM --------------------
#define PWM_FREQ              5000
#define PWM_RES_BITS          8

// -------------------- LIGHT THRESHOLDS --------------------
int insideDarkMax   = 60;
int insideMediumMax = 180;

int outsideNightMax = 120;
int outsideDayMin   = 500;

// Simulated contribution of manual lamp
int manualLampBoost = 250;

// -------------------- TIMING --------------------
unsigned long motionHoldMsStandard = 20000;
unsigned long serialEvery          = 5000;
unsigned long lcdEvery             = 600;
unsigned long dhtEvery             = 2000;

// AWAY security window
unsigned long awayMotionWindowMs   = 50000;

// -------------------- SERVO ANGLES --------------------
int blindClosedAngle = 0;
int blindHalfAngle   = 90;
int blindOpenAngle   = 180;

// -------------------- LCD --------------------
LiquidCrystal_PCF8574 lcd(0x27);

// -------------------- DHT --------------------
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

enum LightState {
  LIGHT_OFF,
  LIGHT_DIM,
  LIGHT_ON
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

enum RoomMode {
  NORMAL_MODE,
  SLEEP_MODE,
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

enum OutsideSource {
  OUTSIDE_SRC_WOKWI,
  OUTSIDE_SRC_BLYNK
};

enum RequestState {
  REQ_NONE,
  REQ_CHILD_EXIT_PIN,
  REQ_AWAY_DISARM_PIN,
  REQ_INTRUDER_CLEAR_WORD,
  REQ_AWAY_PET_QUERY
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

unsigned long lastMotionTime = 0;
bool motionSeenOnce = false;
unsigned long lastSerialTime = 0;
unsigned long lastLcdTime = 0;
unsigned long lastDhtTime = 0;

// AWAY monitoring
int awayMotionCount = 0;
unsigned long awayWindowStart = 0;
bool lastPirState = false;

// Manual lamp state
bool manualLampOn = false;

// DHT cached values
float currentTempC = 24.0;
float currentHumidity = 50.0;
bool dhtValid = false;

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

// Current output states
BlindState currentBlindState = BLINDS_CLOSED;
LightState currentSmartLightState = LIGHT_OFF;
ACState currentACState = AC_OFF;

// Auth system
String serialBuffer = "";
const unsigned int SERIAL_BUFFER_MAX = 24;
const String SYSTEM_PIN  = "1234";        // Demo PIN for simulation
const String SECRET_WORD = "OKAY";        // Demo secret word for simulation
int wrongPinAttempts = 0;

// -------------------- BLYNK CACHED VALUES --------------------
int blynkInsideScore = 0;
int blynkOutsideScore = 0;   // V3 slider: outside brightness simulation
int blynkPirRaw = 0;
bool blynkPresence = false;

InsideState blynkInsideState = INSIDE_DARK;
OutsideState blynkOutsideState = OUTSIDE_NIGHT;
ThermalState blynkThermalState = THERMAL_COMFORT;

OutsideSource currentOutsideSource = OUTSIDE_SRC_WOKWI;
int lastPhysicalOutsideScore = -1;
const int outsideChangeThreshold = 20;
bool blynkOutsideInitialized = false;

// =====================================================
// HELPERS
// =====================================================
int rawToBrightnessScore(int raw) {
  raw = constrain(raw, 0, 4095);
  int inverted = 4095 - raw;
  return map(inverted, 0, 4095, 0, 1000);
}

int getUnifiedOutsideScore(int rawOutside) {
  int physicalOutsideScore = rawToBrightnessScore(rawOutside);
  if (lastPhysicalOutsideScore < 0) lastPhysicalOutsideScore = physicalOutsideScore;
  if (abs(physicalOutsideScore - lastPhysicalOutsideScore) > outsideChangeThreshold) currentOutsideSource = OUTSIDE_SRC_WOKWI;
  lastPhysicalOutsideScore = physicalOutsideScore;
  if (currentOutsideSource == OUTSIDE_SRC_BLYNK) return constrain(blynkOutsideScore, 0, 1000);
  return physicalOutsideScore;
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

BlindState maxOpenBlindState(BlindState a, BlindState b) {
  return (a > b) ? a : b;
}

String pad16(String s) {
  if (s.length() > 16) return s.substring(0, 16);
  while (s.length() < 16) s += " ";
  return s;
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

const char* lightStateStr(LightState s) {
  if (s == LIGHT_OFF) return "OFF";
  if (s == LIGHT_DIM) return "DIM";
  return "ON";
}

const char* acStateStr(ACState s) {
  return (s == AC_ON) ? "ON" : "OFF";
}

const char* thermalStateStr(ThermalState s) {
  if (s == THERMAL_COOL) return "COOL";
  if (s == THERMAL_WARM) return "WARM";
  return "COMFORT";
}

const char* modeStr(RoomMode m) {
  if (m == NORMAL_MODE) return "NORMAL";
  if (m == SLEEP_MODE) return "SLEEP";
  if (m == PRIVACY_MODE) return "PRIVACY";
  return "ECO";
}

const char* modeShort(RoomMode m) {
  if (m == NORMAL_MODE) return "NORM";
  if (m == SLEEP_MODE) return "SLP";
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
  if (intruderAlert) return "INTRUDER ALERT";
  if (suspiciousMotion) return "SUSPICIOUS MOTION";
  if (pinAlert) return "PIN ERROR ALERT";
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

// =====================================================
// BLYNK SEND DATA
// =====================================================
void sendToBlynk() {
  blynkWriteSafe(V0, currentTempC);
  blynkWriteSafe(V1, currentHumidity);

  blynkWriteSafe(V2, blynkInsideScore);

  // V3 is NOT written here.
  // V3 is the outside brightness slider from Blynk to ESP32.

  blynkWriteSafe(V4, blynkPirRaw);
  blynkWriteSafe(V5, blynkPresence ? 1 : 0);

  blynkWriteSafe(V6, blindStateStr(currentBlindState));
  blynkWriteSafe(V7, lightStateStr(currentSmartLightState));
  blynkWriteSafe(V8, acStateStr(currentACState));
  blynkWriteSafe(V9, modeStr(currentMode));
  blynkWriteSafe(V10, effectiveProfileStr());
  blynkWriteSafe(V11, houseStr(currentHouseStatus));
  blynkWriteSafe(V12, activeAlertText());
  blynkWriteSafe(V13, petAtHome ? "YES" : "NO");
  blynkWriteSafe(V14, awayMotionCount);
  blynkWriteSafe(V15, manualLampOn ? "ON" : "OFF");
  blynkWriteSafe(V16, thermalStateStr(blynkThermalState));
  blynkWriteSafe(V17, insideStateStr(blynkInsideState));
  blynkWriteSafe(V18, outsideStateStr(blynkOutsideState));
  blynkWriteSafe(V19, presenceLabel(blynkPresence, blynkInsideState));
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
  else if (mode == SLEEP_MODE) t = 27.5;
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
  if (houseStatus == HOUSE_AWAY) {
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
    } else if (ans == "n") {
      petAtHome = false;
      currentHouseStatus = HOUSE_AWAY;
      resetAwaySecurity();
      currentRequest = REQ_NONE;
      Serial.println("AWAY mode armed. Pet mode: OFF.");
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
    } else {
      Serial.println("Wrong secret word. INTRUDER ALERT remains active.");
    }
    return;
  }

  if (text == SYSTEM_PIN) {
    if (currentRequest == REQ_CHILD_EXIT_PIN) {
      childMode = false;
      Serial.println("Correct PIN. CHILD mode deactivated.");
    } else if (currentRequest == REQ_AWAY_DISARM_PIN) {
      currentHouseStatus = HOUSE_HOME;
      petAtHome = false;
      resetAwaySecurity();
      Serial.println("Correct PIN. House disarmed -> HOME.");
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
  else if (value == 1) currentMode = SLEEP_MODE;
  else if (value == 2) currentMode = PRIVACY_MODE;
  else if (value == 3) currentMode = ECO_MODE;

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

  Serial.print("Manual lamp changed from Blynk to: ");
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
    Serial.print("Manual lamp toggled: ");
    Serial.println(manualLampOn ? "ON" : "OFF");
  }
}

void updateRoomModeButton() {
  if (buttonJustPressed(ROOM_MODE_BTN_PIN, roomLastReading, roomStableState, roomLastDebounce)) {
    if (currentMode == NORMAL_MODE) currentMode = SLEEP_MODE;
    else if (currentMode == SLEEP_MODE) currentMode = PRIVACY_MODE;
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

void applyManualLampState() {
  ledcWrite(MANUAL_LAMP_LED_PIN, manualLampOn ? 255 : 0);
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
  if (mode == SLEEP_MODE) {
    return BLINDS_CLOSED;
  }

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

LightState decideSmartLight(
  OutsideState outsideState,
  InsideState insideState,
  bool presence,
  bool manualLampState,
  RoomMode mode,
  HouseStatus houseStatus,
  bool childModeActive,
  BaseProfile baseProfile
) {
  if (houseStatus == HOUSE_AWAY) {
    return LIGHT_OFF;
  }

  if (manualLampState) {
    return LIGHT_OFF;
  }

  if (!presence) {
    return LIGHT_OFF;
  }

  bool gentleProfile = childModeActive || (baseProfile == PROFILE_ELDERLY);

  if (mode == SLEEP_MODE) {
    if (gentleProfile && outsideState == OUTSIDE_NIGHT) return LIGHT_DIM;
    return LIGHT_OFF;
  }

  if (outsideState == OUTSIDE_NIGHT) {
    if (insideState == INSIDE_DARK) {
      if (gentleProfile) return LIGHT_DIM;
      return (mode == ECO_MODE) ? LIGHT_DIM : LIGHT_ON;
    }
    if (insideState == INSIDE_MEDIUM) return LIGHT_DIM;
    return LIGHT_OFF;
  }

  if (insideState == INSIDE_DARK) return LIGHT_DIM;

  return LIGHT_OFF;
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

void applySmartLight(LightState state) {
  int pwm = 0;

  if (state == LIGHT_OFF) pwm = 0;
  else if (state == LIGHT_DIM) pwm = 90;
  else pwm = 255;

  ledcWrite(SMART_LIGHT_PIN, pwm);
  currentSmartLightState = state;
}

void applyAC(ACState state) {
  digitalWrite(AC_RELAY_PIN, state == AC_ON ? HIGH : LOW);
  currentACState = state;
}

void updateBuzzer() {
  bool active = intruderAlert || pinAlert;

  if (!active) {
    digitalWrite(BUZZER_PIN, LOW);
    return;
  }

  unsigned long period = intruderAlert ? 180 : 450;
  bool on = ((millis() / period) % 2 == 0);
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

// =====================================================
// LCD
// =====================================================
void updateLCD(
  InsideState insideState,
  OutsideState outsideState,
  bool presence,
  ThermalState thermalState
) {
  if (millis() - lastLcdTime < lcdEvery) return;
  lastLcdTime = millis();

  if (intruderAlert) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("INTRUDER ALERT"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("TYPE OKAY SERIAL"));
    return;
  }

  if (suspiciousMotion) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("SUSPICIOUS MOTN"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("AWAY MONITORING"));
    return;
  }

  if (pinAlert) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("PIN ERROR ALERT"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("3 WRONG TRIES"));
    return;
  }

  if (currentRequest == REQ_CHILD_EXIT_PIN) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("PIN TO EXIT"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("CHILD MODE"));
    return;
  }

  if (currentRequest == REQ_AWAY_DISARM_PIN) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("PIN TO DISARM"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("AWAY -> HOME"));
    return;
  }

  if (currentRequest == REQ_AWAY_PET_QUERY) {
    lcd.setCursor(0, 0);
    lcd.print(pad16("PET AT HOME?"));
    lcd.setCursor(0, 1);
    lcd.print(pad16("TYPE y/n SERIAL"));
    return;
  }

  int page = (millis() / 2000) % 4;

  if (page == 0) {
    String line1 = "M:" + String(modeShort(currentMode)) + " P:" + String(effectiveProfileShort());
    String line2 = "H:" + String(houseShort(currentHouseStatus)) + " Pt:" + String(petAtHome ? "Y" : "N");
    lcd.setCursor(0, 0);
    lcd.print(pad16(line1));
    lcd.setCursor(0, 1);
    lcd.print(pad16(line2));
  } else if (page == 1) {
    String line1 = "In:" + String(insideStateStr(insideState)) + " Out:" + String(outsideStateStr(outsideState));
    String line2 = "B:" + String(blindStateStr(currentBlindState)) + " L:" + String(lightStateStr(currentSmartLightState));
    lcd.setCursor(0, 0);
    lcd.print(pad16(line1));
    lcd.setCursor(0, 1);
    lcd.print(pad16(line2));
  } else if (page == 2) {
    String p = presence ? (insideState == INSIDE_DARK ? "YES dark" : "YES") : "NO";
    String line1 = "Pres:" + p;
    String line2 = "Ct:" + String(awayMotionCount);
    lcd.setCursor(0, 0);
    lcd.print(pad16(line1));
    lcd.setCursor(0, 1);
    lcd.print(pad16(line2));
  } else {
    String line1 = "T:" + String(currentTempC, 1) + "C H:" + String((int)currentHumidity) + "%";
    String line2 = "AC:" + String(acStateStr(currentACState)) + " " + String(thermalStateStr(thermalState));
    lcd.setCursor(0, 0);
    lcd.print(pad16(line1));
    lcd.setCursor(0, 1);
    lcd.print(pad16(line2));
  }
}

// =====================================================
// SERIAL DEBUG OUTPUT
// =====================================================
void printStatus(
  int rawInside,
  int rawOutside,
  int insideScore,
  int outsideScore,
  int pirRaw,
  InsideState insideState,
  OutsideState outsideState,
  bool presence,
  ThermalState thermalState
) {
  Serial.println("\n======== SYSTEM STATUS (refresh every 5 seconds) =========");

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

  Serial.print("LDR2 inside raw: ");
  Serial.print(rawInside);
  Serial.print(" | inside effective brightness score: ");
  Serial.println(insideScore);

  Serial.print("LDR1 outside raw: ");
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

  Serial.print("Manual lamp: ");
  Serial.println(manualLampOn ? "ON" : "OFF");

  Serial.print("Blinds: ");
  Serial.println(blindStateStr(currentBlindState));

  Serial.print("Smart ambient light: ");
  Serial.println(lightStateStr(currentSmartLightState));

  Serial.print("Temperature: ");
  Serial.print(currentTempC, 1);
  Serial.println(" C");

  Serial.print("Humidity: ");
  Serial.print(currentHumidity, 1);
  Serial.println(" %");

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

  pinMode(PIR_PIN, INPUT);
  pinMode(MANUAL_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ROOM_MODE_BTN_PIN, INPUT_PULLUP);
  pinMode(PROFILE_BTN_PIN, INPUT_PULLUP);
  pinMode(HOUSE_BTN_PIN, INPUT_PULLUP);
  pinMode(CHILD_BTN_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(AC_RELAY_PIN, OUTPUT);

  analogReadResolution(12);

  if (!ledcAttach(SMART_LIGHT_PIN, PWM_FREQ, PWM_RES_BITS)) {
    Serial.println("Error attaching SMART_LIGHT_PIN to LEDC");
  }

  if (!ledcAttach(MANUAL_LAMP_LED_PIN, PWM_FREQ, PWM_RES_BITS)) {
    Serial.println("Error attaching MANUAL_LAMP_LED_PIN to LEDC");
  }

  Wire.begin(LCD_SDA_PIN, LCD_SCL_PIN);
  lcd.begin(16, 2, Wire);
  lcd.setBacklight(255);

  dht.begin();

  blindsServo.attach(SERVO_PIN, 500, 2400);

  applyBlinds(BLINDS_CLOSED);
  applySmartLight(LIGHT_OFF);
  applyAC(AC_OFF);
  applyManualLampState();
  digitalWrite(BUZZER_PIN, LOW);

  lcd.setCursor(0, 0);
  lcd.print("Bedroom Module");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");

  Serial.println("Bedroom First Module Started");
  Serial.println(ENABLE_BLYNK ? "Blynk enabled." : "Blynk disabled (public default).");
  Serial.println("V3 controls outside brightness simulation.");
  Serial.println("0-119 NIGHT | 120-499 TRANSITION | 500-1000 DAY");
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

  applyManualLampState();

  int rawInside  = analogRead(LDR_INSIDE_PIN);
  int rawOutside = analogRead(LDR_OUTSIDE_PIN);

  int insideScoreBase = rawToBrightnessScore(rawInside);

  // Outside brightness is physical-Wokwi first. If Blynk is enabled,
  // V3 may take control until the physical outside LDR moves again.
  int outsideScore = getUnifiedOutsideScore(rawOutside);

  if (manualLampOn) {
    insideScoreBase += manualLampBoost;
    if (insideScoreBase > 1000) insideScoreBase = 1000;
  }

  OutsideState outsideState = classifyOutside(outsideScore);
  bool presence = presenceActive();

  InsideState insideStatePre = classifyInside(insideScoreBase);

  BlindState blindTarget;
  if (currentHouseStatus == HOUSE_AWAY || intruderAlert || suspiciousMotion) {
    blindTarget = BLINDS_CLOSED;
  } else {
    blindTarget = decideBlinds(
      outsideState,
      insideStatePre,
      currentMode,
      manualLampOn
    );
  }

  BlindState effectiveBlindState = maxOpenBlindState(currentBlindState, blindTarget);
  int daylightBoost = getBlindDaylightBoost(effectiveBlindState, outsideState, outsideScore);

  int insideScore = insideScoreBase + daylightBoost;
  if (insideScore > 1000) insideScore = 1000;

  InsideState insideState = classifyInside(insideScore);

  if (outsideState == OUTSIDE_NIGHT &&
      effectiveBlindState == BLINDS_CLOSED &&
      !manualLampOn) {
    if (insideScore >= insideDarkMax) {
      insideScore = insideDarkMax - 1;
    }
    insideState = classifyInside(insideScore);
  }

  LightState lightTarget;
  if (currentHouseStatus == HOUSE_AWAY || intruderAlert || suspiciousMotion) {
    lightTarget = LIGHT_OFF;
  } else {
    lightTarget = decideSmartLight(
      outsideState,
      insideState,
      presence,
      manualLampOn,
      currentMode,
      currentHouseStatus,
      childMode,
      currentBaseProfile
    );
  }

  float acOnThreshold  = getACOnTempThreshold(currentMode, childMode, currentBaseProfile);
  float acOffThreshold = getACOffTempThreshold(acOnThreshold);
  ThermalState thermalState = classifyThermal(currentTempC, acOnThreshold, acOffThreshold);

  ACState acTarget = decideAC(
    currentTempC,
    currentHumidity,
    currentMode,
    currentHouseStatus,
    childMode,
    currentBaseProfile,
    currentACState
  );

  applyBlinds(blindTarget);
  applySmartLight(lightTarget);
  applyAC(acTarget);
  updateBuzzer();
  updateLCD(insideState, outsideState, presence, thermalState);

  blynkInsideScore = insideScore;
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
      insideScore,
      outsideScore,
      pirRaw,
      insideState,
      outsideState,
      presence,
      thermalState
    );
  }

  delay(50);
}
