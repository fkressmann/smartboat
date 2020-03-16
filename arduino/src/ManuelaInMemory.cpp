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
  for(int i = 3; i < 8; i++) {
    pinMode(i, OUTPUT);
  }
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

int measureAnalog(int pin) {
  long adcs = 0;
  for (int i=0; i<50; i++) {
      adcs = adcs + analogRead(pin);
      delay(10);
    }
  sendData(pin, (adcs / 50));
  return (adcs / 50);
}

int measureDigital(int pin) {
  long adcs = 0;
  for (int i=0; i<25; i++) {
      adcs = adcs + pulseIn(pin, HIGH, 40000);
      delay(20);
    }
  sendData(pin, (adcs / 25));
  return (adcs / 25);
}

void sendData() {
  for (int i=0; i<9; i++) {
      toPrint.concat(m[i]);
      toPrint.concat(":");
    }
  Serial.println(toPrint);
  toPrint = "+";
}

void executeNext(int item) {
  switch (item) {
  case 1:
    analogReference(INTERNAL);
    for (int i=0; i<10; i++) {
      delay(10);
      analogRead(A0);
    }
    break;
  case 2:
    m[0] = measureAnalog(A0);
    break;
  case 3:
    m[1] = measureAnalog(A1);
    break;
  case 4:
    analogReference(DEFAULT);
    for (int i=0; i<10; i++) {
      delay(10);
      analogRead(A2);
    }
    break;
  case 5:
    m[2] = measureAnalog(A2);
    break;
  case 6:
    m[3] = measureAnalog(A3);
    break;
  case 7:
    m[4] = measureAnalog(A4);
    break;
  case 8:
    m[5] = measureAnalog(A5);
    break;
  case 9:
    m[6] = measureAnalog(A6);
    break;
  case 10:
    m[7] = measureAnalog(A7);
    break;
  case 11:
    m[8] = measureDigital(2);
    break;
  case 100:
    sendData();
    break;
  }
}

void commandExecutor(int device, int value) {
  switch (device) {
    // LED 1
    case 1:
      analogWrite(5, value);
      break;
    // LED2
    case 2:
      analogWrite(6, value);
      break;
    // Heizung einschalten
    case 3:
      mySwitch.send(547162328, 31);
      break;
    // Heizung ausschalten
    case 4:
      mySwitch.send(547160708, 31);
      break;
    // Heizung Temperatur erhöhen
    case 5:
      mySwitch.send(547161208, 31);
      break;
    // Heizung Temperatur senken
    case 6:
      mySwitch.send(547160388, 31);
      break;
  }
}

void serialExecutor() {
  int separatorPos = commandBuffer.indexOf(':');
  if (separatorPos != -1) {
    int device = commandBuffer.substring(0, separatorPos).toInt();
    int value = commandBuffer.substring(separatorPos + 1).toInt();
    Serial.println("Rec:" + String(device) + "+" + String(value));
    commandExecutor(device, value);
  }
}


// LOOP
void loop() {
  executeNext(executionCounter);
  executionCounter++;
  if (executionCounter > 12) {
    executionCounter = 1;
  }
}

// ON SERIAL EVENT
void serialEvent() {
  while (Serial.available()) {

    char inChar = (char)Serial.read();

    if (inChar == '+') {
      commandBufferValid = true;
      commandBuffer = "";
    } else if (commandBufferValid && inChar == '-') {
      serialExecutor();
      commandBufferValid = false;
    } else if (commandBufferValid) {
      commandBuffer += inChar;
    }
  }
}
