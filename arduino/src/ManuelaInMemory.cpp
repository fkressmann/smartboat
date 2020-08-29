#include <Arduino.h>
#include <avr/wdt.h>
#include <RCSwitch.h>

int analogMeasurements = 50;
int analogCounter = 0;
long analogValue = 0;
int digitalMesaurements = 25;
int digitalCounter= 0;
long digitalValue = 0;

int executionCounter = 1;

int led5is = 0;
int led5tobe = 0;
int led6is = 0;
int led6tobe = 0;
bool tanksensor = false;

int track[22];

String commandBuffer = "";
boolean commandBufferValid = false;
RCSwitch mySwitch = RCSwitch();

void setup() {
  wdt_enable(WDTO_4S);
  Serial.begin(9600);
  mySwitch.enableTransmit(10);
  mySwitch.setPulseLength(256);
  pinMode(2, INPUT);
  pinMode(3, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  // initialize tracking array
  for (int i = 0; i < 22; i++) {
    track[i] = 0;
  }
  Serial.print("Startup completed");
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

void sendData(int pin, long value) {
  if (track[pin] != value) {
    track[pin] = value;
    String dataToSend = '+' + String(pin) + ':' + String(value) + '_';
    if (dataToSend.startsWith("+") && dataToSend.endsWith("_")) {
      Serial.print(dataToSend);
    } else {
      Serial.print("Crap data");
    }
  }
}

void measureAnalog(int pin) {
  analogCounter++;
  if (analogCounter <= analogMeasurements) {
    analogValue = analogValue + analogRead(pin);
    executionCounter--;
  } else {
    sendData(pin, (analogValue / analogMeasurements));
    analogValue = 0;
    analogCounter = 0;
  }
}

void measureDigital(int pin) {
  if (tanksensor) {
    long newPulse = 0;
    digitalCounter++;
    if (digitalCounter <= digitalMesaurements) {
      newPulse = pulseIn(pin, HIGH, 50000);
      if (newPulse != 0) {
        digitalValue += newPulse;
        executionCounter--;
      }
    } else {
      int value = (digitalValue / digitalMesaurements);
      sendData(pin, value);
      digitalValue = 0;
      digitalCounter = 0;
    }
  }
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
    Serial.print("A-Rec:" + String(device) + ':' + String(value) + '-');

    switch (device) {
      // Tanksensor
      case 3:
        tanksensor = value;
        digitalWrite(3, value);
        break;
      // LED 1
      case 5:
        led5tobe = value;
        break;
      // LED2
      case 6:
        led6tobe = value;
        break;
        
      case 11:
        analogMeasurements = value;
        break;
      case 12:
        // analogDelay = value;
        break;
      case 13:
        digitalMesaurements = value;
        break;
      case 14:
        // digitalDelay = value;
        break;

      // Heizung Power
      case 21:
        if (value == 1) {
          mySwitch.send(547162328, 31); // an
        } else if (value == 0) {
          mySwitch.send(547160708, 31); // aus
        }
        break;
      // Heizung Temperatur
      case 22:
        if (value == 1) {
          mySwitch.send(547161208, 31); // erhoehen
        } else if (value == 0) {
          mySwitch.send(547160388, 31); // senken
        }
        break;
    }
  }
}


// LOOP
void loop() {
  wdt_reset();
  readNextValue(executionCounter);
  executionCounter++;
  if (executionCounter > 11) {
    executionCounter = 1;
  }
  unsigned long previousMillis = millis();
  while (millis() < previousMillis + 10) {
    checkFade();
    delay(1);
  }
  // Serial.println("finished loop run: " + String(executionCounter));
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
