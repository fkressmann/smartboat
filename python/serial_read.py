from openhab import OpenHAB
import serial
from copy import deepcopy

base_url = 'http://localhost:8080/rest'
openhab = OpenHAB(base_url)
items = openhab.fetch_all_items()

ser = serial.Serial(

    port='/dev/ttyAMA0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

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


def read_data():
    x = ser.readline().decode('utf-8')
    print(x)
    # A0, A1, A2, A3, A4, A5, A6, A7, D2
    data = iter((float(e) for e in x.split(":")))
    n['U12v'] = internal_voltage(17.05, next(data))
    n['U5v'] = internal_voltage(6.25, next(data))
    next(data)
    n['Iverb'] = acs711(next(data))
    n['Ibat'] = acs711(next(data))
    n['Iinverter'] = acs711(next(data))
    n['Awasser1'] = next(data)
    n['Awasser2'] = next(data)
    n['Atank'] = tank(next(data))


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
    for k, v in o:
        if n[k] != v:
            v = n[k]
            # items.get(k).update(v)
            print(k + ":" + v)


if __name__ == "__main__":
    while True:
        read_data()
        calc()
        track()
