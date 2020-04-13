from flask import Flask, request
from flask_serial import Serial
from openhab import OpenHAB
from flask_apscheduler import APScheduler

ROUND_TO_DECIMALS = 1

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
app.config['SERIAL_TIMEOUT'] = 2
app.config['SERIAL_PORT'] = '/dev/ttyAMA0'
app.config['SERIAL_BAUDRATE'] = 9600
app.config['SERIAL_BYTESIZE'] = 8
app.config['SERIAL_PARITY'] = 'N'
app.config['SERIAL_STOPBITS'] = 1

ser = Serial(app)
serial_buffer = ""

base_url = 'http://localhost:8080/rest'
try:
    openhab = OpenHAB(base_url)
    items = openhab.fetch_all_items()
except Exception as e:
    print("Could not establish OH connection or read data: ", type(e), e)

address_to_sensor_mapping = {}

new_values = {'Iverb': 0,
              'Ibat': 0,
              'Iinverter': 0,
              'U12v': 0,
              'U5v': 0,
              'Pverb': 0,
              'Ppv': 0,
              'Pbat': 0,
              'Pinverter': 0,
              'Atank': 0,
              'Awasser1': 0,
              'Awasser2': 0,
              }
old_values = {'U12v': 0,
              'U5v': 0,
              'Pverb': 0,
              'Ppv': 0,
              'Pbat': 0,
              'Pinverter': 0,
              'Atank': 0,
              'Awasser1': 0,
              'Awasser2': 0,
              }


def read_data(message):
    try:
        address, command = message.split(':')
        # Get respective sensor and function from mapping dict
        sensor, function = address_to_sensor_mapping[int(address)]
        # Apply command to function and save result in list
        new_values[sensor] = function(float(command))
    except Exception as e:
        print("Exception occured: ", type(e), e)
        print('message was: ', message)
        raise


# Transformation functions, offset used to calibrate
def internal_voltage_5(value):
    # Voltage divider with 6.25V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((6.25 / 1024) * value, ROUND_TO_DECIMALS)


def internal_voltage_12(value):
    # Voltage divider with 17.05V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((17.05 / 1024) * value, ROUND_TO_DECIMALS)


def acs711(value, offset=2):
    # ADC Uref = Vin (5V). Same as Vcc of acs711, so proportions apply
    # 0A = Vin/2. 36.65A = Vin. 0.0716520039 = 73.3 / 1023 (no idea anymore why 1023 instead of 1024 but it works)
    return round(0.0716520039 * (value + offset) - 36.65, ROUND_TO_DECIMALS)


def shunt75mv(value, offset=5.58):
    # 75mV at 100A Shunt, 20 times amplified by AD8217 so 1.5V. 1.1V Uout 73.3A. ADC Uref = 1.1V
    # 0,071614583 = 73.3 / 1024
    offset = offset if value else 0  # Only apply offset if reading is not 0
    return round(0.071614583 * (value + offset), ROUND_TO_DECIMALS)


def tank(value):
    # PWM pulse high time in µS. 1100µS = 0%, 1900µS = 100%. Time divided by 8 is percentage
    return round((value - 1100) / 8, 0)


def just_return(value):
    return value


# Calculation function
def calc():
    new_values['Pverb'] = round(new_values['Iverb'] * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Pbat'] = round((new_values['Ibat'] + new_values['Iinverter']) * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Ppv'] = round((new_values['Ibat'] + new_values['Iverb']) * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Pinverter'] = round(new_values['Iinverter'] * new_values['U12v'], ROUND_TO_DECIMALS)


def send_to_openhab(sensor, new_value):
    try:
        items.get(sensor).update(new_value)
    except Exception as e:
        print("Stuff happened: ", type(e), e)


def track():
    # print("### TRACKING ###")
    calc()
    for sensor, old_value in old_values.items():
        new_value = new_values[sensor]
        if new_value != old_value:
            old_values[sensor] = new_values[sensor]
            send_to_openhab(sensor, new_value)


def handle_led_command(arduino_pin_no):
    param = request.args.get('val', type=int)
    param = int(round(param * 2.55, 0))
    print('LED{} rec. param {}'.format(arduino_pin_no, param))
    serial_send(arduino_pin_no, param)
    return 'ok' + str(param)


def serial_send(address, command=0):
    ser.on_send('+{}:{}-'.format(address, command))


def build_mapping_dict():
    global address_to_sensor_mapping
    address_to_sensor_mapping = {14: ('U12v', internal_voltage_12),  # A0
                                 15: ('U5v', internal_voltage_5),  # A1
                                 16: ('Iinverter', shunt75mv),  # A2
                                 17: ('Iverb', acs711),  # A3
                                 18: ('Ibat', acs711),  # A4
                                 # 19: ('Reserve Analog', just_return),  # A5
                                 20: ('Awasser1', just_return),  # A6
                                 21: ('Awasser2', just_return),  # A7
                                 2: ('Atank', tank)  # D2
                                 }


@app.route('/')
def use_serial():
    return 'No command specified. Use specific endpoint instead.'


@app.route('/led1')
def led1_route():
    return handle_led_command(5)


@app.route('/led2')
def led2_route():
    return handle_led_command(6)


# ToDo: State management
@app.route('/heating')
def heating_route():
    channel = request.args.get('ch', type=str)
    value = request.args.get('val', type=int)
    if channel == 'power':
        if value == 1:
            serial_send(1)
        elif value == 0:
            serial_send(2)
    elif channel == 'temp':
        if value == 1:
            serial_send(3)
        elif value == 0:
            serial_send(4)


@ser.on_message()
def handle_incoming_message(msg):
    message = msg.decode("utf-8").split('-')
    for s in message:
        if s[0] == '+':
            # Cut out '+'
            read_data(s[1:])
        elif s != '':
            print("Cant handle message: ", s)


# @ser.on_log()
def handle_logging(level, info):
    print(level, info)
    pass


if __name__ == '__main__':
    build_mapping_dict()
    app.apscheduler.add_job('tracking', func=track, trigger='interval', seconds=10)
    app.run(host='0.0.0.0')
