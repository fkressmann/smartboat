#include <Arduino.h>
#include <RCSwitch.h>

int executionCounter = 1;
int m[9];
int track[22];
String toPrint = "+";
String commandBuffer = "";
boolean commandBufferValid = false;
RCSwitch mySwitch = RCSwitch();

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  mySwitch.enableTransmit(10);
  mySwitch.setPulseLength(256);
  pinMode(2, INPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  // initialize tracking array
  for (int i = 0; i < 22; i++) {
    track[i] = 0;
  }
  Serial.println("Startup completed");
}

void sendData(int pin, int value) {
  if (track[pin] != value) {
    track[pin] = value;
    Serial.print('+' + String(pin) + ':' + String(value) + '-');
  }
}

void measureAnalog(int pin) {
  long adcs = 0;
  for (int i=0; i<50; i++) {
      adcs = adcs + analogRead(pin);
      delay(10);
    }
  sendData(pin, (adcs / 50));
}

void measureDigital(int pin) {
  long adcs = 0;
  for (int i=0; i<25; i++) {
      adcs = adcs + pulseIn(pin, HIGH);
      delay(20);
    }
  int value = (adcs / 25);
  if (value != 0) sendData(pin, value);
}

void readNextValue(int item) {
  switch (item) {
  case 1:
    analogReference(INTERNAL);
    for (int i=0; i<10; i++) {
      delay(10);
      analogRead(A0);
    }
    break;
  case 2:
    measureAnalog(A0);
    break;
  case 3:
    measureAnalog(A1);
    break;
  case 4:
    analogReference(DEFAULT);
    for (int i=0; i<10; i++) {
      delay(10);
      analogRead(A2);
    }
    break;
  case 5:
    // measureAnalog(A2);
    break;
  case 6:
    measureAnalog(A3);
    break;
  case 7:
    measureAnalog(A4);
    break;
  case 8:
    measureAnalog(A5);
    break;
  case 9:
    measureAnalog(A6);
    break;
  case 10:
    measureAnalog(A7);
    break;
  case 11:
    measureDigital(2);
    break;
  }
}

void serialCommandExecutor() {
  int separatorPos = commandBuffer.indexOf(':');
  if (separatorPos != -1) {
    int device = commandBuffer.substring(0, separatorPos).toInt();
    int value = commandBuffer.substring(separatorPos + 1).toInt();
    Serial.println("Rec:" + String(device) + ':' + String(value) + '-');

    switch (device) {
    // LED 1
    case 5:
      analogWrite(5, value);
      break;
    // LED2
    case 6:
      analogWrite(6, value);
      break;
    // Heizung einschalten
    case 1:
      mySwitch.send(547162328, 31);
      break;
    // Heizung ausschalten
    case 2:
      mySwitch.send(547160708, 31);
      break;
    // Heizung Temperatur erhöhen
    case 3:
      mySwitch.send(547161208, 31);
      break;
    // Heizung Temperatur senken
    case 4:
      mySwitch.send(547160388, 31);
      break;
    }
  }
}


// LOOP
void loop() {
  readNextValue(executionCounter);
  executionCounter++;
  if (executionCounter > 12) {
    executionCounter = 1;
  }
  delay(100);
}

// ON SERIAL EVENT
void serialEvent() {
  while (Serial.available()) {

    char inChar = (char)Serial.read();

    if (inChar == '+') {
      commandBufferValid = true;
      commandBuffer = "";
    } else if (commandBufferValid && inChar == '-') {
      serialCommandExecutor();
      commandBufferValid = false;
    } else if (commandBufferValid) {
      commandBuffer += inChar;
    }
  }
}
