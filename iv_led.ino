// LED I-V sweep with an ESP32, used to measure Planck's constant.
//
// Wiring:
//   GPIO25 (DAC) --+-- LED anode (long leg)
//                  |
//                GPIO34 (Va, voltage at the anode)
//
//   LED cathode (short leg) --+-- 220 ohm resistor -- GND
//                             |
//                           GPIO35 (Vb, voltage across the resistor)
//
// V_LED = Va - Vb, I = Vb / R.
// Usage: open the Serial Monitor at 115200 baud and send one letter
// (r, y, g, b) to measure the LED currently on the breadboard.
// Output: CSV rows of the sweep, then a RESULT line with the LED voltage at 1 mA.

#define PIN_DAC 25
#define PIN_VA  34
#define PIN_VB  35

const float R_OHM       = 220.0f;
const float I_TARGET_MA = 1.0f;

float readMv(int pin) {
  uint32_t s = 0;
  for (int i = 0; i < 64; i++) s += analogReadMilliVolts(pin);
  return s / 64.0f;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_VA, ADC_11db);  // up to ~3 V at the anode
  analogSetPinAttenuation(PIN_VB, ADC_0db);   // better resolution around 0.2 V
  dacWrite(PIN_DAC, 0);
  Serial.println("Send a letter (r/y/g/b) to measure the LED on the breadboard.");
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == '\n' || c == '\r' || c == ' ') return;
  while (Serial.available()) Serial.read();

  Serial.printf("# LED %c\n# dac,Va_mV,Vb_mV,I_mA,Vled_mV\n", c);

  float prevV = 0, prevI = 0, vAt = 0;
  bool found = false;

  for (int d = 0; d <= 255; d++) {
    dacWrite(PIN_DAC, d);
    delay(5);
    float va = readMv(PIN_VA);
    float vb = readMv(PIN_VB);
    float i  = vb / R_OHM;            // mV / ohm = mA
    float vl = va - vb;
    Serial.printf("%d,%.0f,%.0f,%.3f,%.0f\n", d, va, vb, i, vl);

    if (!found && d > 0 && i >= I_TARGET_MA) {
      float t = (I_TARGET_MA - prevI) / (i - prevI);   // linear interpolation
      vAt = prevV + t * (vl - prevV);
      found = true;
    }
    prevV = vl; prevI = i;
    if (found && i > 2.0f * I_TARGET_MA) break;        // do not push the LED further
  }
  dacWrite(PIN_DAC, 0);

  if (found) Serial.printf("RESULT %c: V at %.1f mA = %.0f mV\n", c, I_TARGET_MA, vAt);
  else       Serial.printf("RESULT %c: %.1f mA not reached\n", c, I_TARGET_MA);
}
