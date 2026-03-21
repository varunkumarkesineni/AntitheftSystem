#include <HX711.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ── Pin Definitions ────────────────────────────────────────
#define HX711_DT     3
#define HX711_SCK    2
#define LED_GREEN    8
#define LED_RED      9
#define BUZZER_PIN  10

// ── Constants ──────────────────────────────────────────────
#define TOLERANCE_G       10.00    // ±10g tolerance
#define CALIBRATION_FACTOR 420.0   // increase or decrease this number
#define NUM_READINGS       10     // Avg readings for stability

// ── Objects ────────────────────────────────────────────────
HX711 scale;
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Change 0x27 if your I2C addr differs

// ── State ──────────────────────────────────────────────────
float expectedWeight = 0.0;
bool  waitingForBag  = false;
String inputBuffer   = "";

// ── Custom LCD Characters ──────────────────────────────────
byte checkMark[8] = {
  0b00000, 0b00001, 0b00011, 0b10110,
  0b11100, 0b01000, 0b00000, 0b00000
};
byte crossMark[8] = {
  0b00000, 0b10001, 0b01010, 0b00100,
  0b01010, 0b10001, 0b00000, 0b00000
};

// ─────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  // LCD Init
  lcd.init();
  lcd.backlight();
  lcd.createChar(0, checkMark);
  lcd.createChar(1, crossMark);

  lcd.setCursor(0, 0); lcd.print("  SmartMart  ");
  lcd.setCursor(0, 1); lcd.print(" Initializing...");
  delay(1500);

  // Scale Init
  scale.begin(HX711_DT, HX711_SCK);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare();  // Zero the scale

  // GPIO
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(LED_RED,    OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  allOff();

  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("System  Ready");
  lcd.setCursor(0, 1); lcd.print("Waiting for cmd");
  Serial.println("READY");
}

// ─────────────────────────────────────────────────────────
void loop() {
  // Read Serial commands from PC
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += ch;
    }
  }

  // If in verification mode, periodically update LCD with live weight
  if (waitingForBag && scale.is_ready()) {
    float liveWt = scale.get_units(3);
    if (liveWt < 0) liveWt = 0;
    lcd.setCursor(0, 1);
    lcd.print("Live:");
    lcd.print(liveWt, 0);
    lcd.print("g      ");
    delay(200);
  }
}

// ─────────────────────────────────────────────────────────
void processCommand(String cmd) {
  cmd.trim();

  // ── VERIFY:<expected_grams> ─────────────────────────────
  if (cmd.startsWith("VERIFY:")) {
    expectedWeight = cmd.substring(7).toFloat();
    waitingForBag  = true;
    allOff();

    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("Exp:" + String(expectedWeight,0) + "g");
    lcd.setCursor(0, 1); lcd.print("Place bag...");
    Serial.println("ACK:READY");

    delay(2000);  // Wait for customer to place bag
    performVerification();
  }

  // ── TARE (re-zero the scale) ────────────────────────────
  else if (cmd == "TARE") {
    scale.tare();
    Serial.println("ACK:TARED");
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("Scale Zeroed");
    delay(1000);
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("System  Ready");
    lcd.setCursor(0, 1); lcd.print("Waiting for cmd");
  }

  // ── PING (health check) ─────────────────────────────────
  else if (cmd == "PING") {
    Serial.println("PONG");
  }

  // ── READWEIGHT (one-shot reading) ──────────────────────
  else if (cmd == "READWEIGHT") {
    if (scale.is_ready()) {
      float w = scale.get_units(NUM_READINGS);
      if (w < 0) w = 0;
      Serial.println("WEIGHT:" + String(w, 1));
    } else {
      Serial.println("ERROR:SCALE_NOT_READY");
    }
  }
}

// ─────────────────────────────────────────────────────────
void performVerification() {
  waitingForBag = false;

  if (!scale.is_ready()) {
    Serial.println("ERROR:SCALE_NOT_READY");
    return;
  }

  // Average multiple readings for accuracy
  float actualWeight = scale.get_units(NUM_READINGS);
  if (actualWeight < 0) actualWeight = 0;

  float diff = actualWeight - expectedWeight;
  float absDiff = abs(diff);

  if (absDiff <= TOLERANCE_G) {
    // ── MATCHED ─────────────────────────────────────────
    greenPass();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.write(byte(0));  // ✓
    lcd.print(" MATCHED!");
    lcd.setCursor(0, 1);
    lcd.print("A:");
    lcd.print(actualWeight, 0);
    lcd.print("g E:");
    lcd.print(expectedWeight, 0);
    lcd.print("g");

    Serial.println("RESULT:MATCHED:" + String(actualWeight, 1));
    delay(5000);

  } else {
    // ── MISMATCH ─────────────────────────────────────────
    redAlert();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.write(byte(1));  // ✗
    lcd.print(" MISMATCH!");
    lcd.setCursor(0, 1);
    lcd.print("Diff:");
    lcd.print(diff, 0);
    lcd.print("g ALERT!");

    Serial.println("RESULT:MISMATCH:" + String(actualWeight, 1) + ":" + String(diff, 1));
    delay(8000);
  }

  // Reset
  allOff();
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("System  Ready");
  lcd.setCursor(0, 1); lcd.print("Waiting for cmd");
  Serial.println("RESET:READY");
}

// ── Hardware Helpers ───────────────────────────────────────
void greenPass() {
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_RED,   LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void redAlert() {
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED,   HIGH);
  // Buzzer beep pattern: 3 beeps
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH); delay(400);
    digitalWrite(BUZZER_PIN, LOW);  delay(200);
  }
  // Keep LED on
  digitalWrite(LED_RED, HIGH);
}

void allOff() {
  digitalWrite(LED_GREEN,  LOW);
  digitalWrite(LED_RED,    LOW);
  digitalWrite(BUZZER_PIN, LOW);
}
