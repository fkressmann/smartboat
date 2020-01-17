#include <Arduino.h>

int executionCounter = 1;
int m[9];
String toPrint = "+";
String commandBuffer = "";
boolean commandBufferValid = false;

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.println("Startup completed");
  pinMode(2, INPUT);
  for(int i = 3; i < 8; i++) {
    pinMode(i, OUTPUT);
  }
}

int measureAnalog(int pin) {
  long adcs = 0;
  for (int i=0; i<50; i++) {
      adcs = adcs + analogRead(pin);
      delay(10);
    }
  return (adcs / 50);
}

int measureDigital(int pin) {
  long adcs = 0;
  for (int i=0; i<25; i++) {
      adcs = adcs + pulseIn(pin, HIGH, 40000);
      delay(20);
    }
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
  case 12:
    sendData();
    break;
  }
}

void serialExecutor() {
  int separatorPos = commandBuffer.indexOf(':');
  if (separatorPos != -1) {
    String device = commandBuffer.substring(0, separatorPos);
    int value = commandBuffer.substring(separatorPos + 1).toInt();
    Serial.println("Rec:" + device + String(value));
    if (device == "led1") {
      analogWrite(5, value);
    } else if (device == "led2") {
      analogWrite(6, value);
    }
  }
}

// the loop routine runs over and over again forever:
void loop() {
  executeNext(executionCounter);
  executionCounter++;
  if (executionCounter > 12) {
    executionCounter = 1;
  }
}

void serialEvent() {
  while (Serial.available()) {

    char inChar = (char)Serial.read();

    if (inChar == '+') {
      commandBufferValid = true;
    } else if (commandBufferValid && inChar == '-') {
      serialExecutor();
      commandBuffer = "";
    } else if (commandBufferValid) {
      commandBuffer += inChar;
    }
  }
}
