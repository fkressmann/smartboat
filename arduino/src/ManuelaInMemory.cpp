#include <Arduino.h>

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  pinMode(2, INPUT);
}
String m[9];
String toPrint = "";

String measureAnalog(int pin) {
  long adcs = 0;
  for (int i=0; i<50; i++) {
      adcs = adcs + analogRead(pin);
      delay(10);
    }
  return String(adcs / 50);
}

String measureDigital(int pin) {
  long adcs = 0;
  for (int i=0; i<25; i++) {
      adcs = adcs + pulseIn(pin, HIGH, 40000);
      delay(20);
    }
  return String(adcs / 25);
}

// the loop routine runs over and over again forever:
void loop() {
  analogReference(INTERNAL);
  for (int i=0; i<10; i++) {
    delay(10);
    analogRead(A0);
  }
  m[0] = measureAnalog(A0);
  m[1] = measureAnalog(A1);
  analogReference(DEFAULT);
  for (int i=0; i<10; i++) {
    delay(10);
    analogRead(A2);
  }
  m[2] = measureAnalog(A2);
  m[3] = measureAnalog(A3);
  m[4] = measureAnalog(A4);
  m[5] = measureAnalog(A5);
  m[6] = measureAnalog(A6);
  m[7] = measureAnalog(A7);
  m[8] = measureDigital(2);

  for (int i=0; i<9; i++) {
    toPrint.concat(m[i]);
    toPrint.concat(":");
  }

  Serial.println(toPrint);
  toPrint = "";
}
