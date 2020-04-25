#include <Arduino.h>
#include <RCSwitch.h>

int analogMeasurements = 50;
int analogDelay = 2;
int digitalMesaurements = 0;
int digitalDelay = 0;

int executionCounter = 1;

int led5is = 0;
int led5tobe = 0;
int led6is = 0;
int led6tobe = 0;

int m[9];
int track[22];

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

void checkFade() {
  // Check LED5
  if (led5is < led5tobe) {
    analogWrite(5, ++led5is);
  } else if (led5is > led5tobe) {
    analogWrite(5, --led5is);
  }

  // Check LED6
  if (led6is < led6tobe) {
    analogWrite(6, ++led6is);
  } else if (led6is > led6tobe) {
    analogWrite(6, --led6is);
  }
}

void sendData(int pin, int value) {
  if (track[pin] != value) {
    track[pin] = value;
    Serial.print('+' + String(pin) + ':' + String(value) + '-');
  }
}

void measureAnalog(int pin) {
  long adcs = 0;
  for (int i=0; i < analogMeasurements; i++) {
    adcs = adcs + analogRead(pin);
    delay(analogDelay);
    }
  sendData(pin, (adcs / analogMeasurements));
}

void measureDigital(int pin) {
  long pulse = 0;
  for (int i = 0; i < digitalMesaurements; i++) {
    pulse = pulse + pulseIn(pin, HIGH, 4000);
    delay(digitalDelay);
    }
  int value = (pulse / digitalMesaurements);
  if (value != 0) sendData(pin, value);
}

void readNextValue(int item) {
  switch (item) {
  case 1:
    analogReference(INTERNAL);
    for (int i = 0; i < analogMeasurements; i++) {
    }
    break;
  case 2:
    measureAnalog(A0);
    break;
  case 3:
    measureAnalog(A1);
    break;
  case 4:
    measureAnalog(A2);
    break;
  case 5:
    analogReference(DEFAULT);
    for (int i = 0; i < analogMeasurements; i++) {
      analogRead(A2);
    }
    break;
  //case 6:
    // measureAnalog(A5);
    //break;
  case 7:
    measureAnalog(A3);
    break;
  case 8:
    measureAnalog(A4);
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
      led5tobe = value;
      break;
    // LED2
    case 6:
      led6tobe = value;
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
    case 11:
      analogMeasurements = value;
      break;
    // Heizung ausschalten
    case 12:
      analogDelay = value;
      break;
    // Heizung Temperatur erhöhen
    case 13:
      digitalMesaurements = value;
      break;
    // Heizung Temperatur senken
    case 14:
      digitalDelay = value;
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
  checkFade();
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
