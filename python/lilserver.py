from flask import Flask, request
from flask_serial import Serial

app = Flask(__name__)
app.config['SERIAL_TIMEOUT'] = 2
app.config['SERIAL_PORT'] = '/dev/ttyAMA0'
app.config['SERIAL_BAUDRATE'] = 9600
app.config['SERIAL_BYTESIZE'] = 8
app.config['SERIAL_PARITY'] = 'N'
app.config['SERIAL_STOPBITS'] = 1

ser = Serial(app)
command_string = '+led{}:{}-'

n = {'Iverb': 0,
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
o = {'U12v': 0,
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
    # A0, A1, A2, A3, A4, A5, A6, A7, D2
    try:
        print('generating iter')
        data = iter((float(e) for e in message.split(":")))
        n['U12v'] = internal_voltage(17.05, next(data))
        n['U5v'] = internal_voltage(6.25, next(data))
        next(data)
        n['Iverb'] = acs711(next(data))
        n['Ibat'] = acs711(next(data))
        n['Iinverter'] = acs711(next(data))
        n['Awasser1'] = next(data)
        n['Awasser2'] = next(data)
        n['Atank'] = tank(next(data))
    except Exception:
        print("Exception occured")


def internal_voltage(Umax, value):
    return round((Umax / 1024) * value, 2)


def acs711(value, offset=0):
    return round(0.0716520039 * (value + offset) - 36.65, 2)


def acs709(value, offset=0):
    # ToDo: clarify calculation values
    return round(0.0716520039 * (value + offset) - 36.65, 2)


def tank(value, offset=0):
    # ToDo: clarify calculation values
    return round(123, -1)


def calc():
    n['Pverb'] = round(n['Iverb'] * n['U12v'], 1)
    n['Pbat'] = round((n['Ibat'] + n['Iinverter']) * n['U12v'], 1)
    n['Ppv'] = round((n['Ibat'] + n['Iverb']) * n['U12v'], 1)
    n['Pinverter'] = round(n['Iinverter'] * n['U12v'], 1)


def track():
    for k, v in o.items():
        if n[k] != v:
            o[k] = n[k]
            # items.get(k).update(v)
            print(k + ":" + str(n[k]))


def do_everything(message):
    print("Processing:", message)
    read_data(message)
    calc()
    track()


def handle_led_command(led_no):
    param = request.args.get('val', type=int)
    param = int(round(param * 2.55, 0))
    print('LED1 rec. param', param)
    ser.on_send(command_string.format(led_no, param))
    return 'ok' + str(param)


@app.route('/')
def use_serial():
    do_everything('123:123:123:132:132:123:123:123:123:')
    return 'use flask serial!'


@app.route('/led1')
def led1_route():
    return handle_led_command(1)


@app.route('/led2')
def led2_route():
    return handle_led_command(2)


@ser.on_message()
def handle_message(msg):
    serial_buffer = msg.decode("utf-8")
    if serial_buffer.count(':') >= 9:
        do_everything(serial_buffer)



@ser.on_log()
def handle_logging(level, info):
    print(level, info)
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0')
