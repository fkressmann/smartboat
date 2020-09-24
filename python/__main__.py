from flask import Flask
from flask_serial import Serial
from openhab import OpenHAB
from flask_apscheduler import APScheduler
import mysql.connector as mariadb
import time
import python.transformations as tr
import python.helper as helper
from python.day_aggregation import DayAggregation
from python.battery import read_from_bms

ROUND_TO_DECIMALS = 1
mariadb_password = open("mariadb_boot_pw.txt", "r").read().strip()


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
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

ser = Serial(app)
serial_buffer = ""
time_of_last_reading = 0
system_state = True
sending_to_openhab_enabled = False

# Openhab Init
base_url = 'http://localhost:8080/rest'
try:
    openhab = OpenHAB(base_url)
    items = openhab.fetch_all_items()
except Exception as e:
    print("Could not establish OH connection or read data: ", type(e), e)


def send_to_openhab(sensor, new_value):
    if sending_to_openhab_enabled:
        try:
            items.get(sensor).update(new_value)
        except Exception as e:
            print("Error sending to OpenHAB: ", type(e), e)


address_to_sensor_mapping = {14: ('U12v', tr.internal_voltage_12),  # A0
                             15: ('U5v', tr.internal_voltage_5),  # A1
                             16: ('Iinverter', tr.shunt75mv),  # A2
                             17: ('Iverb', tr.acs711),  # A3
                             18: ('Ibat', tr.acs711),  # A4
                             # 19: ('Reserve Analog', tr.just_return),  # A5
                             20: ('Awasser1', tr.just_return),  # A6
                             21: ('Awasser2', tr.just_return),  # A7
                             2: ('Atank', tr.tank)  # D2
                             }
consumptions = [DayAggregation('Pverb'),
                DayAggregation('Pinverter'),
                DayAggregation('Pbat'),
                DayAggregation('Ppv')]

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
              'ULiFe': 0,
              'ILiFe': 0,
              'RSOCLiFe': 0,
              'TimeLiFe': 0
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
              'ULiFe': 0,
              'RSOCLiFe': 0,
              'TimeLiFe': 0
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


# Calculation function
def calculate_mesaurements():
    new_values['Pverb'] = round(new_values['Iverb'] * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Pinverter'] = round(new_values['Iinverter'] * new_values['U12v'], ROUND_TO_DECIMALS)
    # minus Ibat cause it's wired the wrong way :D
    # old Pb battery: new_values['Pbat'] = round((-new_values['Ibat'] - new_values['Iinverter']) * new_values['U12v'], ROUND_TO_DECIMALS)
    new_values['Pbat'] = round(new_values['ILiFe'] * new_values['ULiFe'], ROUND_TO_DECIMALS)
    new_values['Ppv'] = round((-new_values['Ibat'] + new_values['Iverb']) * new_values['U12v'], ROUND_TO_DECIMALS)
    for metric in consumptions:
        metric.update(system_state, new_values)


def check_system_state():
    global system_state, time_of_last_reading
    if time.time() < time_of_last_reading + 60:
        if system_state is False:
            print(f"{helper.print_time()}: System operational")
            send_to_openhab("SystemState", f"OPERATIONAL - seit {helper.print_time()}")
        system_state = True
        return True
    else:
        if system_state is True:
            print(f"{helper.print_time()}: System failure")
            send_to_openhab("SystemState", f"FAILURE - seit {helper.print_time()}")
        system_state = False
        return False


def track_changed_values_and_send():
    # print("### TRACKING ###")
    read_from_bms(new_values)
    calculate_mesaurements()
    for sensor, old_value in old_values.items():
        new_value = new_values[sensor]
        if new_value != old_value:
            old_values[sensor] = new_values[sensor]
            send_to_openhab(sensor, new_value)
            print(f"Sending {new_value} to item {sensor}")

    if check_system_state():
        for metric in consumptions:
            metric.send_if_changed(send_to_openhab)


def reset_day_counters():
    mariadb_connection = mariadb.connect(host='debian.fritz.box', user='boot', password=mariadb_password,
                                         database='boot')
    cursor = mariadb_connection.cursor()
    [x.persist_and_reset(cursor) for x in consumptions]
    mariadb_connection.commit()
    mariadb_connection.close()


if __name__ == '__main__':
    app.apscheduler.add_job('tracking', func=track_changed_values_and_send, trigger='interval', seconds=10)
    app.apscheduler.add_job('day_counter', func=reset_day_counters, trigger='cron', hour='0')
    send_to_openhab("SystemState", f"OPERATIONAL - seit {helper.print_time()}")
    print("Initialisation finished, running App")
    app.run(host='0.0.0.0')
