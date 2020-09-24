import time

from python.__main__ import ser


def print_time():
    return time.strftime('%d.%m. %T', time.localtime(time.time()))


def serial_send(address, command):
    ser.on_send(f"+{address}:{command}-")