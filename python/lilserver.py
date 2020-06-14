from flask import Flask, request, jsonify
from flask_serial import Serial
from openhab import OpenHAB
from flask_apscheduler import APScheduler
import mysql.connector as mariadb
import time

ROUND_TO_DECIMALS = 1
mariadb_password = open("mariadb_boot_pw.txt", "r").read().strip()


class DayAggregation:
    def __init__(self, metric):
        self.metric = metric
        self.last_reading = 0
        self.last_reading_time = time.time()
        self.aggregated_value = 0
        self.previous_value = 0

    def add_last_reading(self):
        self.aggregated_value += (self.last_reading * self.get_time_delta())

    def update(self):
        self.add_last_reading()
        self.last_reading = new_values[self.metric]
        self.last_reading_time = time.time()

    def get_time_delta(self):
        return (time.time() - self.last_reading_time) / 3600

    def send_if_changed(self):
        if round(self.aggregated_value) != round(self.previous_value):
            self.previous_value = self.aggregated_value
            send_to_openhab(self.get_item_name(), self.aggregated_value)

    def get_item_name(self):
        return self.metric + "H"

    def persist_and_reset(self, cursor):
        self.add_last_reading()
        cursor.execute(f"INSERT INTO {self.metric} (time,value) VALUES (NOW(),%s)", (self.aggregated_value,))
        self.last_reading = 0
        self.aggregated_value = 0


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
consumptions = []
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
settings = {'tanksensor': 3,
            'led-salon': 5,
            'led-vorschiff': 6,
            'analogMeasurements': 11,
            'analogDelay': 12,
            'digitalMeasurements': 13,
            'digitalDelay': 14,
            'heizung-power': 21,
            'heizung-temp': 22}


def read_data(message):
    try:
        address, command = message.split(':')
        # Get respective sensor and function from mapping dict
        sensor, function = address_to_sensor_mapping[int(address)]
        # Apply command to function and save result in list
        new_values[sensor] = function(float(command))
    except Exception as e:
        print(f"Error reading message: {type(e)}, {e}")
        print(f"message was '{message}'")
        raise


# Transformation functions, offset used to calibrate
def internal_voltage_5(value):
    # Voltage divider with 6.25V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((6.25 / 1024) * value, ROUND_TO_DECIMALS)


def internal_voltage_12(value):
    # Voltage divider with 17.05V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((17.05 / 1024) * value, ROUND_TO_DECIMALS)


def acs711(value, offset=0):
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
    print(f"Tank ist {value}")
    return round((value - 1100) / 8, 0)


def just_return(value):
    return value


# Calculation function
def calc():
    new_values['Pverb'] = round(new_values['Iverb'] * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Pinverter'] = round(new_values['Iinverter'] * new_values['U12v'], ROUND_TO_DECIMALS)
    # minus Ibat cause it's wired the wrong way :D
    new_values['Pbat'] = round((-new_values['Ibat'] - new_values['Iinverter']) * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Ppv'] = round((-new_values['Ibat'] + new_values['Iverb']) * new_values['U12v'], ROUND_TO_DECIMALS)
    for metric in consumptions:
        metric.update()

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

    for metric in consumptions:
        metric.send_if_changed()


def reset_day_counters():
    mariadb_connection = mariadb.connect(host='debian.fritz.box', user='boot', password=mariadb_password,
                                         database='boot')
    cursor = mariadb_connection.cursor()
    [x.persist_and_reset(cursor) for x in consumptions]
    mariadb_connection.commit()
    mariadb_connection.close()


def serial_send(address, command):
    ser.on_send(f"+{address}:{command}-")


def initialize_objects():
    global address_to_sensor_mapping
    global consumptions
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
    consumptions = [DayAggregation('Pverb'),
                    DayAggregation('Pinverter'),
                    DayAggregation('Pbat'),
                    DayAggregation('Ppv')]


@app.route('/')
def use_serial():
    return 'No command specified. Use specific endpoint instead.'


@app.route('/settings')
def edit_settings():
    setting = request.args.get('s', type=str)
    value = request.args.get('v', type=int)
    try:
        serial_send(settings[setting], value)
    except KeyError:
        return f"Setting {setting} could not be found"
    except Exception as ex:
        return f"Unknown error: {type(ex)}, {ex}"
    return f"Successfully set {setting} to {value}"


@app.route('/led-salon')
def led1_route():
    serial_send(settings["led-salon"], request.args.get('val', type=int))
    return "ok"


@app.route('/led-vorschiff')
def led2_route():
    serial_send(settings["led-vorschiff"], request.args.get('val', type=int))
    return "ok"


@app.route('/tanksensor')
def tanksensor_route():
    value = request.args.get('val', type=int)
    serial_send(settings['tanksensor'], value)
    return 'ok'


# ToDo: State management
@app.route('/heating')
def heating_route():
    channel = request.args.get('ch', type=str)
    value = request.args.get('val', type=int)
    serial_send(settings[channel], value)
    return 'ok'


@app.route('/debug')
def debug_data():
    return jsonify({'new_values': new_values,
                    'old_values': old_values,
                    'settings': settings}, )


@ser.on_message()
def handle_incoming_message(msg):
    message = msg.decode("utf-8")
    print(message)
    for s in message.split('_'):
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
    initialize_objects()
    app.apscheduler.add_job('tracking', func=track, trigger='interval', seconds=10)
    app.apscheduler.add_job('day_counter', func=reset_day_counters, trigger='cron', hour='0')
    print("Initialisation finished, running App")
    app.run(debug=True, host='0.0.0.0')
