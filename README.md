# SmartBoat
Stuff I did to make a boat from the 1970s smart.

## Components
The System is made of three main components: OpenHAB as smarthome server, a Python middleware and an Arduino 

### OpenHAB
Openhab is used as central controller of everything. It primarily takes care of the user interactions, there is a 
touchscreen in the boat and the OpenHAB cloud connections for controlling from home are used. Some things interface 
directly with OpenHAB like WiFi RGB LED controllers, temperature sensors etc. All the custom-built sensors are connected
through the Python middleware. The REST API of OpenHAB is used for updating the state of items. Commands are sent using
the HTTP binding to Flask.

### Python
The Python middleware reads the raw measurements from the Arduino, applies some calculations and sends them to OpenHAB.
Commands are received and relayed to the Arduino. Communication to the Arduino is handled over serial.

### Arduino
The Arduino part connects to most of the hardware to read sensors and control actors. There is a basic algorithm to
debounce the readings and only send changed values.
