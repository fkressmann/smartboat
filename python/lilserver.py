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
openhab = OpenHAB(base_url)
items = openhab.fetch_all_items()

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


### Transformation functions
def internal_voltage_5(value):
    return round((6.25 / 1024) * value, ROUND_TO_DECIMALS)


def internal_voltage_12(value):
    return round((17.05 / 1024) * value, ROUND_TO_DECIMALS)


def acs711(value, offset=0):
    return round(0.0716520039 * (value + offset) - 36.65, ROUND_TO_DECIMALS)


def acs709(value, offset=0):
    # ToDo: clarify calculation values
    return round(0.0716520039 * (value + offset) - 36.65, ROUND_TO_DECIMALS)


def tank(value, offset=0):
    # ToDo: clarify calculation values
    return round(123, -1)


def just_return(value):
    return value


# Calculation function
def calc():
    new_values['Pverb'] = round(new_values['Iverb'] * new_values['U12v'], 1)
    new_values['Pbat'] = round((new_values['Ibat'] + new_values['Iinverter']) * new_values['U12v'], 1)
    new_values['Ppv'] = round((new_values['Ibat'] + new_values['Iverb']) * new_values['U12v'], 1)
    new_values['Pinverter'] = round(new_values['Iinverter'] * new_values['U12v'], 1)


def track():
    print("### TRACKING ###")
    calc()
    for sensor, old_value in old_values.items():
        new_value = new_values[sensor]
        if new_value != old_value:
            old_values[sensor] = new_values[sensor]
            items.get(sensor).update(new_value)
            print(sensor + ":" + str(new_value))


def handle_led_command(arduino_pin_no):
    param = request.args.get('val', type=int)
    param = int(round(param * 2.55, 0))
    print('LED{} rec. param {}', arduino_pin_no, param)
    serial_send(arduino_pin_no, param)
    return 'ok' + str(param)


def serial_send(address, command):
    ser.on_send('+{}:{}-'.format(address, command))


def build_mapping_dict():
    global address_to_sensor_mapping
    address_to_sensor_mapping = {14: ('U12v', internal_voltage_12),
                                 15: ('U5v', internal_voltage_5),
                                 17: ('Iverb', acs711),
                                 18: ('Ibat', acs711),
                                 19: ('Iinverter', acs711),
                                 20: ('Awasser1', just_return),
                                 21: ('Awasser2', just_return),
                                 2: ('Atank', tank)
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


@ser.on_message()
def handle_incoming_message(msg):
    message = msg.decode("utf-8").split('-')
    print(message)
    for s in message:
        if s[0] == '+':
            # Cut out '+'
            read_data(s[1:])


#@ser.on_log()
def handle_logging(level, info):
    print(level, info)
    pass


if __name__ == '__main__':
    build_mapping_dict()
    app.apscheduler.add_job('tracking', func=track, trigger='interval', seconds=10)
    app.run(host='0.0.0.0')
